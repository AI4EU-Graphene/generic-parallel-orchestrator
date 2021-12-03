import logging
import threading
import traceback
import grpc
import importlib
import time

from queue import Queue, Full, Empty
from typing import Dict, Any, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod


class Event(BaseModel):
    run: Optional[str]
    name: str
    component: str
    detail: Dict[str, Any]


class OrchestrationObserver(ABC):
    @abstractmethod
    def event(self, evt: Event):
        pass


class LoggingOrchestrationObserver(OrchestrationObserver):
    def event(self, evt: Event):
        shortdetail = {
            k: v
            for k, v in evt.detail.items()
            if k not in 'message'}
        messagedetail = ''
        if 'message' in evt.detail:
            messagedetail = ' (message length %d)' % len(str(evt.detail['message']))
        logging.info("Orchestration Event: %s/%s %s%s", evt.component, evt.name, shortdetail, messagedetail)


class OrchestrationQueue(ABC):
    queue: Queue

    @abstractmethod
    def __init__(self, name: str, internal_queue: Queue, observer: OrchestrationObserver):
        self.name = name
        self.observer = observer
        self.queue = internal_queue

    def _event(self, name: str, detail: dict):

        # only transfer datatypes that can be understood by the orchestrator client for sure
        converted_detail = {}
        for k, v in detail.items():
            if not isinstance(v, (str, int, float)):
                converted_detail[k] = str(v)
            else:
                converted_detail[k] = v

        self.observer.event(Event(
            component=str(self),
            name=name,
            detail=converted_detail))

    def __str__(self):
        return 'OrchestrationQueue[%s]' % self.name

    def add(self, message: Any):
        try:
            self.queue.put_nowait(message)
            self._event('queue.added', {'queue': self.name, 'message': message})
        except Full:
            self._event('queue.discarded', {'queue': self.name, 'message': message})

    def poll(self) -> Any or None:
        '''
        return consume() if there is a message in the queue, None otherwise
        '''
        try:
            return self._consume(block=False)
        except Empty:
            self._event('queue.polled_empty', {'queue': self.name})
            return None

    def consume(self, timeout=None) -> Optional[Any]:
        '''
        wait for queue to contain element, remove and return
        notify on consumption
        '''
        return self._consume(block=True, timeout=timeout)

    def qsize(self) -> int:
        return self.queue.qsize()

    def _consume(self, block: bool, timeout=None) -> Optional[Any]:
        try:
            message = self.queue.get(block=block, timeout=timeout)
            self._event('queue.consumed', {'queue': self.name, 'message': message})
        except Empty:
            message = None
        return message


class LimitlessOrchestrationQueue(OrchestrationQueue):
    def __init__(self, name: str, observer: OrchestrationObserver):
        super().__init__(name, Queue(maxsize=0), observer)


class LatestMessageOrchestrationQueue(OrchestrationQueue):
    def __init__(self, name: str, observer: OrchestrationObserver):
        super().__init__(name, Queue(maxsize=1), observer)


