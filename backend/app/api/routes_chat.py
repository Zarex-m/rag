"""Write chat routes here."""
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.chat_service import answer_question
from app.core.responses import ok
router=APIRouter()

class ChatRequest(BaseModel):
    question:str=Field(...,min_length=1)
    top_k:int=Field(default=5,ge=1,le=20)
    retrieval_strategy:Literal[
    "similarity",
    "mmr",
    "hybrid",
    "hybrid_rerank",
] = "hybrid_rerank"
    
@router.post("")
async def chat(request:ChatRequest)->dict:
    result= await answer_question(
        question=request.question,
        top_k=request.top_k,
        retrieval_strategy=request.retrieval_strategy,
    )
    return ok(data=result)
