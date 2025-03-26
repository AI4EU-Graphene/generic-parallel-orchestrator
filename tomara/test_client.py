import grpc
import sys
import os

# Ensure parent path is included
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Corrected imports and naming
import tomara.orchestrator_pb2 as pb2
import tomara.orchestrator_pb2_grpc as pb2_grpc

def run():
    # Connect to gRPC server
    channel = grpc.insecure_channel('localhost:8080')
    stub = pb2_grpc.OrchestratorStub(channel)  # ✅ matches service name in proto

    # Build request
    request = pb2.RunLabel(label="test-run")
    
    # Call gRPC method
    response = stub.get_status(request)

    # Print response
    print("Response:")
    print("  Status:", response.success)
    print("  Message:", response.message)
    print("  Active Threads:", response.active_threads)

if __name__ == '__main__':
    run()
