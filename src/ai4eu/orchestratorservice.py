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


logger = logging.getLogger(__name__)
#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.DEBUG)


class OrchestratorServicerImpl(orchestrator_pb2_grpc.OrchestratorServicer):
    def __init__(self):
        pass

    def initialize(self, request: orchestrator_pb2.OrchestrationConfiguration, context) -> orchestrator_pb2.OrchestrationStatus:
        try:
            logging.info("OSI initialize %s", request)

            # TODO

            ret = orchestrator_pb2.OrchestrationStatus(
                # TODO
            )
            logging.info("OSI initialize returning %s", ret)
            return ret
        except Exception as e:
            logging.info("OSI initialize exception: %s", traceback.format_exc())

    def observe(self, request: orchestrator_pb2.OrchestrationObservationConfiguration, context) -> Generator[orchestrator_pb2.OrchestrationEvent, None, None]:
        try:
            logging.info("OSI observe %s", request)

            # exit if the connection dies
            while context.is_active():
                # TODO
                time.sleep(5)

                evt = orchestrator_pb2.OrchestrationEvent(
                    # TODO
                )
                logging.debug("OSI observe yielding %s", evt)
                yield evt

            logging.info("OSI observe exiting (context inactive)")
        except Exception as e:
            logging.info("OSI observe exception: %s", traceback.format_exc())

    def run(self, request: orchestrator_pb2.RunLabel, context) -> orchestrator_pb2.OrchestrationStatus:
        try:
            logging.info("OSI run %s", request)

            # TODO

            ret = orchestrator_pb2.OrchestrationStatus(
                # TODO
            )
            logging.info("OSI run returning %s", ret)
            return ret
        except Exception as e:
            logging.info("OSI run exception: %s", traceback.format_exc())


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
