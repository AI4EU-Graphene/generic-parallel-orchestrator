## FULL SETUP: Parallel Orchestrator Using Docker + Kubernetes + Pipenv (Windows)

### Prerequisites 

- Python (recommended: 3.8+)
- Docker Desktop (with Kubernetes enabled)
- Git
- Pipenv  
  Install with:
  ```sh
  pip install pipenv
  ```

## Step 1: Cloning the Repository

```sh
git clone https://github.com/ai4eu/generic-parallel-orchestrator.git
cd generic-parallel-orchestrator
```

## Step 2: Build the Docker Image Using Pipenv

Dockerfile at path : orchestrator_container\Dockerfile

## Step 3: Build & Push the Docker Image

```sh
docker build -t parallel-orchestrator .\orchestrator_container\

#### output ####
[+] Building 1.1s (15/15) FINISHED                                                                                                                             docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                                                           0.0s
 => => transferring dockerfile: 1.07kB                                                                                                                                         0.0s
 => [internal] load metadata for docker.io/library/debian:buster-slim                                                                                                          0.9s
 => [auth] library/debian:pull token for registry-1.docker.io                                                                                                                  0.0s
 => [internal] load .dockerignore                                                                                                                                              0.0s
 => => transferring context: 87B                                                                                                                                               0.0s
 => [1/9] FROM docker.io/library/debian:buster-slim@sha256:bb3dc79fddbca7e8903248ab916bb775c96ec61014b3d02b4f06043b604726dc                                                    0.0s
 => [internal] load build context                                                                                                                                              0.0s
 => => transferring context: 288B                                                                                                                                              0.0s
 => CACHED [2/9] WORKDIR /app                                                                                                                                                  0.0s
 => CACHED [3/9] COPY Pipfile ./                                                                                                                                               0.0s
 => CACHED [4/9] COPY Pipfile.lock ./                                                                                                                                          0.0s
 => CACHED [5/9] RUN set -ex     && apt-get update -y     && apt-get upgrade -y     && apt-get install -y --no-install-recommends         python3 python3-pip python3-dev bui  0.0s
 => CACHED [6/9] COPY src ./                                                                                                                                                   0.0s
 => CACHED [7/9] COPY orchestrator.proto ./                                                                                                                                    0.0s 
 => CACHED [8/9] RUN pipenv run python -m grpc_tools.protoc --python_out=/app/ --proto_path=/app/ --grpc_python_out=/app/ /app/orchestrator.proto                              0.0s 
 => CACHED [9/9] RUN find /app                                                                                                                                                 0.0s 
 => exporting to image                                                                                                                                                         0.0s 
 => => exporting layers                                                                                                                                                        0.0s 
 => => writing image sha256:6716ab3678239d01d0f8491a455ad0eb2b759f3fdfe59e3f7009bfc8a08a33cb                                                                                   0.0s 
 => => naming to docker.io/library/parallel-orchestrator                                                                                                                       0.0s 

View build details: docker-desktop://dashboard/build/desktop-linux/desktop-linux/q4v3noqh5zlkbxbvmpmisdrf0

 4 warnings found (use docker --debug to expand):
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 5)
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 6)
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 7)
 - LegacyKeyValueFormat: "ENV key=value" should be used instead of legacy "ENV key value" format (line 4)
```

Tag and push:
```sh
docker tag parallel-orchestrator parallel-orchestrator:latest
docker push parallel-orchestrator:latest

#### output ####
 docker tag parallel-orchestrator tomara/parallel-orchestrator:latest
PS C:\Users\robin\OneDrive\Desktop\generic-parallel-orchestrator> docker push tomara/parallel-orchestrator:latest
The push refers to repository [docker.io/tomara/parallel-orchestrator]
fee407303996: Preparing
fd61d9d29af2: Preparing
edf9e0e8b669: Preparing
ce3a3fee7435: Preparing
222979a8f4d8: Preparing
70adea1cae07: Waiting
ac804d1e7997: Waiting
195bd589011f: Waiting
8a84050e401d: Waiting
denied: requested access to the resource is denied
```

> Failed because we are not pushing the images to docker.io or any private repository. Just keeping it on local.

You can verify the docker images after the above step 

