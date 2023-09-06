import numpy as np 
from libraries.services.worker import ZMQWorker
from sentence_transformers import SentenceTransformer

from libraries.strategies import load_tokenizer, split_text_into_chunks

from typing import List 


class TEXTVectorizer(ZMQWorker):
    def __init__(self, worker_id:str, polling_timeout:int, model_name:str, cache_folder:str, device:str='cpu', chunk_size:int=128):
        super(TEXTVectorizer, self).__init__(worker_id, polling_timeout)
        self.device = device 
        self.model = SentenceTransformer(model_name_or_path=model_name, cache_folder=cache_folder, device=self.device)
        self.tokenizer = load_tokenizer(encoding_name='gpt-3.5-turbo')
        self.chunk_size = chunk_size 

    def process_message(self, incoming_req: bytes) -> np.ndarray:
        text = incoming_req.decode()
        chunks:List[str] = split_text_into_chunks(text, chunk_size=self.chunk_size, tokenizer=self.tokenizer)
        embeddings:np.ndarray = self.model.encode(sentences=chunks, batch_size=32, device=self.device)
        
        if len(embeddings.shape) == 2:
            return embeddings[0].tolist()
        
        dot_scores = embeddings @ embeddings.T
        embedding_norms = np.linalg.norm(embeddings, axis=1)
        weighted_dot_scores = dot_scores / (embedding_norms[:, None] * embedding_norms[None, :])
        aggregated_dot_scores = np.sum(weighted_dot_scores, axis=1, keepdims=True)

        weighted_average_embedding = np.mean(aggregated_dot_scores * embeddings, axis=0)
        return weighted_average_embedding.tolist()