class OrchestrationThreadBase(threading.Thread):
    class EasyTerminate(Exception):
        pass

    def __init__(
        self,
        component: str,  # for identification purposes
        host: str, port: int,
        protobuf_module, grpc_module,
        servicename: str, rpcname: str,
        observer: OrchestrationObserver,
        empty_in: bool = False, empty_out: bool = False,
    ):
        super().__init__(daemon=True)

        self.component = component
        self.host = host
        self.port = port
        self.protobuf_module = protobuf_module
        self.grpc_module = grpc_module
        self.servicename = servicename
        self.rpcname = rpcname
        self.observer = observer
        self.empty_in = empty_in
        self.empty_out = empty_out

        self.shall_terminate = False

        self.input_queue = None
        self.output_queues = []

        self.channel = None

    def resolve_and_create_service_stub(self, channel):
        return getattr(self.grpc_module, self.servicename + 'Stub')(channel)

    def resolve_protobuf_message(self, messagename: str):
        return getattr(self.protobuf_module, messagename)

    def _event(self, name: str, detail: dict):

        # only transfer datatypes that can be understood by the orchestrator client for sure
        converted_detail = {}
        for k, v in detail.items():
            if not isinstance(v, (str, int, float)):
                converted_detail[k] = str(v)
            else:
                converted_detail[k] = v

        self.observer.event(Event(
            component=str(self),
            name=name,
            detail=converted_detail))

    def attach_input_queue(self, q: OrchestrationQueue):
        '''
        connect input queue
        '''
        if self.input_queue is not None:
            raise RuntimeError("cannot attach more than one queue to thread %s" % str(self))
        self.input_queue = q

    def attach_output_queue(self, q: OrchestrationQueue):
        '''
        connect output queue
        '''
        if q in self.output_queues:
            raise RuntimeError("cannot attach the same queue %s twice to thread %s" % (str(q), str(self)))
        self.output_queues.append(q)

    def _wait_for_or_create_input(self):
        in_message = None
        if not self.empty_in:
            while not self.shall_terminate and in_message is None:
                in_message = self.input_queue.consume(timeout=1.0)
        else:
            in_message = self.resolve_protobuf_message('Empty')()

        # raising here is easier than changing all threads
        if self.shall_terminate:
            raise self.EasyTerminate()

        return in_message

    def _distribute_or_ignore_output(self, out_message):
        if not self.empty_out:
            # distribute message to all output queues
            for oq in self.output_queues:
                oq.add(out_message)

    def __str__(self):
        return f'OrchestrationThreadBase[component={self.component},svc={self.servicename},rpc={self.rpcname}]'

    def terminate(self):
        '''
        send termination flag and do not wait for termination
        '''
        if self.channel is not None:
            self.channel.close()
        self.shall_terminate = True


class StreamOutOrchestrationThread(OrchestrationThreadBase):
    def run(self):
        self._event('thread.start', {})
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        stub = self.resolve_and_create_service_stub(self.channel)
        try:
            while True:
                in_message = self._wait_for_or_create_input()
                self._event('RPC.call', {'rpc': self.rpcname, 'message': in_message})
                rpcresult = getattr(stub, self.rpcname)(in_message)
                for out_message in rpcresult:
                    self._event('distributing streaming output', {'rpc': self.rpcname, 'message': out_message})
                    self._distribute_or_ignore_output(out_message)
                self._event('RPC.finished', {'rpc': self.rpcname})
        except self.EasyTerminate:
            pass
        except Exception:
            logging.error(traceback.format_exc())
        self._event('thread.terminate', {})


class NonstreamOrchestrationThread(OrchestrationThreadBase):
    def run(self):
        self._event('thread.start', {})
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        stub = self.resolve_and_create_service_stub(self.channel)
        try:
            while True:
                in_message = self._wait_for_or_create_input()
                self._event('RPC.call', {'rpc': self.rpcname, 'message': in_message})
                out_message = getattr(stub, self.rpcname)(in_message)
                self._event('distributing output message', {'rpc': self.rpcname, 'message': out_message})
                self._distribute_or_ignore_output(out_message)
                self._event('RPC.finished', {'rpc': self.rpcname})
        except self.EasyTerminate:
            pass
        except Exception:
            logging.error(traceback.format_exc())
        self._event('thread.terminate', {})


class InputIteratorFromOrchestrationQueue:
    def __init__(self, t: OrchestrationThreadBase, q: OrchestrationQueue):
        self.t = t
        self.q = q

    def __iter__(self):
        while True:
            e = self.q.consume(timeout=1.0)
            if e is not None:
                # TODO remember "unconsumed" if exception during yield and usefor next rpc call
                yield e
            elif self.t.shall_terminate:
                raise self.t.EasyTerminate()


