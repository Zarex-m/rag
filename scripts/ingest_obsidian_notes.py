import argparse
import asyncio
import hashlib
from pathlib import Path

from langchain_core.documents import Document

from app.rag.chunk_store import clear_chunks, save_chunks
from app.rag.markdown_cleaner import (
    build_title_path,
    clean_markdown_text,
    extract_markdown_tags,
    extract_markdown_title,
    inject_title_path,
)
from app.rag.splitters import split_documents
from app.rag.text_cleaner import clean_text, is_valid_chunk
from app.rag.vectorstore import build_vectorstore, clear_vectorstore


DEFAULT_NOTE_ROOTS = [
    Path("/Users/zarex/Desktop/obsidian库/cpp"),
    Path("/Users/zarex/Desktop/obsidian库/数据结构与算法"),
]


def build_document_id(path: Path) -> str:
    digest = hashlib.md5(str(path).encode("utf-8")).hexdigest()
    return f"obsidian-{digest}"


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if ".obsidian" in parts:
        return True
    if path.name.endswith(".excalidraw.md"):
        return True
    return False


def collect_note_files(note_roots: list[Path]) -> list[Path]:
    files = []

    for root in note_roots:
        if not root.exists():
            continue

        for path in root.rglob("*.md"):
            if should_skip(path):
                continue
            files.append(path)

    return sorted(files)


def load_note(path: Path, root: Path) -> Document | None:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    tags = extract_markdown_tags(raw_text)
    text = clean_markdown_text(raw_text)
    text = clean_text(text)

    if not text.strip():
        return None

    relative_path = path.relative_to(root)
    folder = str(relative_path.parent) if str(relative_path.parent) != "." else ""
    document_id = build_document_id(path)
    title = extract_markdown_title(text, path.stem)
    title_path = build_title_path(root.name, relative_path, title)
    text = inject_title_path(text, title_path)

    metadata = {
            "source": str(path),
            "document_id": document_id,
            "filename": path.name,
            "title": title,
            "title_path": title_path,
            "source_type": "obsidian",
            "vault_name": root.name,
            "vault_root": str(root),
            "vault_relative_path": str(relative_path),
            "folder": folder,
    }

    if tags:
        metadata["tags"] = ",".join(tags)

    return Document(
        page_content=text,
        metadata=metadata,
    )


async def ingest_obsidian_notes(note_roots: list[Path], clear_existing: bool = True) -> dict:
    if clear_existing:
        deleted_vectors = clear_vectorstore()
        clear_chunks()
    else:
        deleted_vectors = 0

    note_files = collect_note_files(note_roots)
    documents = []
    errors = []

    for root in note_roots:
        for path in [item for item in note_files if root in item.parents or item == root]:
            try:
                document = load_note(path, root)
                if document is not None:
                    documents.append(document)
            except Exception as exc:
                errors.append({"file": str(path), "error": str(exc)})

    chunks = split_documents(documents)
    cleaned_chunks = []

    chunk_counts_by_document: dict[str, int] = {}

    for chunk in chunks:
        chunk.page_content = clean_text(chunk.page_content)
        if not is_valid_chunk(chunk.page_content):
            continue

        document_id = chunk.metadata["document_id"]
        chunk_index = chunk_counts_by_document.get(document_id, 0)
        chunk_counts_by_document[document_id] = chunk_index + 1

        chunk.metadata["chunk_id"] = f"{document_id}-chunk-{chunk_index}"
        chunk.metadata["chunk_index"] = chunk_index
        chunk.metadata["content_length"] = len(chunk.page_content)
        chunk.metadata["chapter"] = chunk.metadata.get("folder") or chunk.metadata.get("title")
        chunk.metadata["title_path"] = chunk.metadata.get("title_path", "")

        cleaned_chunks.append(chunk)

    if cleaned_chunks:
        vectorstore = build_vectorstore()
        vectorstore.add_documents(cleaned_chunks)
        save_chunks(cleaned_chunks)

    return {
        "status": "completed",
        "deleted_vectors": deleted_vectors,
        "note_roots": [str(root) for root in note_roots],
        "note_files": len(note_files),
        "loaded_documents": len(documents),
        "total_chunks": len(cleaned_chunks),
        "errors": errors,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest selected Obsidian notes into the RAG index.")
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="Obsidian note root to ingest. Can be passed multiple times.",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not clear the existing vector store and chunk store before ingesting.",
    )
    args = parser.parse_args()

    note_roots = [Path(root).expanduser() for root in args.root] if args.root else DEFAULT_NOTE_ROOTS
    result = await ingest_obsidian_notes(
        note_roots=note_roots,
        clear_existing=not args.keep_existing,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
