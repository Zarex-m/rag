from langchain_core.retrievers import BaseRetriever

from app.rag.vectorstore import build_vectorstore


def build_retriever(top_k: int = 5, search_type: str = "mmr",filter:dict|None=None) -> BaseRetriever:
    vectorstore = build_vectorstore()

    if search_type == "mmr":
        search_kwargs={
                "k": top_k,
                "fetch_k": max(top_k * 4, 20),
                "lambda_mult": 0.7, #更偏向相关性
            }
        if filter:
            search_kwargs["filter"]=filter       
        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs,
        )
    search_kwargs = {
        "k": top_k,
    }
    if filter:
        search_kwargs["filter"] = filter
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )