#文档入库服务
from pathlib import Path

from app.rag.vectorstore import build_vectorstore
from app.rag.loaders import load_document
from app.rag.splitters import split_documents
from app.rag.chunk_store import save_chunks
from app.rag.chunk_store import clear_chunks
from app.rag.vectorstore import clear_vectorstore
from app.services.document_service import list_raw_document_files
from app.rag.text_cleaner import clean_text,is_valid_chunk

async def ingest_document(
    file_path: str,
    document_id: str,
    extra_metadata: dict | None = None,
) -> dict:
    # extra_metadata 是为 Obsidian/其他外部知识源预留的扩展口，不影响普通上传文件入库。
    path=Path(file_path)
    
    docs=load_document(str(path))
    chunks=split_documents(docs)
    #给每一个chunk打上索引，一个chunk包含文本内容和元信息，元信息包括文档id、chunk id、来源路径、chunk索引等
    cleaned_chunks = []

    for index, chunk in enumerate(chunks):
        chunk.page_content = clean_text(chunk.page_content)

        if not is_valid_chunk(chunk.page_content):
            continue

        chunk.metadata["document_id"] = document_id
        chunk.metadata["chunk_id"] = f"{document_id}-chunk-{index}"
        chunk.metadata["source"] = str(path)
        chunk.metadata["chunk_index"] = index
        chunk.metadata["filename"] = path.name
        chunk.metadata["chapter"] = extract_chapter(path.name)
        chunk.metadata["content_length"] = len(chunk.page_content)

        if extra_metadata:
            # Obsidian 导入会在这里补充 source_type、vault_relative_path、tags、links 等信息。
            chunk.metadata.update(extra_metadata)

        cleaned_chunks.append(chunk)

    if not cleaned_chunks:
        # 有些 Obsidian 空笔记或模板笔记清洗后没有有效内容，直接跳过，避免向量库写入空 embeddings。
        return {
            "document_id": document_id,
            "status": "skipped",
            "num_chunks": 0,
            "vector_ids": [],
        }
    
    vectorstore=build_vectorstore()
    
    #ids是vectorstore为每个chunk生成的唯一标识符，后续可以通过这个id来检索对应的chunk内容和元信息
    ids=vectorstore.add_documents(cleaned_chunks)
    save_chunks(cleaned_chunks) 
    return {
        "document_id":document_id,
        "status":"indexed",
        "num_chunks":len(cleaned_chunks),
        "vector_ids":ids
    }



async def rebuild_index()->dict:
    #返回被删除的向量数量
    deleted_vectors=clear_vectorstore()
    clear_chunks()
    
    documents=list_raw_document_files()
    
    indexed_documents=0
    total_chunks=0
    errors=[]
    
    for document in documents:
        try:
            result=await ingest_document(
                file_path=document["file_path"],
                document_id=document["document_id"]
            )
            indexed_documents+=1
            total_chunks+=result.get("num_chunks",0)
        except Exception as exc:
            errors.append({
                "document_id":document["document_id"],
                "filename":document["filename"],
                "error":str(exc)
            })
    return {
        "status":"completed",
        "deleted_vectors":deleted_vectors,
        "indexed_documents":indexed_documents,
        "total_chunks":total_chunks,
        "errors":errors
    }

def extract_chapter(filename: str) -> str | None:
    name = filename.rsplit(".", 1)[0]
    if "章" in name:
        return name
    return None
