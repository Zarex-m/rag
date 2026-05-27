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
        # Obsidian 笔记优先使用解析出来的标题，避免插件来源区只显示 “未命名.md”。
        title = doc.metadata.get("title") or (Path(source).name if source else "unknown")
        sources.append({
            "document_id":doc.metadata.get("document_id"),
            "chunk_id":doc.metadata.get("chunk_id"),
            "source":source,
            "title":title,
            "page":doc.metadata.get("page"),
            "content":doc.page_content[:500],
            "score":doc.metadata.get("reranker_score") or doc.metadata.get("rrf_score"),
            # 以下字段主要给 Obsidian 插件使用：展示来源类型、标签、文件夹，并支持跳回原笔记。
            "source_type": doc.metadata.get("source_type"),
            "vault_name": doc.metadata.get("vault_name"),
            "vault_relative_path": doc.metadata.get("vault_relative_path"),
            "folder": doc.metadata.get("folder"),
            "tags": doc.metadata.get("tags"),
            "links": doc.metadata.get("links"),
        })    
    return sources