```bash 
PS C:\Users\robin\OneDrive\Desktop\generic-parallel-orchestrator> docker images | grep parallel-orchestrator

#### output ####
REPOSITORY                                TAG                                                                           IMAGE ID       CREATED         SIZE
parallel-orchestrator                     latest                                                                        6716ab367823   2 weeks ago     307MB
```

## Step 4: Create Kubernetes Deployment and Service

### `parallel-orchestrator-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: parallel-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: parallel-orchestrator
  template:
    metadata:
      labels:
        app: parallel-orchestrator
    spec:
      containers:
        - name: orchestrator
          image: parallel-orchestrator:latest
          imagePullPolicy: Never #As we are going to pull the image from local 
          ports:
            - containerPort: 50051
```


### `parallel-orchestrator-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: parallel-orchestrator-service
spec:
  selector:
    app: parallel-orchestrator
  ports:
    - protocol: TCP
      port: 80
      targetPort: 50051
  type: LoadBalancer
```


## Step 5: Deploy to Kubernetes

First run docker login command, following the kubectl apply to deploy the deployment and svc

```sh
kubectl apply -f tomara/parallel-orchestrator-deployment.yaml
kubectl apply -f tomara/parallel-orchestrator-service.yaml

#### output ####

deployment.apps/parallel-orchestrator created
service/parallel-orchestrator-service created
```

Check if it’s working:
```sh
kubectl get pods
kubectl get services
```

or to check all of them in one go 
```sh
kubectl get po,deploy,svc

#### output ####

NAME                                         READY   STATUS    RESTARTS   AGE
pod/parallel-orchestrator-5d85869b7c-fkdpp   1/1     Running   0          4s
pod/parallel-orchestrator-5d85869b7c-gtjhg   1/1     Running   0          4s
pod/parallel-orchestrator-5d85869b7c-p65bl   1/1     Running   0          4s

NAME                                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/kubernetes                      ClusterIP      10.96.0.1        <none>        443/TCP          3h50m
service/parallel-orchestrator-service   LoadBalancer   10.106.159.112   localhost     8080:32158/TCP   4s

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/parallel-orchestrator   3/3     3            3           4s

NAME                                               DESIRED   CURRENT   READY   AGE
replicaset.apps/parallel-orchestrator-5d85869b7c   3         3         3       4s
```

Note: Not using Any specific namespace as everything is running on local and we only want to test a specific fnunctionality


## Step 6: Test Your Parallel Orchestrator

### Step 1: Port Forward the Service
Expose your orchestrator service to your local machine:

```bash
kubectl port-forward svc/parallel-orchestrator-service 8080:80
```

> This forwards Kubernetes port `50051` (used in container) → to your local port `8080`

### Step 2: Create a Python gRPC Client

We’ll use Python to send a gRPC request.

#### create `test_client.py`  

### Step 3: Install Required Python Packages
Run this inside your project folder:

```bash
pip install grpcio grpcio-tools
```

### Step 4: Ensure gRPC Python Stubs Are Available
If `orchestrator_pb2.py` and `orchestrator_pb2_grpc.py` are not present, generate them from your `.proto` file:

```bash
python -m grpc_tools.protoc --proto_path=tomara --python_out=tomara --grpc_python_out=tomara orchestrator.proto
```

This will create the `*_pb2.py` files needed by the Python client.

### Step 5: Run the Test Client
Make sure your orchestrator is port-forwarded (step 1), then run:

```bash
python -m tomara.test_client
```

Expected output:
```
Response: task_id: "test-123"
output: "Squared value: 16"
status: "SUCCESS"
```

*(your output may vary based on your orchestrator logic)*

### Optional: Customize the Task
If your orchestrator expects specific parameters, adjust this block in `test_client.py`:
```python
parameters={"input": "4"}
```

You can test with other inputs or trigger multiple parallel tasks in a loop.


## Coming to dpeloyment of WP3.1 

### pull docker images from docker.io 

```bash 
docker pull aditya2277/energy-training:latest
docker pull aditya2277/energy-databroker:latest
docker pull aditya2277/energy-prediction:latest

#### output ####

