python -m grpc_tools.protoc --python_out=orchestrator_client/ --proto_path=protobuf --grpc_python_out=orchestrator_client/ protobuf/orchestrator.proto
python -m grpc_tools.protoc --python_out=orchestrator_container/src/ --proto_path=protobuf --grpc_python_out=orchestrator_container/src/ protobuf/orchestrator.proto
