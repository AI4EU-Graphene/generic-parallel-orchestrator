import concurrent.futures
import re
import json
import logging
import os
import queue
import time
import traceback
from typing import Generator
import grpc

import orchestrator_pb2
import orchestrator_pb2_grpc

from ai4eu.orchestrator import (
    Core as OrchestratorCore,
)

import ai4eu.othread as othread
from ai4eu.othread import (
    OrchestrationObserver,
    Event,
)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)


class QueueOrchestrationObserver(OrchestrationObserver):
    def __init__(self, queue: queue.Queue):
        self.queue = queue

    def event(self, evt: Event):
        self.queue.put(evt)


class OrchestratorServicerImpl(orchestrator_pb2_grpc.OrchestratorServicer):
    def __init__(self):
        super().__init__()

        self.event_queue = queue.Queue()
        self.observer = QueueOrchestrationObserver(self.event_queue)

        self.oc = None
        self.om = None
        self.threads = {}
        self.queues = {}
        self.status = orchestrator_pb2.OrchestrationStatus(message="not initialized")

    def _kill_threads_remove_queues(self):
        if self.om is not None:
            self.observer.event(Event(name='terminate_orchestration', component='orchestrator', detail={}))
            logging.error("terminate orch")
            self.om.terminate_orchestration()

        if len(self.threads) > 0:
            self.observer.event(Event(name='delete_threads', component='orchestrator', detail={}))
            for tid, t in list(self.threads.items()):
                t.input_queue = None
                t.output_queue = None
                del(self.threads[tid])
        assert len(self.threads) == 0

        if len(self.queues) > 0:
            self.observer.event(Event(name='delete_queues', component='orchestrator', detail={}))
            for qid, q in list(self.queues.items()):
                del(self.queues[qid])
        assert len(self.queues) == 0

        self.oc = None
        self.om = None

    def get_status_string(self):
        return f'message: {self.status.message} - active_threads: {self.status.active_threads} - success: {self.status.success} - code: {self.status.code}'

    def initialize(self, request: orchestrator_pb2.OrchestrationConfiguration, context) -> orchestrator_pb2.OrchestrationStatus:
        try:
            logging.info("initialize %s", request)
            # do a clean start
            self.status = orchestrator_pb2.OrchestrationStatus(message="initializing...")
            self._kill_threads_remove_queues()

            # interpret input jsons
            bpjson = json.loads(request.blueprint)
            dijson = json.loads(request.dockerinfo)

            # create new core
            self.observer.event(Event(name='create_core', component='orchestrator', detail={}))
            self.oc = OrchestratorCore()
            nodes = self.oc.merge_protobuf_collect_node_infos(bpjson, dijson, request.protofiles)
            rpcs, links = self.oc.collect_rpc_and_link_infos(bpjson)

            # create manager
            self.observer.event(Event(name='create_manager', component='orchestrator', detail={}))
            # can be imported only here because is created by merge_protobuf_collect_node_infos above
            import all_in_one_pb2
            import all_in_one_pb2_grpc
            self.om = othread.OrchestrationManager(all_in_one_pb2, all_in_one_pb2_grpc, observer=self.observer)

            # create one thread for each rpc with an input queue
            self.observer.event(Event(name='create_threads', component='orchestrator', detail={}))
            self.threads = {}
            for rpc in rpcs:
                # identifier
                rpcid = rpc.identifier()
                logging.debug("creating thread for rpc %s", rpcid)
                assert rpcid not in self.threads, 'rpcid must be unique in the solution'

                # create
                t = self.om.create_thread(
                    component=rpc.node.container_name,
                    stream_in=rpc.input.stream,
                    stream_out=rpc.output.stream,
                    empty_in=rpc.input.name == 'Empty',
                    empty_out=rpc.output.name == 'Empty',
                    host=rpc.node.host, port=rpc.node.port,
                    service=rpc.node.service_name,
                    rpc=rpc.operation,
                )


                if rpc.input.name != 'Empty':
                    # create input queue and attach
                    q = self.om.create_queue(
                        name=rpcid,
                        message=rpc.input.name,
                    )
                    t.attach_input_queue(q)

                # register thread
                self.threads[rpcid] = t

            # for each link, add input queue of receiver to list of output queues of sender
            self.observer.event(Event(name='register_queues', component='orchestrator', detail={}))
            for link in links:
                # input/output is seen differently from link and thread perspective!
                # the input of the link is the output of a thread
                # the output of the link is the input of a thread
                # here we use the link perspective

                # threads
                input_from_rpcid = link.input.identifier()
                output_to_rpcid = link.output.identifier()

                input_thread = self.threads[input_from_rpcid]
                output_thread = self.threads[output_to_rpcid]

                # each thread at the output of a link has one input queue
                queue = output_thread.input_queue

                # we connect the output of a thread at the input of the queue to the queue
                input_thread.attach_output_queue(queue)

            self.observer.event(Event(name='initialized', component='orchestrator', detail={}))

            self.status.success = False
            self.status.code = 0
            self.status.message = "initialized"
            self.active_threads = len(self.threads)


        except Exception as e:
            logging.info("OSI initialize exception: %s", traceback.format_exc())
            self.observer.event(Event(name='exception', component='orchestrator', detail={'method': 'initialize', 'traceback': traceback.format_exc()}))
            self.status.success = False
            self.status.code = -1
            self.status.message = "OSI initialize exception: "+traceback.format_exc()
            self.active_threads = len(self.threads)

        logging.info("OSI initialize returning %s", self.get_status_string())
        return self.status

    def observe(self, request: orchestrator_pb2.OrchestrationObservationConfiguration, context) -> Generator[orchestrator_pb2.OrchestrationEvent, None, None]:
        try:
            logging.info("OSI observe %s", request)

            namefilter = re.compile(request.name_regex)
            componentfilter = re.compile(request.component_regex)

            # exit if the connection dies
            while context.is_active():

                # try to get orchestrator event from queue
                try:
                    oevt = self.event_queue.get(block=True, timeout=1.0)

                    # create yield event
                    logging.debug("OSI event %s", oevt)
                    if namefilter.match(oevt.name) and componentfilter.match(oevt.component):
                        yevt = orchestrator_pb2.OrchestrationEvent(
                            run=oevt.run,
                            name=oevt.name,
                            component=oevt.component,
                            detail=oevt.detail,
                        )
                        logging.debug("OSI observe yielding %s", yevt)
                        yield yevt

                except queue.Empty:
                    pass

            logging.info("OSI observe exiting (context inactive)")
        except Exception as e:
            logging.info("OSI observe exception: %s", traceback.format_exc())

    def run(self, request: orchestrator_pb2.RunLabel, context) -> orchestrator_pb2.OrchestrationStatus:
        try:
            logging.info("OSI run %s", request)

            self.om.start_orchestration()

            self.status.success = False
            self.status.code = 0
            self.status.message = "running"
            self.active_threads = len(self.threads)

        except Exception as e:
            logging.info("OSI run exception: %s", traceback.format_exc())
            self.status.success = False
            self.status.code = -1
            self.status.message = "OSI run exception: "+traceback.format_exc()
            self.active_threads = len(self.threads)

        logging.info("OSI run returning %s", self.get_status_string())
        return self.status

    def get_status(self, request: orchestrator_pb2.RunLabel, context) -> orchestrator_pb2.OrchestrationStatus:
        self.status.active_threads = len(self.threads)
        logging.info("OSI get_status returning %s", self.get_status_string())
        return self.status


