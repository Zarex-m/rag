from langchain_core.documents import Document
from app.rag.bm25_retriever import build_bm25_retriever
from app.rag.retrievers import build_retriever

#给一个Docuemnt生成唯一标识
def get_document_key(document: Document) -> str:
    chunk_id = document.metadata.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    #兜底逻辑，防止metadata里没有chunk_id，或者chunk_id不是唯一的
    source = document.metadata.get("source", "")
    page = document.metadata.get("page", "")
    chunk_index = document.metadata.get("chunk_index", "")

    return f"{source}:{page}:{chunk_index}"

# RRF 融合算法：Reciprocal Rank Fusion
# 用来把多路检索结果合并成一个最终排序
def rrf_fusion(
    # 多个已经排好序的检索结果列表
    # 例如：[向量检索结果, BM25 检索结果]
    ranked_lists: list[list[Document]],

    # 最终返回多少条结果
    top_k: int = 5,

    # RRF 平滑参数，常用值是 60
    # 值越大，不同排名之间的分差越小
    rrf_k: int = 60,
) -> list[Document]:
    # 保存每个 chunk 的融合分数
    # key 是 chunk 的唯一标识，value 是 RRF 分数
    scores: dict[str, float] = {}

    # 保存 key 对应的 Document
    # 避免同一个 chunk 被多个检索器返回时重复加入结果
    documents_by_key: dict[str, Document] = {}

    # 遍历每一路检索结果
    for ranked_list in ranked_lists:
        # 遍历当前这一路中的每个 document
        # rank 从 1 开始，代表这个 document 在当前检索器里的排名
        for rank, document in enumerate(ranked_list, start=1):
            # 生成 document 的唯一 key
            key = get_document_key(document)

            # RRF 公式：
            # score += 1 / (rrf_k + rank)
            # 排名越靠前，加分越多
            # 如果同一个 chunk 被多路检索命中，会累积分数
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)

            # 第一次见到这个 key 时，把对应 Document 保存下来
            if key not in documents_by_key:
                documents_by_key[key] = document

    # 按融合后的 RRF 分数从高到低排序
    sorted_keys = sorted(
        scores.keys(),
        key=lambda key: scores[key],
        reverse=True,
    )

    # 保存最终结果
    results = []

    # 取融合分数最高的 top_k 个 chunk
    for key in sorted_keys[:top_k]:
        document = documents_by_key[key]

        # 把 RRF 分数写入 metadata，方便调试或前端展示
        document.metadata["rrf_score"] = scores[key]

        results.append(document)

    return results

# 混合检索：向量检索 + BM25 关键词检索 + RRF 融合
async def hybrid_retrieve(query: str, top_k: int = 5) -> list[Document]:
    # 构建向量检索器
    # 这里用 MMR，让语义检索结果尽量兼顾相关性和多样性
    # 先多取一些候选，后面再融合筛选
    vector_retriever = build_retriever(
        top_k=max(top_k * 2, 10),
        search_type="mmr",
    )

    # 异步执行向量检索
    vector_docs = await vector_retriever.ainvoke(query)

    # 构建 BM25 检索器
    # BM25 用于关键词匹配，补充向量检索可能漏掉的精确词
    bm25_retriever = build_bm25_retriever()

    # 执行 BM25 检索
    # 同样先多取一些候选
    bm25_docs = bm25_retriever.retrieve(
        query,
        top_k=max(top_k * 2, 10),
    )

    # 把向量检索结果和 BM25 检索结果用 RRF 融合
    # 最终只返回 top_k 条
    return rrf_fusion(
        ranked_lists=[vector_docs, bm25_docs],
        top_k=top_k,
    )