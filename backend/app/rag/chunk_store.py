import json
from pathlib import Path

from langchain_core.documents import Document

CHUNK_STORE_PATH = Path("data/processed/chunks.jsonl")

#保存切分好的chunk，同时保存新的chunk，替换掉旧的chunk，避免重复存储相同document_id的chunk。
def save_chunks(documents: list[Document]) -> None:
    CHUNK_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

    document_ids = {
        doc.metadata.get("document_id")
        for doc in documents
        if doc.metadata.get("document_id")
    }

    existing_items = []

    if CHUNK_STORE_PATH.exists():
        with CHUNK_STORE_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                item = json.loads(line)
                metadata = item.get("metadata", {})

                if metadata.get("document_id") not in document_ids:
                    existing_items.append(item)

    new_items = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in documents
    ]

    with CHUNK_STORE_PATH.open("w", encoding="utf-8") as file:
        for item in existing_items + new_items:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

#从本地保存的chunk文件中加载chunk，返回一个Document对象列表，如果文件不存在则返回空列表。
def load_chunks() -> list[Document]:
    if not CHUNK_STORE_PATH.exists():
        return []

    documents = []

    with CHUNK_STORE_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            item = json.loads(line)
            documents.append(
                Document(
                    page_content=item["page_content"],
                    metadata=item.get("metadata", {}),
                )
            )

    return documents

#删除指定 document_id 的 chunk，返回被删除的 chunk 数量。如果文件不存在，说明没有 chunk 被删除，直接返回 0。
def delete_chunks_by_document_id(document_id: str) -> int:
    # 如果本地 chunk 存储文件不存在，说明还没有保存过 chunks，直接返回删除数量 0
    if not CHUNK_STORE_PATH.exists():
        return 0

    # 用来保存不需要删除的 chunk
    kept_items = []

    # 记录被删除的 chunk 数量
    deleted_count = 0

    # 打开 chunks.jsonl 文件，逐行读取
    with CHUNK_STORE_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            # 去掉每行首尾空格和换行符
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 把当前这一行 JSON 字符串解析成 Python 字典
            item = json.loads(line)

            # 取出当前 chunk 的 metadata
            metadata = item.get("metadata", {})

            # 如果当前 chunk 的 document_id 等于要删除的 document_id
            # 说明它属于目标文档，不加入 kept_items，相当于删除
            if metadata.get("document_id") == document_id:
                deleted_count += 1

            # 否则说明它属于其他文档，需要保留下来
            else:
                kept_items.append(item)

    # 用写入模式重新打开 chunks.jsonl
    # "w" 会覆盖原文件，所以这里只写入需要保留的 chunks
    with CHUNK_STORE_PATH.open("w", encoding="utf-8") as file:
        for item in kept_items:
            # 每个 chunk 仍然按 jsonl 格式写入：一行一个 JSON
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    # 返回本次删除了多少个 chunk
    return deleted_count   

def clear_chunks()->None:
    CHUNK_STORE_PATH.parent.mkdir(parents=True,exist_ok=True)
    CHUNK_STORE_PATH.write_text("",encoding="utf-8")