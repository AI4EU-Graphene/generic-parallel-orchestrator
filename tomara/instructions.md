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
```

Tag and push:
```sh
docker tag parallel-orchestrator tomara/parallel-orchestrator:latest
docker push tomara/parallel-orchestrator:latest
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
```

Check if it’s working:
```sh
kubectl get pods
kubectl get services
```

or to check all of them in one go 
```sh
kubectl get po,deploy,svc
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
