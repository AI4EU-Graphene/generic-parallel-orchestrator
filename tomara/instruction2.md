```bash
 python .\kubernetes-client-script.py --namespace tomara
namespace = tomara
image_pull_policy = Always
base_path = C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7  
error reading config file: [Errno 2] No such file or directory: '/home/ai4eu/playground-app/config.json'
Given namespace is active 
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_deployment.yaml
set_image_pull_policy setting imagePullPolicy to Always
  apply got ['deployment.apps/node11', 'created\n']
file_name of service yaml = C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service.yaml
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service_webui.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service_webui.yaml to 8061
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service_webui.yaml to 30281
  apply got ['service/node11webui', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service.yaml to 8062
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node11_service.yaml to 31818
  apply got ['service/node11', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_deployment.yaml
set_image_pull_policy setting imagePullPolicy to Always
  apply got ['deployment.apps/node21', 'created\n']
file_name of service yaml = C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service.yaml
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service_webui.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service_webui.yaml to 8063
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service_webui.yaml to 31843
  apply got ['service/node21webui', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service.yaml to 8064
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node21_service.yaml to 31124
  apply got ['service/node21', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_deployment.yaml
set_image_pull_policy setting imagePullPolicy to Always
  apply got ['deployment.apps/node31', 'created\n']
file_name of service yaml = C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service.yaml
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service_webui.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service_webui.yaml to 8065
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service_webui.yaml to 31847
  apply got ['service/node31webui', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service.yaml to 8066
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\node31_service.yaml to 31446
  apply got ['service/node31', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_deployment.yaml
set_image_pull_policy setting imagePullPolicy to Always
  apply got ['deployment.apps/orchestrator', 'created\n']
file_name of service yaml = C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service.yaml
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service_webui.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service_webui.yaml to 8067
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service_webui.yaml to 32238
  apply got ['service/orchestratorwebui', 'configured\n']
apply_yaml: C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service.yaml
set_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service.yaml to 8068
set_node_port in C:\Users\robin\OneDrive\Desktop\MU\SEM_2\ANALYTICS_LIVE\solution-7\deployments\orchestrator_service.yaml to 32116
  apply got ['service/orchestrator', 'configured\n']
{'node11webui': 30281, 'node11': 31818, 'node21webui': 31843, 'node21': 31124, 'node31webui': 31847, 'node31': 31446, 'orchestratorwebui': 32238, 'orchestrator': 32116}

Start updating the docker info Json :
update_node_port: [{'container_name': 'node11', 'ip_address': 'node11', 'port': 31818}, {'container_name': 'node21', 'ip_address': 'node21', 'port': 31124}, {'container_name': 'node31', 'ip_address': 'node31', 'port': 31446}, {'container_name': 'orchestrator', 'ip_address': 'orchestrator', 'port': 32116}]

 Docker info file is successfully updated
Node IP-address : kubernetes.docker.internal
Orchestrator Port is : 32116
Please run python orchestrator_client/orchestrator_client.py --endpoint=kubernetes.docker.internal:32116 --basepath=./




PS C:\Users\robin\OneDrive\Desktop\generic-parallel-orchestrator> kubectl get pods -n tomara
>> kubectl logs deployment/orchestrator -n tomara
>>
NAME                            READY   STATUS             RESTARTS        AGE
node11-79c795998-gptdw          0/1     CrashLoopBackOff   8 (3m45s ago)   19m  
node21-57c8c4b69b-bxc9w         0/1     CrashLoopBackOff   8 (3m27s ago)   19m  
node31-645bd4f595-xs4xg         0/1     CrashLoopBackOff   8 (3m31s ago)   19m  
orchestrator-74dcf75446-m56db   1/1     Running            0               7s   
INFO:root:loading config from config.json
WARNING:root:using empty config (=defaults) because [Errno 2] No such file or directory: 'config.json'
INFO:root:starting Orchestrator gRPC server at port 8061
INFO:root:Registered gRPC method: /Orchestrator/initialize
INFO:root:Registered gRPC method: /Orchestrator/observe
INFO:root:Registered gRPC method: /Orchestrator/run
INFO:root:Registered gRPC method: /Orchestrator/get_status



npython orchestrator_client/orchestrator_client.py --endpoint=kubernetes.docker.internal:32116 --basepath=./ --messages
INFO:root:load_solution_configuration returning <__main__.SolutionConfiguration object at 0x00000164375ADE80>
INFO:root:connecting to orchestrator
INFO:root:creating observer
INFO:root:calling initialize
orchestrator produced event 'create_core'
orchestrator produced event 'create_manager'
orchestrator produced event 'create_threads'
INFO:root:calling run
orchestrator produced event 'register_queues'
orchestrator produced event 'initialized'

OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'thread.start'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'thread.start'
OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'thread.start'

OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'RPC.call' with details message='' rpc='Execute'
OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'distributing output message' with details rpc='Execute'
OrchestrationQueue[node31_Execute] produced event 'queue.added' with details queue='node31_Execute'

OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'RPC.call' with details message='' rpc='Execute'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'distributing output message' with details rpc='Execute'
OrchestrationQueue[node21_Execute] produced event 'queue.added' with details queue='node21_Execute'

OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'RPC.call' with details message='' rpc='Execute'

OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'
OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'

OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'thread.terminate'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'thread.terminate'
OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'thread.terminate'






kubectl logs orchestrator-647d5cf9fd-wzgt9 -n tomara
INFO:root:loading config from config.json
WARNING:root:using empty config (=defaults) because [Errno 2] No such file or directory: 'config.json'
INFO:root:starting Orchestrator gRPC server at port 8061
INFO:root:Registered gRPC method: /Orchestrator/initialize
INFO:root:Registered gRPC method: /Orchestrator/observe
INFO:root:Registered gRPC method: /Orchestrator/run
INFO:root:Registered gRPC method: /Orchestrator/get_status
INFO:root:OSI observe name_regex: ".*"
component_regex: ".*"

INFO:root:initialize blueprint: "{\"nodes\":[{\"proto_uri\":\"org\/acumos\/3883ce0a-05bb-425c-ad49-8fc4e9cdc4b0\/node1\/1.0.1\/node1-1.0.1.proto\",\"image\":\"vaibhavtechie\/node1-image:latest\",\"node_type\":\"MLModel\",\"container_name\":\"node11\",\"operation_signature_list\":[{\"connected_to\":[{\"container_name\":\"node31\",\"operation_signature\":{\"operation_name\":\"Execute\"}}],\"operation_signature\":{\"operation_name\":\"Execute\",\"output_message_name\":\"Empty\",\"input_message_name\":\"Empty\",\"output_message_stream\":false,\"input_message_stream\":false}}]},{\"proto_uri\":\"org\/acumos\/27efda2a-8a2c-4860-8108-e4ff41897b70\/node2\/1.0.0\/node2-1.0.0.proto\",\"image\":\"vaibhavtechie\/node2-image:latest\",\"node_type\":\"MLModel\",\"container_name\":\"node21\",\"operation_signature_list\":[{\"connected_to\":[],\"operation_signature\":{\"operation_name\":\"Execute\",\"output_message_name\":\"Empty\",\"input_message_name\":\"Empty\",\"output_message_stream\":false,\"input_message_stream\":false}}]},{\"proto_uri\":\"org\/acumos\/0c2941ee-bc0f-44db-9bfd-249c144438d5\/node3\/1.0.0\/node3-1.0.0.proto\",\"image\":\"vaibhavtechie\/node3-image:latest\",\"node_type\":\"MLModel\",\"container_name\":\"node31\",\"operation_signature_list\":[{\"connected_to\":[{\"container_name\":\"node21\",\"operation_signature\":{\"operation_name\":\"Execute\"}}],\"operation_signature\":{\"operation_name\":\"Execute\",\"output_message_name\":\"Empty\",\"input_message_name\":\"Empty\",\"output_message_stream\":false,\"input_message_stream\":false}}]}],\"name\":\"Node132\",\"pipeline_id\":\"1047a39c-2ebe-11ea-bbf7-52ce898b1042:bcc44ad3-ed4c-4711-951f-fb3d4ed4d48c:2496fb3e-ffad-4746-8343-67e31c90f074\",\"creation_date\":\"2025-04-11 14:19:36.276085\",\"type\":\"pipeline-topology\/v2\",\"version\":\"1.0.0\"}"
dockerinfo: "{\"docker_info_list\": [{\"container_name\": \"node11\", \"ip_address\": \"node11\", \"port\": 31818}, {\"container_name\": \"node21\", \"ip_address\": \"node21\", \"port\": 31124}, {\"container_name\": \"node31\", \"ip_address\": \"node31\", \"port\": 31446}, {\"container_name\": \"orchestrator\", \"ip_address\": \"orchestrator\", \"port\": 32116}]}"
protofiles {
  key: "node11.proto"
  value: "syntax = \"proto3\";\nservice Component {\n  rpc Execute(Empty) returns (Empty);\n}\nmessage Empty {}"
}
protofiles {
  key: "node21.proto"
  value: "syntax = \"proto3\";\nservice Component {\n  rpc Execute(Empty) returns (Empty);\n}\nmessage Empty {}"
}
protofiles {
  key: "node31.proto"
  value: "syntax = \"proto3\";\nservice Component {\n  rpc Execute(Empty) returns (Empty);\n}\nmessage Empty {}"
}

/root/.local/share/virtualenvs/app-xyz/lib/python3.7/site-packages/grpc_tools/protoc.py:17: DeprecationWarning: pkg_resources is deprecated ...
  import pkg_resources

INFO:root:OSI initialize returning message: initialized - active_threads: 3 - success: True - code: 0
INFO:root:OSI run
INFO:root:OSI run returning message: running - active_threads: 3 - success: True - code: 0

OrchestrationQueue[node31_Execute] produced event 'queue.added' with details queue='node31_Execute'
OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'RPC.call' with details rpc='Execute'
OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'distributing output message' with details rpc='Execute'
OrchestrationQueue[node31_Execute] produced event 'queue.added' with details queue='node31_Execute'
OrchestrationThreadBase[component=node11,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'

OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'RPC.call' with details rpc='Execute'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'distributing output message' with details rpc='Execute'
OrchestrationQueue[node21_Execute] produced event 'queue.added' with details queue='node21_Execute'
OrchestrationThreadBase[component=node31,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'

OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'RPC.call' with details rpc='Execute'
OrchestrationThreadBase[component=node21,svc=Component,rpc=Execute] produced event 'RPC.finished' with details rpc='Execute'

INFO:root:All orchestration threads completed successfully.

```