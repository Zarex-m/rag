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
    latency_ms: int | None = None
    retrieval_time_ms: int | None = None
    top_k: int
    retrieval_strategy: str | None = None
    retrieved_count: int | None = None
    context_count: int | None = None
    neighbor_window: int | None = None
    max_context_documents: int | None = None
    expansion_seed_count: int | None = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    answer: str
    sources: list[SourceChunk]
    retrieval: RetrievalInfo
