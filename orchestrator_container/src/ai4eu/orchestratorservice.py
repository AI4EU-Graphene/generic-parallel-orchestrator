import concurrent.futures
import grpc
import json
import logging
import os
import queue
import time
import traceback
from typing import Generator

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

    def _kill_threads_remove_queues(self):
        if self.om is not None:
            self.observer.event(Event(name='terminate_orchestration', component='orchestrator', detail={}))
            logging.error("terminate orch")
            self.om.terminate_orchestration()

        logging.error("del thread")
        if len(self.threads) > 0:
            self.observer.event(Event(name='delete_threads', component='orchestrator', detail={}))
            for tid, t in list(self.threads.items()):
                t.input_queue = None
                t.output_queue = None
                del(self.threads[tid])
        assert len(self.threads) == 0

        logging.error("del queue")
        if len(self.queues) > 0:
            self.observer.event(Event(name='delete_queues', component='orchestrator', detail={}))
            for qid, q in list(self.queues.items()):
                del(self.queues[qid])
        assert len(self.queues) == 0

        self.oc = None
        self.om = None


    def initialize(self, request: orchestrator_pb2.OrchestrationConfiguration, context) -> orchestrator_pb2.OrchestrationStatus:
        try:
            logging.info("OSI initialize %s", request)

            # do a clean start
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

            # create a queue for each link
            self.observer.event(Event(name='create_queues', component='orchestrator', detail={}))
            self.queues = {}
            for link in links:
                # identifier
                linkid = link.identifier()
                logging.debug("creating queue for link %s", linkid)
                assert linkid not in self.queues, 'linkid must be unique in the solution'

                # create
                self.queues[linkid] = self.om.create_queue(name=linkid, message=link.message_name)

            # create one thread for each rpc
            self.observer.event(Event(name='create_threads', component='orchestrator', detail={}))
            self.threads = {}
            for rpc in rpcs:
                # identifier
                rpcid = rpc.identifier()
                logging.debug("creating thread for rpc %s", rpcid)
                assert rpcid not in self.threads, 'rpcid must be unique in the solution'

                # create
                self.threads[rpcid] = self.om.create_thread(
                    stream_in=rpc.input.stream,
                    stream_out=rpc.output.stream,
                    empty_in=rpc.input.name == 'Empty',
                    empty_out=rpc.output.name == 'Empty',
                    host=rpc.node.host, port=rpc.node.port,
                    service=rpc.node.service_name,
                    rpc=rpc.operation,
                )

            # register each queue in an output and an input thread
            self.observer.event(Event(name='register_queues', component='orchestrator', detail={}))
            for link in links:
                # get queue and threads
                queue = self.queues[link.identifier()]
                input_from_rpcid = link.input.identifier()
                output_to_rpcid = link.output.identifier()
                input_thread = self.threads[input_from_rpcid]
                output_thread = self.threads[output_to_rpcid]

                # the output from some thread is the input for the queue
                input_thread.attach_output_queue(queue)
                # the output of the queue is the input for another thread
                output_thread.attach_input_queue(queue)

            self.observer.event(Event(name='initialized', component='orchestrator', detail={}))

        except Exception as e:
            logging.info("OSI initialize exception: %s", traceback.format_exc())
            self.observer.event(Event(name='exception', component='orchestrator', detail={'method': 'initialize', 'traceback': traceback.format_exc()}))

        ret = orchestrator_pb2.OrchestrationStatus(
            # TODO
        )
        logging.info("OSI initialize returning %s", ret)
        return ret

    def observe(self, request: orchestrator_pb2.OrchestrationObservationConfiguration, context) -> Generator[orchestrator_pb2.OrchestrationEvent, None, None]:
        try:
            logging.info("OSI observe %s", request)

            # exit if the connection dies
            while context.is_active():

                # try to get orchestrator event from queue
                try:
                    oevt = self.event_queue.get(block=True, timeout=1.0)

                    # create yield event
                    logging.warning("event is %s", oevt)
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
        ret = None
        try:
            logging.info("OSI run %s", request)

            self.om.start_orchestration()

            ret = orchestrator_pb2.OrchestrationStatus(
                success=True,
                code=0,
                message='success',
            )

        except Exception as e:
            logging.info("OSI run exception: %s", traceback.format_exc())
            ret = orchestrator_pb2.OrchestrationStatus(
                success=False,
                code=-1,
                message=traceback.format_exc(),
            )

        logging.info("OSI run returning %s", ret)
        return ret


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
