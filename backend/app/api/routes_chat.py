"""Write chat routes here."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.chat_service import answer_question

router=APIRouter()

class ChatRequest(BaseModel):
    question:str=Field(...,min_length=1)
    top_k:int=Field(default=5,ge=1,le=20)
    
@router.post("")
async def chat(request:ChatRequest)->dict:
    return await answer_question(
        question=request.question,
        top_k=request.top_k
    )