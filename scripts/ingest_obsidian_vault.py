import argparse
import asyncio
from pathlib import Path

from app.rag.chunk_store import clear_chunks
from app.rag.obsidian import (
    build_obsidian_document_id,
    extract_obsidian_metadata,
    iter_obsidian_notes,
)
from app.rag.vectorstore import clear_vectorstore
from app.services.ingest_service import ingest_document


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest an Obsidian vault into the RAG index.")
    parser.add_argument("--vault", required=True, help="Path to the Obsidian vault directory.")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vectors and chunk store before importing the vault.",
    )
    args = parser.parse_args()

    vault_path = Path(args.vault).expanduser().resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise ValueError(f"Vault path not found: {vault_path}")

    if args.clear:
        # 重新构建 Obsidian 知识库时使用；不加 --clear 则会在现有 PDF/Markdown 索引上追加。
        clear_vectorstore()
        clear_chunks()

    notes = iter_obsidian_notes(vault_path)
    indexed_notes = 0
    total_chunks = 0
    errors = []

    for note_path in notes:
        try:
            # document_id 基于 Vault 相对路径生成，保证同一篇笔记多次导入时 id 稳定。
            document_id = build_obsidian_document_id(vault_path, note_path)
            # 额外 metadata 用来支持插件侧展示标题、标签、文件夹和“打开笔记”。
            metadata = extract_obsidian_metadata(vault_path, note_path)

            # 复用项目原来的通用入库链路：Loader -> Splitter -> Cleaner -> Embedding -> Chroma。
            result = await ingest_document(
                file_path=str(note_path),
                document_id=document_id,
                extra_metadata=metadata,
            )

            indexed_notes += 1
            total_chunks += result.get("num_chunks", 0)

        except Exception as exc:
            errors.append(
                {
                    "file": str(note_path),
                    "error": str(exc),
                }
            )

    print(
        {
            "status": "completed",
            "vault": str(vault_path),
            "total_notes": len(notes),
            "indexed_notes": indexed_notes,
            "total_chunks": total_chunks,
            "errors": errors,
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
