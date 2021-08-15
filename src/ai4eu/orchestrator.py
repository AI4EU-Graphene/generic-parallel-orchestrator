# from __future__ import annotations  # for recursive pydantic types, only > 3.7
import json
import logging
import os
import subprocess
import sys
import tempfile
import collections

from google.protobuf.descriptor_pb2 import FileDescriptorSet, FileDescriptorProto
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel

from . import othread


class NodeInfo(BaseModel):
    container_name: str
    service_name: Optional[str]  # None for the orchestrator node
    host: str
    port: int


class MessageInfo(BaseModel):
    name: str
    stream: bool


linkinfo_next_idx = 0
class LinkInfo(BaseModel):
    input: 'RPCInfo'
    output: 'RPCInfo'
    message_name: str
    idx: int

    def __init__(self, **kwargs):
        global linkinfo_next_idx
        linkinfo_next_idx += 1
        super().__init__(idx=linkinfo_next_idx, **kwargs)

    def identifier(self) -> str:
        return '%s=%s=>%s_%d' % (
            self.input.node.container_name,
            self.message_name,
            self.output.node.container_name,
            self.idx
        )


class RPCInfo(BaseModel):
    node: NodeInfo
    operation: str
    input: MessageInfo
    output: MessageInfo
    incoming: List[LinkInfo]
    outgoing: List[LinkInfo]

    def identifier(self) -> str:
        return '%s_%s' % (
            self.node.container_name,
            self.operation
        )


# for the 'RPCInfo'
LinkInfo.update_forward_refs()


def readfile(path) -> str:
    with open(path, 'rt') as f:
        return f.read()


class ProtobufMerger:
    def __init__(self, protoc='protoc'):
        self.protoc = protoc

    def merge(self, protofiles: Dict[str, str], output_filename) -> FileDescriptorSet:
        '''
        parse protofiles with protoc into descriptor
        combine descriptors
        raise error if duplicate message names have different content
        return file descriptor set that can be used as input to protoc to generate Python code
        '''
        messages = {}
        message_in_files = collections.defaultdict(list)
        
        services = {}
        service_in_files = collections.defaultdict(list)

        with tempfile.TemporaryDirectory() as tdir:
            for fname, fcontent in protofiles.items():
                disk_fname = os.path.join(tdir, fname + '.proto')
                with open(disk_fname, 'w+') as f:
                    f.write(fcontent)

                out = subprocess.check_output(
                    '%s --descriptor_set_out=/dev/stdout --proto_path=%s %s' % (
                        self.protoc,
                        tdir,
                        disk_fname,
                    ),
                    stderr=sys.stderr, shell=True)
                fds = FileDescriptorSet.FromString(out)
                # logging.debug("from fname %s parsed fds %s", fname, fds)

                for f in fds.file:
                    if f.package is not None and f.package != '':
                        raise ValueError("cannot process package '%s' in file '%s'" % (f.package, fname))
                    if f.syntax != 'proto3':
                        raise ValueError("cannot process syntax '%s' in file '%s'" % (f.syntax, fname))

                    # collect messages
                    for msg in f.message_type:
                        # copy message if unknown, compare if known
                        if msg.name in messages:
                            if msg != messages[msg.name]:
                                raise ValueError("cannot merge protobuf files: message '%s' present in files %s and in file %s with different content" % (
                                    msg.name, message_in_files[msg.name], fname))
                            message_in_files[msg.name].append(fname)
                        else:
                            messages[msg.name] = msg
                            message_in_files[msg.name].append(fname)

                    if len(f.enum_type) > 0:
                        raise ValueError("cannot process protobuf input with enums '%s'" % str([ed.name for ed in f.enum_type]))
                    if len(f.extension) > 0:
                        raise ValueError("cannot process protobuf input with extensions '%s'" % str([e.name for e in f.extension]))

                    # collect services
                    for srv in f.service:
                        # copy srvice if unknown, compare if known
                        if srv.name in services:
                            if srv != services[srv.name]:
                                raise ValueError("cannot merge protobuf files: service '%s' present in files %s and in file %s with different content" % (
                                    srv.name, service_in_files[srv.name], fname))
                            service_in_files[srv.name].append(fname)
                        else:
                            services[srv.name] = srv
                            service_in_files[srv.name].append(fname)

        fdp = FileDescriptorProto(
            name=output_filename,
            message_type=messages.values(),
            service=services.values(),
        )
        ofds = FileDescriptorSet(file=[fdp])
        return ofds

