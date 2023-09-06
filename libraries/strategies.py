
import numpy as np 
import tiktoken

import operator as op 
import itertools as it, functools as ft 

from sentence_transformers import SentenceTransformer

from typing import List, Tuple, Dict, Any, Optional

def load_tokenizer(encoding_name:str='gpt-3.5-turbo') -> tiktoken.Encoding:
    return tiktoken.encoding_for_model(encoding_name)

def load_transformers(model_name:str, cache_folder:str, device:str='cpu') -> SentenceTransformer:
    return SentenceTransformer(
        model_name_or_path=model_name,
        cache_folder=cache_folder,
        device=device
    )

def split_text_into_chunks(text:str, chunk_size:int, tokenizer:tiktoken.Encoding) -> List[str]:
    tokens:List[int] = tokenizer.encode(text)
    nb_tokens = len(tokens)
    accumulator:List[str] = []
    for cursor in range(0, nb_tokens, chunk_size):
        paragraph = tokenizer.decode(tokens[cursor:cursor+chunk_size]) 
        accumulator.append(paragraph)
    
    return accumulator