PS C:\Users\robin\OneDrive\Desktop\EnergyConsumption-WP3.1\solution\deployments> docker pull aditya2277/energy-training:latest
>> docker pull aditya2277/energy-databroker:latest
>> docker pull aditya2277/energy-prediction:latest
>>
latest: Pulling from aditya2277/energy-training
6e909acdb790: Already exists
a6f2701f375f: Pull complete
7a729f9c5873: Pull complete
75c77ac11059: Pull complete
8d257e8260b0: Pull complete
af218872b250: Pull complete
91c911236d9e: Pull complete
807412e4040d: Pull complete
Digest: sha256:9edbd393022dc1d894424030441e4e94632bc6787935565a82bdbb0affd13800
Status: Downloaded newer image for aditya2277/energy-training:latest
docker.io/aditya2277/energy-training:latest
latest: Pulling from aditya2277/energy-databroker
6e909acdb790: Already exists
a6f2701f375f: Already exists                                                                                                                                                        
7a729f9c5873: Already exists                                                                                                                                                        
75c77ac11059: Already exists                                                                                                                                                        
bea27b076a85: Pull complete
37f351c5535a: Pull complete
7e355122723f: Pull complete
Digest: sha256:4b76ecb874432da90edda6c8ace4fd96e4a2830a206ea9bbdafed9c93327fabd
Status: Downloaded newer image for aditya2277/energy-databroker:latest
docker.io/aditya2277/energy-databroker:latest
latest: Pulling from aditya2277/energy-prediction
6e909acdb790: Already exists
a6f2701f375f: Already exists
7a729f9c5873: Already exists
75c77ac11059: Already exists
a6f2701f375f: Already exists
7a729f9c5873: Already exists
75c77ac11059: Already exists
193e210d8134: Pull complete
0d0ee0f270d2: Pull complete
dcd0d7232f0a: Pull complete
caa83a9dfc31: Pull complete
Digest: sha256:8c44ab70c94ebb713ac5b9a339a71fec2df66bf7f44fc3ca6df5d31910f51526
Status: Downloaded newer image for aditya2277/energy-prediction:latest
docker.io/aditya2277/energy-prediction:latest
```

### clone the WP3.1 repo to local that contains the zip

```bash 
git clone https://github.com/AI4EU-Graphene/EnergyConsumption-WP3.1.git
```

1. After cloning the same to the local next step will be to go to the cloned repo and unzip it inside it 
2. After unzip, next step will be to to go inside the unzipped folder that will be by name *solution*

### Deploy kubectl deployments 

1. After going to the folder, go to EnergyConsumption-WP3.1\solution\deployments
```bash
cd solution/deployments 

#### output ####

kubectl apply -f energy-databroker1_service.yaml
kubectl apply -f energy-databroker1_deployment.yaml

kubectl apply -f energy-training1_service.yaml
kubectl apply -f energy-training1_deployment.yaml

kubectl apply -f energy-prediction1_service.yaml
kubectl apply -f energy-prediction1_deployment.yaml
```

or 

```bash 
kubectl apply -f .

#### output ####

service/energy-databroker1 created
deployment.apps/energy-databroker1 created
service/energy-training1 created
deployment.apps/energy-training1 created
service/energy-prediction1 created
deployment.apps/energy-prediction1 created
```

3. Verify that the pods and services are in running state 

```bash
kubectl get pods,svc

#### output ####

PS C:\Users\robin\OneDrive\Desktop\EnergyConsumption-WP3.1\solution\deployments> kubectl get pods,svc
NAME                                         READY   STATUS    RESTARTS   AGE
pod/energy-databroker1-f7b675c94-w8hs2       1/1     Running   0          80s
pod/energy-prediction1-7ccbc5b4d6-dwdjh      1/1     Running   0          80s
pod/energy-training1-75dc8b855c-sjxqv        1/1     Running   0          80s
pod/parallel-orchestrator-5d85869b7c-fkdpp   1/1     Running   0          43m
pod/parallel-orchestrator-5d85869b7c-gtjhg   1/1     Running   0          43m
pod/parallel-orchestrator-5d85869b7c-p65bl   1/1     Running   0          43m

NAME                                    TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
service/energy-databroker1              NodePort       10.111.35.117    <none>        8556:31573/TCP   80s
service/energy-prediction1              NodePort       10.98.113.165    <none>        8556:32197/TCP   80s
service/energy-training1                NodePort       10.101.138.69    <none>        8556:31268/TCP   80s
service/kubernetes                      ClusterIP      10.96.0.1        <none>        443/TCP          4h34m
service/parallel-orchestrator-service   LoadBalancer   10.106.159.112   localhost     8080:32158/TCP   43m
```