class Core:
    nodes: Dict[str, NodeInfo] = {}
    rpcs: List[RPCInfo] = []
    links: List[LinkInfo] = []

    def parse_service_name_from_protofile(self, filecontent: str) -> str:
        # parse single service or first service (for merged services)
        # return service name
        servicelines = [
            line.strip()
            for line in filecontent.split('\n')
            if line.startswith('service ')
        ]
        logging.debug("got servicelines %s", servicelines)
        servicename = servicelines[0].split('{', 1)[0].strip().split(' ', 1)[1].strip()
        logging.debug("parsed servicename '%s'", servicename)
        return servicename

    def merge_and_compile_protobuf_files(self, protofiles: Dict[str, str], output_filename='all_in_one.proto') -> None:
        merger = ProtobufMerger()
        merged_fds = merger.merge(protofiles, output_filename)

        subprocess.run(
            'python -m grpc_tools.protoc --descriptor_set_in=/dev/stdin --python_out=./ --grpc_python_out=./ %s' % output_filename,
            stderr=sys.stderr, input=merged_fds.SerializeToString(), shell=True, check=True)

    def merge_protobuf_collect_node_infos(self, bpjson: dict, dijson: dict, protofiles: Dict[str, str]) -> Dict[str, NodeInfo]:
        '''
        extract node infos from dockerinfo json
        verify that all nodes in blueprint are in dockerinfo
        '''

        self.merge_and_compile_protobuf_files(protofiles)

        # extract dockerinfo
        for di in dijson['docker_info_list']:
            protofilename = di['container_name'] + '.proto'
            protofilecontent = protofiles.get(protofilename, None)
            if protofilecontent:
                service_name = self.parse_service_name_from_protofile(protofilecontent)
            else:
                service_name = None
            ni = NodeInfo(
                container_name=di['container_name'],
                service_name=service_name,
                host=di['ip_address'],
                port=di['port'])
            if ni.container_name in self.nodes:
                raise ValueError("dockerinfo json contains duplicate container name %s" % ni.container_name)
            self.nodes[ni.container_name] = ni

        # verify blueprint
        for n in bpjson['nodes']:
            if n['container_name'] not in self.nodes:
                raise ValueError("blueprint json contains container named %s that is not present in dockerinfo json" % n['container_name'])

        return self.nodes

    def collect_rpc_and_link_infos(self, bpjson: dict) -> Tuple[List[RPCInfo], List[LinkInfo]]:
        '''
        extract rpc from blueprint
        interlink rpcs (incoming/outgoing)
        '''

        link_partial = []
        for node in bpjson['nodes']:

            for sig_conn in node['operation_signature_list']:

                # extract one RPC with its outgoing links
                sig = sig_conn['operation_signature']
                rpc = RPCInfo(
                    node=self.nodes[node['container_name']],
                    operation=sig['operation_name'],
                    input=MessageInfo(
                        name=sig['input_message_name'],
                        stream=sig['input_message_stream']),
                    output=MessageInfo(
                        name=sig['output_message_name'],
                        stream=sig['output_message_stream']),
                    incoming=[],
                    outgoing=[])

                # outgoing links (partial info)
                for con in sig_conn['connected_to']:
                    link_partial.append({
                        "input": rpc,
                        "message_name": sig['output_message_name'],
                        "output_node": self.nodes[con['container_name']],
                        "output_operation": con['operation_signature']['operation_name']
                    })

                self.rpcs.append(rpc)

        # find details about incoming RPCs and create LinkInfos and store into incoming/outgoing
        for rpc in self.rpcs:
            incoming_links = [
                lp
                for lp in link_partial
                if lp['output_node'] == rpc.node and lp['output_operation'] == rpc.operation]

            expected_incoming_links = 1
            if rpc.input.name == 'Empty':
                expected_incoming_links = 0
            if len(incoming_links) != expected_incoming_links:
                raise RuntimeError((
                    "unexpected situation: encountered %d incoming links for rpc %s "
                    "with input type %s while trying to interlink rpcs (expect %d): %s") % (
                        len(incoming_links), repr(rpc),
                        rpc.input.name, expected_incoming_links, repr(incoming_links)))

            if expected_incoming_links > 0:
                incoming = incoming_links[0]

                link = LinkInfo(
                    input=incoming['input'],
                    output=rpc,
                    message_name=incoming['message_name'])
                self.links.append(link)

                # register link in RPCs
                link.input.outgoing.append(link)
                link.output.incoming.append(link)

        return self.rpcs, self.links


