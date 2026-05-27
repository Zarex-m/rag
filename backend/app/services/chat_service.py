"""Write chat service here."""
import time

from app.rag.context_expander import expand_with_neighbors
from app.rag.chains import build_answer_chain,build_rewrite_chain
from app.rag.retrievers import build_retriever
from app.rag.citations import format_context, build_sources
from app.rag.hybrid_retriever import hybrid_retrieve
from app.rag.confidence import build_confidence
from app.core.exceptions import AppError
from app.rag.chains import build_multi_query_chain
from app.rag.hybrid_retriever import hybrid_retrieve_multi_query

async def answer_question(
    question:str,
    top_k:int=6,
    retrieval_strategy: str = "hybrid_rerank",
    metadata_filter: dict | None = None,
    )->dict:
    start_time=time.perf_counter()
    neighbor_window = 1
    max_context_documents = 8
    expansion_seed_count = 2
    
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
        
    multi_queries=[rewrite_question]
    try:
        multi_query_chain=build_multi_query_chain()
        multi_query_response=await multi_query_chain.ainvoke({"question":question})
       
        generated_queries = [
            line.strip(" -0123456789.、")
            for line in multi_query_response.content.splitlines()
            if line.strip()
        ]
        
        for query in generated_queries:
            if query and query not in multi_queries:
                multi_queries.append(query)
        multi_queries=multi_queries[:4]
    except Exception:
        multi_queries=multi_queries[:1]

    #创建检索器对象，然后调用invoke方法进行检索，得到相关文档列表
    try:
        if retrieval_strategy == "hybrid":
            docs = await hybrid_retrieve(
                rewrite_question,
                top_k=top_k,
                use_reranker=False,
                bm25_query=f"{question} {rewrite_question}",
                filter=metadata_filter
            )
        elif retrieval_strategy == "hybrid_rerank":
            docs = await hybrid_retrieve(
                rewrite_question,
                top_k=top_k,
                use_reranker=True,
                bm25_query=f"{question} {rewrite_question}",
                filter=metadata_filter
            )
        elif retrieval_strategy == "multi_hybrid_rerank":
            docs = await hybrid_retrieve_multi_query(
                queries=multi_queries,
                top_k=top_k,
                use_reranker=True,
                rerank_query=question,
                filter=metadata_filter
            )
        else:
            retriever = build_retriever(top_k=top_k, search_type=retrieval_strategy, filter=metadata_filter)
            docs = await retriever.ainvoke(rewrite_question)
    except Exception as e:
        raise AppError(
            code="DOCUMENT_RETRIEVAL_FAILED",
            message="文档检索失败，请检查向量数据库服务。",
            status_code=502,
        ) from e

    if not docs:
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        confidence = build_confidence(question=question, documents=[], top_k=top_k)
        return {
        "answer": "知识库中没有找到与该问题相关的内容。",
        "sources": [],
        "retrieval": {
            "top_k": top_k,
            "retrieval_time_ms": latency_ms,
            "query_rewrite": rewrite_question,
            "retrieval_strategy": retrieval_strategy,
            "retrieved_count": 0,
            "context_count": 0,
            "neighbor_window": neighbor_window,
            "max_context_documents": max_context_documents,
            "expansion_seed_count": expansion_seed_count,
            "metadata_filter": metadata_filter,
            "confidence": confidence,
        },
    }
    retrieved_count = len(docs)
    confidence = build_confidence(question=question, documents=docs, top_k=top_k)
    #拓展chunk
    docs = expand_with_neighbors(
        docs[:expansion_seed_count],
        window=neighbor_window,
        max_documents=max_context_documents,
    )
    context_count = len(docs)
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
            "retrieved_count": retrieved_count,
            "context_count": context_count,
            "neighbor_window": neighbor_window,
            "max_context_documents": max_context_documents,
            "expansion_seed_count": expansion_seed_count,
            "multi_queries": multi_queries,
            "metadata_filter": metadata_filter,
            "confidence": confidence,
        }
    }
