"""Write embedding provider setup here."""
import os 
from langchain_core.embeddings import Embeddings
from zhipuai import ZhipuAI

from app.core.config import settings
class ZhipuEmbeddings(Embeddings):
    def __init__(self):
        self.client=ZhipuAI(api_key=settings.zhipu_api_key)
        self.model=settings.embedding_model
        self.dimensions=int(settings.embedding_dimensions)
    
    def embed_documents(self, texts:list[str])->list[list[float]]:
        batch_size=32
        embeddings:list[list[float]]=[]
        
        for start in range(0,len(texts),batch_size):
            batch=texts[start:start+batch_size]
            response=self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            batch_embeddings=[item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        return embeddings #返回一个二维列表，每个子列表是对应输入文本的向量表示

    def embed_query(self, text:str)->list[float]:
        return self.embed_documents([text])[0]

def build_embeddings() -> Embeddings:
    return ZhipuEmbeddings()