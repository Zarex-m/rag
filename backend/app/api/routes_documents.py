"""Write document routes here."""
from fastapi import APIRouter, UploadFile, File
from app.services.document_service import save_uploaded_file   
from app.services.ingest_service import ingest_document
from app.services.document_service import list_uploaded_documents
from app.rag.chunk_store import delete_chunks_by_document_id
from app.rag.vectorstore import delete_vectors_by_document_id
from app.services.document_service import delete_raw_document
from app.services.ingest_service import rebuild_index
from app.core.responses import ok
router=APIRouter()

@router.post("/upload")
async def upload_document(file:UploadFile)->dict:
    saved_file=await save_uploaded_file(file)
    indexed_result=await ingest_document(
        file_path=saved_file["file_path"],
        document_id=saved_file["document_id"]
    )
    return ok(data={
        **saved_file,
        **indexed_result
    })

@router.get("")
async def list_documents()->list[dict]:
    return ok(data=list_uploaded_documents())


@router.post("/rebuild-index")
async def rebuild_documents_index() -> dict:
    return ok(data=await rebuild_index())

@router.delete("/{document_id}")
async def delete_document(document_id:str)->dict:
    raw_deleted=delete_raw_document(document_id)
    chunks_deleted=delete_chunks_by_document_id(document_id)
    vectors_deleted=delete_vectors_by_document_id(document_id)

    return ok({
        "document_id": document_id,
        "raw_deleted": raw_deleted,
        "chunks_deleted": chunks_deleted,
        "vectors_deleted": vectors_deleted,
    })