"""Write vector store setup here."""
from pathlib import Path
from langchain_chroma import Chroma 
from app.core.config import settings    
from app.rag.embeddings import build_embeddings

def build_vectorstore(collection_name:str="rag_documents")->Chroma:
    persist_dir=Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True,exist_ok=True)
    
    return Chroma(
        collection_name=collection_name,
        embedding_function=build_embeddings(),
        persist_directory=str(persist_dir)
    )
    
def delete_vectors_by_document_id(document_id:str)->int:
    vectorstore=build_vectorstore()
    results=vectorstore.get(
        where={"document_id": document_id},
    )
    
    ids=results.get("ids", [])
    if not ids:
        return 0
    vectorstore.delete(ids=ids)
    return len(ids)

def clear_vectorstore() -> int:
    vectorstore = build_vectorstore()

    results = vectorstore.get()
    ids = results.get("ids", [])

    if not ids:
        return 0

    vectorstore.delete(ids=ids)

    return len(ids)