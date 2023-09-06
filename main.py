import click 
import torch as th 

from vectorizer import TEXTVectorizer

from libraries.log import logger 

from dotenv import load_dotenv

import multiprocessing as mp 

from time import sleep 

from typing import List 
from starter import launch_broker, launch_server, launch_vectorizer

@click.command()
@click.option('--host', default="0.0.0.0")
@click.option('--port', default=8000)
@click.option('--mounting_path', type=str, default='/')
@click.option('--model_name', required=True)
@click.option('--nb_workers', type=int, default=1)
@click.option('--chunk_size', type=int, default=128)
@click.option('--polling_timeout', type=int, default=100)
@click.option('--cache_folder', envvar='TRANSFORMERS_CACHE', required=True, type=click.Path(exists=True, file_okay=False))
@click.option('--protocol_buffers', envvar='PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION', required=True, type=click.Choice(['python']))
def main(host:str, port:int, mounting_path:str, model_name:str, nb_workers:int, chunk_size:int, polling_timeout:int, cache_folder:str, protocol_buffers:str):
    device = 'cuda:0' if th.cuda.is_available() else 'cpu'
    th.multiprocessing.set_start_method('spawn')
    logger.info('multiprocessing => start_method set to spawn for cuda')

    processes:List[mp.Process] = [
        mp.Process(target=launch_server, args=[host, port, mounting_path]),
        mp.Process(target=launch_broker, args=[polling_timeout])
    ]

    for worker_id in range(nb_workers):
        processes.append(
            mp.Process(
                target=launch_vectorizer,
                args=[f'txt-embedding-{worker_id:03d}', polling_timeout, model_name, cache_folder, device, chunk_size]
            )
        )
    
    for p in processes:
        try:
            p.start()
        except Exception as e:
            logger.error(e)

    keep_monitoring = True 
    while keep_monitoring:
        try:
            if any([ p.exitcode is not None for p in processes ]):
                keep_monitoring = False 
            sleep(3)
        except KeyboardInterrupt:
            for p in processes:
                p.terminate()  # send SIGTERM
                p.join()
    
    for p in processes:
        if p.exitcode is None:
            p.terminate()
            p.join()


if __name__ == '__main__':
    load_dotenv()
    main()
