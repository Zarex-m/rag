"""Write chat service here."""
import time

from app.rag.context_expander import expand_with_neighbors
from app.rag.chains import build_answer_chain,build_rewrite_chain
from app.rag.retrievers import build_retriever
from app.rag.citations import format_context, build_sources
from app.rag.hybrid_retriever import hybrid_retrieve
from app.core.exceptions import AppError
async def answer_question(
    question:str,
    top_k:int=6,
    retrieval_strategy: str = "hybrid_rerank",
    )->dict:
    start_time=time.perf_counter()
    
    #检索前，对问题进行重写
    try:
        rewrite_chain=build_rewrite_chain()
        rewrite_response=await rewrite_chain.ainvoke({"question":question})
        rewrite_question=rewrite_response.content.strip()
    except Exception as e:
        raise AppError(
        code="QUERY_REWRITE_FAILED",
        message="问题改写失败，请检查大模型服务。",
        status_code=502,
    ) from e

    #创建检索器对象，然后调用invoke方法进行检索，得到相关文档列表
    try:
        if retrieval_strategy == "hybrid":
            docs = await hybrid_retrieve(
                rewrite_question,
                top_k=top_k,
                use_reranker=False,
            )
        elif retrieval_strategy == "hybrid_rerank":
            docs = await hybrid_retrieve(
                rewrite_question,
                top_k=top_k,
                use_reranker=True,
            )
        else:
            retriever = build_retriever(top_k=top_k, search_type=retrieval_strategy)
            docs = await retriever.ainvoke(rewrite_question)
    except Exception as e:
        raise AppError(
            code="DOCUMENT_RETRIEVAL_FAILED",
            message="文档检索失败，请检查向量数据库服务。",
            status_code=502,
        ) from e

    if not docs:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        return {
        "answer": "知识库中没有找到与该问题相关的内容。",
        "sources": [],
        "retrieval": {
            "top_k": top_k,
            "retrieval_time_ms": latency_ms,
            "query_rewrite": rewrite_question,
            "retrieval_strategy": retrieval_strategy,
        },
    }
    #拓展chunk
    docs = expand_with_neighbors(
        docs[:2],
        window=1,
        max_documents=8,
    )
    #把检索到的文档列表进行格式化，得到一个字符串形式的上下文
    context=format_context(docs)
    sources=build_sources(docs)
    
    #创建问答链对象，然后调用invoke方法进行问答，得到模型的回答
    try:
        chain=build_answer_chain()
        response=await chain.ainvoke(
        {
            "question":question,
            "context":context
        }
    )
    except Exception as e:
        raise AppError(
            code="ANSWER_GENERATION_FAILED",
            message="答案生成失败，请检查大模型服务。",
            status_code=502,
        ) from e
    
    latency_ms=int((time.perf_counter()-start_time)*1000)
    
    return{
        "answer":response.content,
        "sources":sources,
        "retrieval":{
            "top_k":top_k,
            "retrieval_time_ms":latency_ms,
            "query_rewrite":rewrite_question,
            "retrieval_strategy": retrieval_strategy,
        }
    }
