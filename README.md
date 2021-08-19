# generic-parallel-orchestrator

Orchestrator with support for streaming, RPC, and seamless conversion between the two, based on a queued multithreading architecture.

Enables streaming/event-based communication in addition to RPC calls.
This enables many applications, including bridges to/from ROS.

This also enables cyclic topologies like control loops or multiple calls of a subcomponent (one component requires `n` calls of another component to compute its result).

The orchestrator is meant to run as a docker container in kubernetes where it can access other containers (=components).
There is an Orchestrator Client (directory `orchestrator_client`) for controlling the orchestrator.

# How to use

Run the orchestrator via `./scripts/run-orchestrator.sh`.
Run the client via `./scripts/run-client.sh`.
This will use a sample solution in directory `./sample/`.

Generally the solution is created by the kubernetes-client of AI4EU Experiments platform, triggered in the platform with the button `Deploy to local` in each solution.

Orchestrator client usage:

```
python orchestrator_client.py [-h] [-H HOST] [-p PORT] [-e IP:PORT]
                              [-b BASEPATH]

optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  The host name or IP address of the orchestrator.
  -p PORT, --port PORT  The network port of the orchestrator.
  -e IP:PORT, --endpoint IP:PORT
                        The endpoint (combination of host and port) of the
                        orchestrator.
  -b BASEPATH, --basepath BASEPATH
                        The path where dockerinfo.json, blueprint.json, and
                        pipelineprotos.zip can be found.
```

# Technical Description

gRPC provides four flavors of calls: https://grpc.io/docs/what-is-grpc/core-concepts/

Initially we used the first one: classical RPC calls without streaming.

Now we permit all four types.

* We permit the stream keyword for input and output arguments and support 4 types of RPC calls.
* We ignore the stream keywork in AcuCompose (permit connection of stream to non-stream and vice versa).

This orchestrator does not ignore the keyword and connects in the right way to each component:

* The orchestrator redirects streams between components (each link in the blueprint becomes a `Queue`).
* The orchestrator convertes stream-to-rpc and rpc-to-stream (each operation in the blueprint becomes a `Thread`).
* Connections from a streaming output to a streaming input act as cycle-breakers in the (service-view of the) topology of the solution.

# Lifecycle

* Initialization: interpreting protobuf files, merging protobufs into one file, setting up queues and threads
* Run: starting threads and permitting RPC calls to be made. Empty input means "make the call immediately", input from a queue means "call when the first message arrives".
* Observation: it is possible to attach to an observation stream that receives all events produced in the orchestration.

Initialization can be done multiple times.
Runs can be done multiple times.

## RPC calls

Each RPC call that is connected to at least one link is managed by an Thread (`ai4eu.othread.OrchestrationThreadBase`).

Depending on stream keywords in input/output they operate as follows:

* Single input/single output: calls RPC if message is present for input queue, result is written to output queue.
* Single input/stream output: calls RPC if message is present for input queue, result is streamed to output queue. First all output is streamed into the output queue and then, if a new message appears in the input queue, the next call is started.
* Stream input/single output: calls RPC if message is present in input queue, streams further messages until RPC is closed. Result is written to output queue. If new message is present in input queue, start the next call.
* Stream input/stream output: call RPC once the first message is in the queue for stream input, stream further messages from/to input/output queues. If call is closed and new message is present in input queue, start the next call.

There are 2 special RPC flavors that are connected only to one component (sources/sinks):

* input type is `Empty`: needs no input connection

This is used for data brokers, GUIs, sensors, webcam streams, etc. that "trigger" processing in the application.

* output type is `Empty`: needs no output connection

This is used for data sinks, e.g., final nodes of a pipeline: GUIs, displays, audio output, logging, etc.

# Benefits and Caveats

## Benefits

The multithreaded architecture means that we do not need to analyze the topology to orchestrate.
Whenever a message can be passed it will be passed.

## Caveats

Every message passes through the orchestrator, so performance is less than it could be (if components would directly talk to each other).
However, AI4EU Experiments is intended for experiments. For real applications, something specific needs to be implemented in any case.
