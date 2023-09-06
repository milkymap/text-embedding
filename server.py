import zmq 
import zmq.asyncio as aiozmq 

import pickle 

import asyncio
import uvicorn 
from fastapi import FastAPI
from fastapi import HTTPException, BackgroundTasks

import signal 

from libraries.log import logger 
from libraries.apischema import TextEmbeddingReqBaseModel, TextEmbeddingResBaseModel
from libraries.zmqconfig import ZMQEndpoint

class APIServer:
    def __init__(self, port:int, host:str, mounting_path:str="/"):
        self.host = host 
        self.port = port 
        self.mounting_path = mounting_path
        
        self.app = FastAPI(
            title="text-embedding",
            docs_url="/",
            version='0.0.1',
            description="""
                This API server provides a fast and efficient text embedding service. It allows clients to send text data and receive corresponding embeddings. The server leverages asynchronous processing and a distributed architecture to ensure quick and reliable responses.

                Features:
                - Fast Text Embedding: Submit text data and receive its embedding for various NLP tasks.
                - Asynchronous Processing: Utilizes asyncio and FastAPI to handle multiple requests concurrently.
                - Distributed Architecture: Distributes tasks to worker nodes for efficient computation.
                - Graceful Termination: Gracefully handles server termination, canceling background tasks and cleaning up resources.

                Endpoints:
                - POST /embedding: Submit text for embedding. Returns the embedding result.

                Please note that this is a minimal version (0.0.1) of the API server, and additional features may be added in the future.
            """
        )

        self.app.add_event_handler('startup', self.handle_startup)
        self.app.add_event_handler('shutdown', self.handle_shutdown)

        self.app.add_api_route('/embedding', self.handle_embedding, methods=['POST'], response_model=TextEmbeddingResBaseModel)
    
    async def handle_embedding(self, incoming_req:TextEmbeddingReqBaseModel):
        text = incoming_req.text
        try:
            dealer_socket:aiozmq.Socket = self.ctx.socket(zmq.DEALER)
            dealer_socket.connect(ZMQEndpoint.CLIENT2BROKER)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f'can not create new dealer socket => {e}'
            )
        
        encoded_text = text.encode('utf-8')
        await dealer_socket.send_multipart([b'', encoded_text])

        _, worker_response = await dealer_socket.recv_multipart()
        worker_response_status, worker_response_data = pickle.loads(worker_response)

        dealer_socket.close(linger=0)

        if worker_response_status == True:
            return TextEmbeddingResBaseModel(
                embedding=worker_response_data
            )
        
        raise HTTPException(
            status_code=500,
            detail='worker was not able to compute the embedding'
        )
    
    async def __handle_termination(self):
        signal.raise_signal(signal.SIGINT)
    
    async def __handle_interruption(self):
        logger.info('SIGINT was caught ...!')
        tasks = [task for task in asyncio.all_tasks() if task.get_name().startswith('background-task')]
        for task in tasks:
            task.cancel()
            
        await asyncio.gather(*tasks)
        logger.info('all background tasks were removed')
        self.server.should_exit = True 

    async def handle_startup(self):
        self.ctx = aiozmq.Context()
        self.loop = asyncio.get_running_loop()
        self.loop.add_signal_handler(
            signal.SIGTERM,
            lambda: asyncio.create_task(self.__handle_termination())
        )
        self.loop.add_signal_handler(
            signal.SIGINT,
            lambda: asyncio.create_task(self.__handle_interruption())
        )
        
        logger.info('server has started its execution')

    async def handle_shutdown(self):
        self.ctx.term()
        logger.info('server has stopped its execution')

    async def start_serving(self):
        await self.server.serve()
    
    async def __aenter__(self):
        self.config = uvicorn.Config(host=self.host, port=self.port, app=self.app, root_path=self.mounting_path)
        self.server = uvicorn.Server(self.config)
        return self 
        
    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error(exc_value)
            logger.exception(traceback)

