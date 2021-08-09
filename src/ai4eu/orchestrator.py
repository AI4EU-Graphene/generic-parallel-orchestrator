# from __future__ import annotations  # for recursive pydantic types, only > 3.7
import logging
import os
import json
from typing import List, Dict, Tuple
from pydantic import BaseModel

from . import othread


class NodeInfo(BaseModel):
    container_name: str
    service_name: str
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
        return '%s_%d' % (
            self.node.container_name,
            self.operation
        )


# for the 'RPCInfo'
LinkInfo.update_forward_refs()


def readfile(path) -> str:
    with open(path, 'rt') as f:
        return f.read()


class Core:
    nodes: Dict[str, NodeInfo] = {}
    rpcs: List[RPCInfo] = []
    links: List[LinkInfo] = []

    def parse_service_name_from_protofile(self, protofilename: str) -> str:
        # find protofile in zip or unpacked
        # parse single service or first service (for merged services)
        # return service name

    def collect_node_infos(self, bpjson: dict, dijson: dict) -> Dict[str, NodeInfo]:
        '''
        extract node infos from dockerinfo json
        verify that all nodes in blueprint are in dockerinfo
        '''

        # extract dockerinfo
        for di in dijson['docker_info_list']:
            service_name = self.parse_service_name_from_protofile(di['container_name']+'.proto')
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


def test_orchestrator(blueprint: str, dockerinfo: str, protofiles: List[str]):
    bpjson = json.loads(blueprint)
    dijson = json.loads(dockerinfo)
    oc = Core()
    nodes = oc.collect_node_infos(bpjson, dijson)
    rpcs, links = oc.collect_rpc_and_link_infos(bpjson)

    logging.warning("nodes\n\t%s", '\n\t'.join([str(n) for n in nodes.items()]))
    logging.warning("rpcs\n\t%s", '\n\t'.join([str(r) for r in rpcs]))
    logging.warning("links\n\t%s", '\n\t'.join([str(l) for l in links]))

    om = othread.OrchestrationManager()

    # create a queue for each link
    queues = {}
    for link in links:
        linkid = link.identifier()
        logging.warning("creating queue for link %s", linkid)
        assert linkid not in queues, 'linkid must be unique in the solution'
        queues[linkid] = om.create_queue(name=linkid, message=link.message_name)

    # create one thread for each rpc
    threads = {}
    for rpc in rpcs:
        rpcid = rpc.identifier()
        logging.warning("creating thread for rpc %s", rpcid)
        assert rpcid not in rpcs, 'rpcid must be unique in the solution'
        rpcs[rpcid] = om.create_thread(
            stream_in=rpc.input.stream,
            stream_out=rpc.output.stream,
            host=rpc.node.host, port=rpc.node.port,
            service=rpc.
            rpc=rpc.operation,


    # next steps:
    # * create queues for links
    # * create threads for rpcs
    # * generate protobuf libraries from protofiles (do not merge)
    # * adapt othread to import the right library and resolve types/RPCs from there
    # * test orchestration with sudoku
    # * 


def main():
    BASE = os.path.abspath(os.path.dirname(__file__))
    test_orchestrator(
        readfile(os.path.join(BASE, '..', '..', 'sample', 'blueprint.json')),
        readfile(os.path.join(BASE, '..', '..', 'sample', 'dockerinfo.json')),
        [
            readfile(os.path.join(BASE, '..', '..', 'sample', 'protofiles', f + '.proto'))
            for f in ['asp', 'sudoku-design-evaluator', 'sudoku-gui']
       ]
    )


if __name__ == '__main__':
    main()