def test_orchestrator(blueprint: str, dockerinfo: str, protofiles: Dict[str, str]):
    '''
    directly run the orchestrator with given files
    '''
    bpjson = json.loads(blueprint)
    dijson = json.loads(dockerinfo)
    oc = Core()
    nodes = oc.merge_protobuf_collect_node_infos(bpjson, dijson, protofiles)
    rpcs, links = oc.collect_rpc_and_link_infos(bpjson)

    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logging.debug("nodes\n\t%s", '\n\t'.join([str(n) for n in nodes.items()]))
        logging.debug("rpcs\n\t%s", '\n\t'.join([str(r) for r in rpcs]))
        logging.debug("links\n\t%s", '\n\t'.join([str(l) for l in links]))

    import all_in_one_pb2
    import all_in_one_pb2_grpc
    om = othread.OrchestrationManager(all_in_one_pb2, all_in_one_pb2_grpc)

    # create a queue for each link
    queues = {}
    for link in links:
        # identifier
        linkid = link.identifier()
        logging.debug("creating queue for link %s", linkid)
        assert linkid not in queues, 'linkid must be unique in the solution'

        # create
        queues[linkid] = om.create_queue(name=linkid, message=link.message_name)

    # create one thread for each rpc
    threads = {}
    for rpc in rpcs:
        # identifier
        rpcid = rpc.identifier()
        logging.debug("creating thread for rpc %s", rpcid)
        assert rpcid not in threads, 'rpcid must be unique in the solution'

        # create
        threads[rpcid] = om.create_thread(
            stream_in=rpc.input.stream,
            stream_out=rpc.output.stream,
            empty_in=rpc.input.name == 'Empty',
            empty_out=rpc.output.name == 'Empty',
            host=rpc.node.host, port=rpc.node.port,
            service=rpc.node.service_name,
            rpc=rpc.operation,
        )

    # register each queue in an output and an input thread
    for link in links:
        # get queue and threads
        queue = queues[link.identifier()]
        input_from_rpcid = link.input.identifier()
        output_to_rpcid = link.output.identifier()
        input_thread = threads[input_from_rpcid]
        output_thread = threads[output_to_rpcid]

        # the output from some thread is the input for the queue
        input_thread.attach_output_queue(queue)
        # the output of the queue is the input for another thread
        output_thread.attach_input_queue(queue)

    om.orchestrate_forever()


def main():
    '''
    this is just for testing
    '''
    logging.basicConfig(level=logging.DEBUG)
    BASE = os.path.abspath(os.path.dirname(__file__))
    test_orchestrator(
        readfile(os.path.join(BASE, '..', '..', 'sample', 'blueprint.json')),
        readfile(os.path.join(BASE, '..', '..', 'sample', 'dockerinfo.json')),
        {
            f + '.proto': readfile(os.path.join(BASE, '..', '..', 'sample', 'protofiles', f + '.proto'))
            for f in ['sudoku-aspsolver1', 'sudoku-design-evaluator-stream1', 'sudoku-gui-stream1']
        }
    )


if __name__ == '__main__':
    # test this file
    main()
