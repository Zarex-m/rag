"""Document metadata operations live here."""
from pathlib import Path
from uuid import uuid4
import shutil
from fastapi import UploadFile

RAW_DATA_DIR=Path("data/raw")

async def save_uploaded_file(file:UploadFile)->dict:
    document_id=str(uuid4())
    filename=file.filename or "untitled"
    
    document_dir=RAW_DATA_DIR/document_id
    document_dir.mkdir(parents=True,exist_ok=True)
    
    file_path=document_dir/filename
    content=await file.read()
    file_path.write_bytes(content)
    
    return{
        "document_id":document_id,
        "filename":filename,
        "file_path":str(file_path),
        "status":"uploaded"
    }
    
def list_uploaded_documents()->list[dict]:
    documents=[]
    
    if not RAW_DATA_DIR.exists():
        return documents
    
    for document_dir in RAW_DATA_DIR.iterdir():
        if not document_dir.is_dir():
            continue
        
        files=[file for file in document_dir.iterdir() if file.is_file()]
        if not files:
            continue
        file=files[0]
        
        documents.append({
            "document_id":document_dir.name,
            "filename":file.name,
            "file_path":str(file),
            "status":"uploaded"
        })
    
    return documents

def delete_raw_document(document_id:str)->bool:
    document_dir=RAW_DATA_DIR/document_id
    if not document_dir.exists() or not document_dir.is_dir():
        return False
    
    shutil.rmtree(document_dir)
    return True

def list_raw_document_files()->list[dict]:
    documents=[]
    if not RAW_DATA_DIR.exists():
        return documents
    
    for document_dir in RAW_DATA_DIR.iterdir():
        if not document_dir.is_dir():
            continue
        
        files=[file for file in document_dir.iterdir() if file.is_file()]
        if not files:
            continue
        file=files[0]
        documents.append(
            {
                "document_id":document_dir.name,
                "file_path":str(file),
                "filename":file.name
            }
        )
    return documents