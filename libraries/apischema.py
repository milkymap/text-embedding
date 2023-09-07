
from pydantic import BaseModel
from typing import List, Optional

class ComputeEmbeddingRequestModel(BaseModel):
    request_id:str 
    text:str 

class ComputeEmbeddingResponseContentModel(BaseModel):
    embedding:List[float]=[]

class ComputeEmbeddingResponseModel(BaseModel):
    request_id:str 
    status:bool
    content:Optional[ComputeEmbeddingResponseContentModel]=None
    error_message:str=None 