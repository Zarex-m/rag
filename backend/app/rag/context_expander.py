from langchain_core.documents import Document

from app.rag.chunk_store import find_neighbor_chunks

#对检索结果逐个做相邻扩展，并去重，避免重复 chunk 塞进上下文。
def expand_with_neighbors(
    documents: list[Document],
    window: int = 1,
    max_documents: int = 8,
) -> list[Document]:
    results: list[Document] = []
    seen: set[str] = set()

    for document in documents:
        document_id = document.metadata.get("document_id")
        chunk_index = document.metadata.get("chunk_index")

        if document_id is None or chunk_index is None:
            candidates = [document]
        else:
            candidates = find_neighbor_chunks(
                document_id=str(document_id),
                chunk_index=int(chunk_index),
                window=window,
            )

        for candidate in candidates:
            chunk_id = candidate.metadata.get("chunk_id")
            key = str(chunk_id) if chunk_id else candidate.page_content

            if key in seen:
                continue

            seen.add(key)
            results.append(candidate)

            if len(results) >= max_documents:
                return results

    return results