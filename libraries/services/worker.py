import zmq 
import signal 

from typing import List, Tuple, Dict, Any, Optional
from abc import ABC, abstractmethod

from libraries.log import logger 
from libraries.zmqconfig import ZMQWorkerMessageType, ZMQEndpoint

class ZMQWorker(ABC):
    def __init__(self, worker_id:str, polling_timeout:int):
        self.worker_id = worker_id 
        self.polling_timeout = polling_timeout 

    def __handle_termination(self, signal_num, frame):
        signal.raise_signal(signal.SIGINT)
    
    def __consume_message(self, incoming_msg:bytes) -> Tuple[bool, Optional[Any]]:
        try:
            response = self.process_message(incoming_msg)
            return True, response 
        except Exception as e:
            logger.error(e)
            return False, None  
    
    @abstractmethod
    def process_message(self, incoming_msg:bytes) -> Any:
        pass 

    def start_consuming(self):
        try:
            dealer_socket = self.ctx.socket(zmq.DEALER)
            dealer_socket.connect(ZMQEndpoint.BROKER2WORKER)
        except Exception as e:
            logger.warning(e)
            raise Exception('can not create dealer socket')

        poller = zmq.Poller()
        poller.register(dealer_socket, zmq.POLLIN)

        
        logger.info(f'worker {self.worker_id} is running')
        has_asked_new_job = False 
        keep_looping = True 
        while keep_looping:
            try:
                if not has_asked_new_job:
                    dealer_socket.send_multipart([b'', ZMQWorkerMessageType.ASK_NEW_TASK, b'', b''])
                    has_asked_new_job = True 
                
                map_socket2value = dict(poller.poll(timeout=self.polling_timeout))
                if dealer_socket in map_socket2value:
                    dealer_polling_value = map_socket2value[dealer_socket]
                    if dealer_polling_value == zmq.POLLIN:
                        _, client_id, incoming_msg = dealer_socket.recv_multipart()
                        response = self.__consume_message(incoming_msg)
                        dealer_socket.send_multipart([b'', ZMQWorkerMessageType.SEND_RESPONSE, client_id],flags=zmq.SNDMORE)
                        dealer_socket.send_pyobj(response)
                        has_asked_new_job = False 
            except KeyboardInterrupt:
                keep_looping = False 
                logger.warning(f'worker {self.worker_id} has caught the SIGINT signal')
            except Exception as e:
                logger.error(e)
                keep_looping = False 

        poller.unregister(dealer_socket)
        dealer_socket.close(linger=0) 

        logger.info(f'worker {self.worker_id} has released its resources')

    def __enter__(self):
        signal.signal(
            signal.SIGTERM,
            self.__handle_termination
        )
        self.ctx = zmq.Context()
        return self 

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error(exc_value)
            logger.exception(traceback)

        self.ctx.term()    