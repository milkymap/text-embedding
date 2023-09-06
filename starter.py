
import asyncio 

from server import APIServer
from vectorizer import TEXTVectorizer

from libraries.services.broker import ZMQBroker

def launch_server(host:str, port:int, mounting_path:str):
    async def __start_server():
        async with APIServer(port=port, host=host, mounting_path=mounting_path) as server_agent:
            await server_agent.start_serving()

    asyncio.run(__start_server())

def launch_broker(polling_timeout:int):
    with ZMQBroker(polling_timeout) as broker_agent:
        broker_agent.start_load_balencing()

def launch_vectorizer(worker_id:int, polling_timeout:int, model_name:str, cache_folder:str, device:str='cpu', chunk_size:int=128):
    with TEXTVectorizer(worker_id, polling_timeout, model_name, cache_folder, device, chunk_size) as worker_agent:
        worker_agent.start_consuming()