class StreamInOrchestrationThread(OrchestrationThreadBase):
    def run(self):
        self._event('thread.start', {})
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        stub = self.resolve_and_create_service_stub(self.channel)
        assert(self.empty_in is False)
        try:

            while True:

                # wait for next input message that can trigger a RPC call
                while self.input_queue.qsize() == 0 and not self.shall_terminate:
                    time.sleep(0.1)
                if self.shall_terminate:
                    raise self.EasyTerminate()

                # start RPC call, streaming in messages from queue
                in_message_iterator = InputIteratorFromOrchestrationQueue(self, self.input_queue)
                self._event('RPC.call', {'rpc': self.rpcname})
                out_message = getattr(stub, self.rpcname)(in_message_iterator.__iter__())

                # distribute the single output message
                self._event('distributing output message', {'rpc': self.rpcname, 'message': out_message})
                self._distribute_or_ignore_output(out_message)
                self._event('RPC.finished', {'rpc': self.rpcname})
        except self.EasyTerminate:
            pass
        except Exception:
            logging.error(traceback.format_exc())
        self._event('thread.terminate', {})


class StreamInOutOrchestrationThread(OrchestrationThreadBase):
    def run(self):
        self._event('thread.start', {})
        self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
        stub = self.resolve_and_create_service_stub(self.channel)
        assert(self.empty_in is False)
        try:

            while True:

                # wait for next input message that can trigger a RPC call
                while self.input_queue.qsize() == 0 and not self.shall_terminate:
                    time.sleep(0.1)
                if self.shall_terminate:
                    raise self.EasyTerminate()

                # start RPC call, streaming in messages from queue
                in_message_iterator = InputIteratorFromOrchestrationQueue(self.input_queue)
                self._event('RPC.call', {'rpc': self.rpcname})
                rpcresult = getattr(stub, self.rpcname)(in_message_iterator.__iter__())

                # distribute output messages (this happens in parallel to input iteration)
                for out_message in rpcresult:
                    self._event('distributing streaming output', {'rpc': self.rpcname, 'message': out_message})
                    self._distribute_or_ignore_output(out_message)
                self._event('RPC.finished', {'rpc': self.rpcname})

        except self.EasyTerminate:
            pass
        except Exception:
            logging.error(traceback.format_exc())

        self._event('thread.terminate', {})


class OrchestrationManager:
    threads: Dict[str, OrchestrationThreadBase]
    queues: Dict[str, OrchestrationQueue]
    observer: OrchestrationObserver

    def __init__(self, merged_protobuf_module, merged_grpc_module, observer=LoggingOrchestrationObserver()):
        self.threads = {}
        self.queues = {}
        self.observer = observer
        self.protobuf_module = merged_protobuf_module
        self.grpc_module = merged_grpc_module

        # key = (stream_in, stream_out)
        self.THREAD_TYPES = {
            (False, False): NonstreamOrchestrationThread,
            (False, True): StreamOutOrchestrationThread,
            (True, False): StreamInOrchestrationThread,
            (True, True): StreamInOutOrchestrationThread,
        }

    def create_thread(
        self,
        component: str,
        stream_in: bool, stream_out: bool,
        host: str, port: int,
        service: str, rpc: str,
        empty_in: bool = False, empty_out: bool = False,
    ) -> OrchestrationThreadBase:

        name = f'{component}/{service}.{rpc}'
        assert(name not in self.threads)

        Thread_type = self.THREAD_TYPES[(stream_in, stream_out)]
        t = Thread_type(component, host, port, self.protobuf_module, self.grpc_module, service, rpc, self.observer, empty_in, empty_out)
        self.threads[name] = t

        return t

    def create_queue(
        self,
        name: str, message: str
    ) -> OrchestrationQueue:

        assert(name not in self.queues)

        Queue_type = LimitlessOrchestrationQueue
        q = Queue_type(name, self.observer)
        self.queues[name] = q

        return q

    def orchestrate(self):
        self.start_orchestration()
        self.wait_for_orchestration()

    def start_orchestration(self):
        for name, t in self.threads.items():
            logging.debug("starting %s", name)
            t.start()

    def terminate_orchestration(self):
        for name, t in self.threads.items():
            logging.debug("terminating %s", name)
            t.terminate()
        self.wait_for_orchestration()

    def wait_for_orchestration(self):
        for name, t in self.threads.items():
            logging.debug("joining %s", name)
            t.join()
