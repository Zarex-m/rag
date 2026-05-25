from langchain_core.retrievers import BaseRetriever

from app.rag.vectorstore import build_vectorstore


def build_retriever(top_k: int = 5, search_type: str = "mmr") -> BaseRetriever:
    vectorstore = build_vectorstore()

    if search_type == "mmr":
        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": top_k,
                "fetch_k": max(top_k * 4, 20),
                "lambda_mult": 0.5,
            },
        )

    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": top_k,
        },
    )