import grpc
from concurrent import futures
import time

import orchestrator_pb2_grpc
from ai4eu.orchestratorservice import OrchestratorServicer

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    orchestrator_pb2_grpc.add_OrchestratorServicer_to_server(OrchestratorServicer(), server)
    server.add_insecure_port('[::]:8061')
    print("✅ Orchestrator gRPC Server is running on port 8061")
    server.start()
    server.wait_for_termination()

class Core:
    def __init__(self):
        print("⚙️ Dummy Core class initialized")

if __name__ == "__main__":
    serve()
