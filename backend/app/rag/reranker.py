from functools import lru_cache

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

@lru_cache(maxsize=1) #缓存 CrossEncoder 对象，避免重复加载模型
def get_reranker() -> CrossEncoder:
    return CrossEncoder("BAAI/bge-reranker-base")

def rerank_documents(
    query:str,
    documents:list[Document],
    top_k:int=5,
)->list[Document]:
    if not documents:
        return []
    
    model=get_reranker()
    pairs=[(query,document.page_content)for document in documents]
    scores=model.predict(pairs)
    
    scored_docs=list(zip(documents,scores))
    scored_docs.sort(key=lambda x:x[1],reverse=True)
    
    results=[]
    for document,score in scored_docs[:top_k]:
        document.metadata["reranker_score"]=float(score)
        results.append(document)
    return results
