from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    retrieval_strategy: str = Field(default="hybrid")


class SourceChunk(BaseModel):
    document_id: str
    title: str
    page: int | None = None
    chunk_id: str
    content: str
    score: float | None = None


class RetrievalInfo(BaseModel):
    query_rewrite: str | None = None
    latency_ms: int
    top_k: int


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    sources: list[SourceChunk]
    retrieval: RetrievalInfo
