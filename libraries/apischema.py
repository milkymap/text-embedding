
from pydantic import BaseModel
from typing import List, Optional

class TextEmbeddingReqBaseModel(BaseModel):
    text: str 

class TextEmbeddingResBaseModel(BaseModel):
    embedding:Optional[List[float]]
