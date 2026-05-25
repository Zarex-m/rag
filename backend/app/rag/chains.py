from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.rag.prompts import RAG_PROMPT, REWRITE_PROMPT


def build_chat_model()->ChatOpenAI:
    api_key = settings.deepseek_api_key or settings.deep_seek_api_key
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is required")

    return ChatOpenAI(
        model=settings.chat_model,
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=0,
    )


def build_answer_chain():
    chat_model=build_chat_model()
    return RAG_PROMPT | chat_model

def build_rewrite_chain():
    chat_model=build_chat_model()
    return REWRITE_PROMPT | chat_model