configfile = os.environ['CONFIG'] if 'CONFIG' in os.environ else "config.json"
try:
    logging.info("loading config from %s", configfile)
    config = json.load(open(configfile, 'rt'))
except Exception as e:
    logging.warning("using empty config (=defaults) because %s", e)
    config = {}

grpcserver = grpc.server(
    concurrent.futures.ThreadPoolExecutor(max_workers=10),
    options=(
        ('grpc.keepalive_time_ms', 1000), # send each second
        ('grpc.keepalive_timeout_ms', 3000), # 3 second = timeout
        ('grpc.keepalive_permit_without_calls', True), # allow ping without RPC calls
        ('grpc.http2.max_pings_without_data', 0), # allow unlimited pings without data
        ('grpc.http2.min_time_between_pings_ms', 1000), # allow pings every second
        ('grpc.http2.min_ping_interval_without_data_ms', 1000), # allow pings without data every second
    )
)
orchestrator_pb2_grpc.add_OrchestratorServicer_to_server(OrchestratorServicerImpl(), grpcserver)
grpcport = config.get('grpcport', 8061)
# listen on all interfaces (otherwise docker cannot export)
grpcserver.add_insecure_port('0.0.0.0:'+str(grpcport))
logging.info("starting Orchestrator gRPC server at port %d", grpcport)
grpcserver.start()

while True:
    time.sleep(1)
