import asyncio
from pathlib import Path

import streamlit as st
from langchain_core.documents import Document

from app.rag.context_expander import expand_with_neighbors
from app.rag.hybrid_retriever import hybrid_retrieve
from app.rag.retrievers import build_retriever


STRATEGIES = {
    "similarity": "向量相似度",
    "mmr": "MMR",
    "hybrid": "Hybrid",
    "hybrid_rerank": "Hybrid + Rerank",
}


def compact_text(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[:max_chars]}..."


def get_score(document: Document) -> float | None:
    score = (
        document.metadata.get("reranker_score")
        or document.metadata.get("rrf_score")
        or document.metadata.get("bm25_score")
    )
    if score is None:
        return None
    return float(score)


async def retrieve_documents(
    query: str,
    strategy: str,
    top_k: int,
) -> list[Document]:
    if strategy == "hybrid":
        return await hybrid_retrieve(query, top_k=top_k, use_reranker=False)

    if strategy == "hybrid_rerank":
        return await hybrid_retrieve(query, top_k=top_k, use_reranker=True)

    retriever = build_retriever(top_k=top_k, search_type=strategy)
    return await retriever.ainvoke(query)


def render_document(document: Document, index: int, max_chars: int) -> None:
    source = document.metadata.get("source")
    title = Path(source).name if source else document.metadata.get("filename", "unknown")
    page = document.metadata.get("page")
    chunk_id = document.metadata.get("chunk_id", "unknown")
    chunk_index = document.metadata.get("chunk_index")
    score = get_score(document)

    with st.container(border=True):
        cols = st.columns([0.12, 0.88])
        with cols[0]:
            st.metric("Rank", index)
        with cols[1]:
            st.markdown(f"**{title}**")
            meta = [
                f"page {int(page) + 1}" if page is not None else "page unknown",
                f"chunk_index {chunk_index}" if chunk_index is not None else None,
                str(chunk_id),
            ]
            if score is not None:
                meta.append(f"score {score:.4f}")
            st.caption(" · ".join(item for item in meta if item))

        st.write(compact_text(document.page_content, max_chars))


def main() -> None:
    st.set_page_config(
        page_title="RAG Retrieval Lab",
        page_icon="🔎",
        layout="wide",
    )

    st.title("RAG Retrieval Lab")
    st.caption("输入同一个问题，对比不同检索策略召回的 chunk。")

    with st.sidebar:
        st.header("实验参数")
        top_k = st.slider("Top K", min_value=1, max_value=10, value=3)
        max_chars = st.slider("每个 chunk 展示字符数", min_value=150, max_value=1000, value=450, step=50)
        use_expansion = st.checkbox("展示相邻 chunk 扩展结果", value=False)
        neighbor_window = st.slider("扩展窗口", min_value=1, max_value=2, value=1)
        max_context_documents = st.slider("最大上下文 chunk 数", min_value=3, max_value=12, value=6)

    query = st.text_input(
        "问题",
        value="随机变量的分布函数有哪些性质？",
        placeholder="输入一个用于检索对比的问题",
    )

    selected_strategies = st.multiselect(
        "检索策略",
        options=list(STRATEGIES.keys()),
        default=["similarity", "mmr", "hybrid", "hybrid_rerank"],
        format_func=lambda value: STRATEGIES[value],
    )

    if not query.strip():
        st.info("请输入问题后开始对比。")
        return

    if not selected_strategies:
        st.info("至少选择一个检索策略。")
        return

    if st.button("开始对比", type="primary"):
        query = query.strip()
        columns = st.columns(len(selected_strategies))

        for column, strategy in zip(columns, selected_strategies):
            with column:
                st.subheader(STRATEGIES[strategy])

                with st.spinner("检索中..."):
                    try:
                        documents = asyncio.run(retrieve_documents(query, strategy, top_k))
                    except Exception as exc:
                        st.error(f"检索失败：{exc}")
                        continue

                st.caption(f"原始召回：{len(documents)} 个 chunk")

                if use_expansion:
                    expanded_documents = expand_with_neighbors(
                        documents[:2],
                        window=neighbor_window,
                        max_documents=max_context_documents,
                    )
                    st.caption(f"扩展后上下文：{len(expanded_documents)} 个 chunk")
                    documents = expanded_documents

                if not documents:
                    st.warning("没有召回结果。")
                    continue

                for index, document in enumerate(documents, start=1):
                    render_document(document, index, max_chars)


if __name__ == "__main__":
    main()
