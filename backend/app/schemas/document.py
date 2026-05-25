from pydantic import BaseModel


class DocumentCreateResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class DocumentItem(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int = 0
