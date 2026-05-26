#把检索结果整理为上下文和引用
from langchain_core.documents import Document
from pathlib import Path

def format_context(documents:list[Document])->str:
    context_blocks=[]
    for index,doc in enumerate(documents, start=1):
        source=doc.metadata.get("source","unknown")
        chunk_id=doc.metadata.get("chunk_id","unknown")
        page=doc.metadata.get("page","unknown")
        context_blocks.append(
            f"[{index}] source={source}, page={page}, chunk_id={chunk_id}\n"
            f"{doc.page_content}"
        )
    
    return "\n\n".join(context_blocks)

def build_sources(document:list[Document])->list[dict]:
    sources=[]
    for doc in document:
        source = doc.metadata.get("source")
        title = Path(source).name if source else "unknown"
        sources.append({
            "document_id":doc.metadata.get("document_id"),
            "chunk_id":doc.metadata.get("chunk_id"),
            "source":source,
            "title":title,
            "page":doc.metadata.get("page"),
            "content":doc.page_content[:500],
            "score":doc.metadata.get("reranker_score") or doc.metadata.get("rrf_score"),
        })    
    return sources
