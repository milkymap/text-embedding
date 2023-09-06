
import zmq 

import signal 


from typing import List, Tuple, Dict, Any, Optional

from libraries.log import logger 
from libraries.zmqconfig import ZMQEndpoint, ZMQWorkerMessageType

class ZMQBroker:
    def __init__(self, polling_timeout:int):
        self.polling_timeout = polling_timeout

    def __handle_termination(self, signal_num, frame):
        signal.raise_signal(signal.SIGINT)

    def start_load_balencing(self):
        try:
            router_socket_for_worker = self.ctx.socket(zmq.ROUTER)
            router_socket_for_worker.bind(ZMQEndpoint.BROKER2WORKER)
        except Exception as e:
            logger.warning(e)
            raise Exception('can not create router_socket_for_worker')

        try:
            router_socket_for_client = self.ctx.socket(zmq.ROUTER)
            router_socket_for_client.bind(ZMQEndpoint.CLIENT2BROKER)
        except Exception as e:
            logger.warning(e)
            raise Exception('can not create router_socket_for_client')
        
        poller = zmq.Poller()
        poller.register(router_socket_for_client, zmq.POLLIN)
        poller.register(router_socket_for_worker, zmq.POLLIN)

        logger.info('broker is running')
        available_workers:List[bytes] = []
        keep_looping = True 
        while keep_looping:
            try:
                map_socket2value = dict(poller.poll(timeout=self.polling_timeout))
                if router_socket_for_worker in map_socket2value:
                    if map_socket2value[router_socket_for_worker] == zmq.POLLIN:
                        worker_id, _, worker_message_type, target_client_id, worker_response = router_socket_for_worker.recv_multipart()
                        if worker_message_type == ZMQWorkerMessageType.ASK_NEW_TASK:
                            available_workers.append(worker_id)
                        
                        if worker_message_type == ZMQWorkerMessageType.SEND_RESPONSE:
                            router_socket_for_client.send_multipart([target_client_id, _, worker_response])

                
                if router_socket_for_client in map_socket2value:
                    if map_socket2value[router_socket_for_client] == zmq.POLLIN:
                        if len(available_workers) > 0:
                            target_worker_id = available_workers.pop(0)
                            client_id, _, incoming_msg = router_socket_for_client.recv_multipart()
                            router_socket_for_worker.send_multipart([target_worker_id, b'', client_id, incoming_msg])

            except KeyboardInterrupt:
                keep_looping = False 
                logger.warning(f'broker has caught the SIGINT signal')
            except Exception as e:
                logger.error(e)
                keep_looping = False 

        poller.unregister(router_socket_for_client)
        poller.unregister(router_socket_for_worker)

        router_socket_for_worker.close(linger=0)
        router_socket_for_client.close(linger=0)

        logger.info('broker has released its resources')

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
    

    