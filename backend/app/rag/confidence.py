import math
from collections import Counter

import jieba
from langchain_core.documents import Document


# 停用词：这些词在问题中很常见，但对判断主题帮助不大
# 提取关键词时会过滤掉
STOPWORDS = {
    "什么",
    "怎么",
    "如何",
    "为什么",
    "是不是",
    "能不能",
    "哪些",
    "一个",
    "这个",
    "那个",
    "之间",
    "进行",
    "应该",
    "可以",
}


def _sigmoid(value: float) -> float:
    # 避免 exp 数值溢出
    if value >= 30:
        return 1.0
    if value <= -30:
        return 0.0

    # 将任意范围的分数压缩到 0~1
    # 常用于归一化 reranker 原始分数
    return 1.0 / (1.0 + math.exp(-value))


def _extract_terms(text: str) -> set[str]:
    # 用来保存提取出来的关键词
    terms = set()

    # 使用 jieba 对中文文本进行分词
    for token in jieba.lcut(text):
        token = token.strip()

        # 跳过空 token 和停用词
        if not token or token in STOPWORDS:
            continue

        # 保留长度 >= 2 的中文词，或者 ASCII token
        # 这样可以保留 AI、RAG、PDF、X 等英文/符号变量
        if len(token) >= 2 or token.isascii():
            terms.add(token)

    return terms


def _keyword_coverage(question: str, documents: list[Document]) -> float:
    # 提取用户问题中的关键词
    query_terms = _extract_terms(question)

    # 如果问题里提取不到关键词，返回中性值 0.5
    if not query_terms:
        return 0.5

    # 只取前 5 个检索结果的内容来计算关键词覆盖
    # 因为排序靠前的文档对回答更重要
    context_terms = _extract_terms("\n".join(doc.page_content for doc in documents[:5]))

    # 如果检索内容里没有有效词，说明上下文质量很差
    if not context_terms:
        return 0.0

    # 计算问题关键词和上下文关键词的交集
    matched_terms = query_terms & context_terms

    # 返回问题关键词被上下文覆盖的比例
    return len(matched_terms) / len(query_terms)


def _get_top_score(documents: list[Document]) -> tuple[float | None, float | None, str | None]:
    # 如果没有文档，就没有分数
    if not documents:
        return None, None, None

    # 取排名第一的文档
    top_doc = documents[0]

    # 优先使用 reranker 分数
    # reranker_score 通常最能反映 query 和 chunk 的相关性
    if top_doc.metadata.get("reranker_score") is not None:
        raw_score = float(top_doc.metadata["reranker_score"])

        # reranker 原始分数不一定在 0~1，所以用 sigmoid 归一化
        return raw_score, _sigmoid(raw_score), "reranker_score"

    # 如果没有 reranker 分数，就使用 RRF 融合分数
    if top_doc.metadata.get("rrf_score") is not None:
        raw_score = float(top_doc.metadata["rrf_score"])

        # RRF 分数通常较小，这里乘以 60 做一个近似归一化，并限制最大为 1
        return raw_score, min(raw_score * 60, 1.0), "rrf_score"

    # 如果没有 RRF 分数，就使用 BM25 分数
    if top_doc.metadata.get("bm25_score") is not None:
        raw_score = float(top_doc.metadata["bm25_score"])

        # BM25 分数没有固定上限，这里用 /10 做简单归一化，并限制最大为 1
        return raw_score, min(raw_score / 10, 1.0), "bm25_score"

    # 如果没有任何检索分数，就返回中性置信度 0.5
    return None, 0.5, None


def _source_concentration(documents: list[Document]) -> float:
    # 提取所有有 source 的文档来源
    sources = [doc.metadata.get("source") for doc in documents if doc.metadata.get("source")]

    # 如果没有来源信息，返回 0
    if not sources:
        return 0.0

    # 统计每个 source 出现的次数
    counts = Counter(sources)

    # 计算出现次数最多的 source 占全部 source 的比例
    # 比如 5 个结果里 3 个来自同一个文件，则为 3/5 = 0.6
    return counts.most_common(1)[0][1] / len(sources)


def build_confidence(
    question: str,
    documents: list[Document],
    top_k: int,
) -> dict:
    # 如果没有检索到文档，直接返回低置信度
    if not documents:
        return {
            "score": 0.0,
            "level": "low",
            "reason": "没有检索到相关文档，不能形成可靠回答。",
            "signals": {
                "retrieved_count": 0,
                "top_score": None,
                "normalized_top_score": 0.0,
                "score_type": None,
                "keyword_coverage": 0.0,
                "evidence_coverage": 0.0,
                "source_concentration": 0.0,
            },
        }

    # 获取排名第一的检索结果分数，并做归一化
    raw_score, normalized_top_score, score_type = _get_top_score(documents)

    # 计算问题关键词在检索上下文中的覆盖率
    keyword_coverage = _keyword_coverage(question, documents)

    # 计算证据数量覆盖率
    # 如果返回数量达到 top_k，则为 1；否则按比例降低
    evidence_coverage = min(len(documents) / max(top_k, 1), 1.0)

    # 计算检索来源集中度
    source_concentration = _source_concentration(documents)

    # 如果来源过于分散，说明检索结果可能不够稳定
    # 但也不直接打到 0，而是给一个中性支持值 0.5
    source_support = source_concentration if source_concentration >= 0.5 else 0.5

    # 综合计算置信度分数
    # 权重含义：
    # 45% 看排名第一的检索分数
    # 30% 看关键词覆盖
    # 15% 看证据数量是否足够
    # 10% 看来源是否集中
    score = (
        0.45 * (normalized_top_score or 0.5)
        + 0.30 * keyword_coverage
        + 0.15 * evidence_coverage
        + 0.10 * source_support
    )

    # 限制 score 在 0~1 之间，并保留 4 位小数
    score = round(max(0.0, min(score, 1.0)), 4)

    # 根据分数划分置信度等级
    if score >= 0.72:
        level = "high"
        reason = "检索结果与问题匹配度较高，可以作为较可靠依据。"
    elif score >= 0.45:
        level = "medium"
        reason = "检索结果具备一定相关性，建议结合引用来源确认。"
    else:
        level = "low"
        reason = "检索结果相关性偏低，当前回答可能不可靠。"

    # 保护逻辑：
    # 如果问题关键词覆盖率很低，即使综合分数较高，也不要直接给 high
    if keyword_coverage < 0.2 and level == "high":
        level = "medium"
        reason = "排序分数较高，但问题关键词覆盖不足，建议结合来源确认。"

    # 返回置信度结果和各项信号，方便前端展示或后续调试
    return {
        "score": score,
        "level": level,
        "reason": reason,
        "signals": {
            "retrieved_count": len(documents),
            "top_score": raw_score,
            "normalized_top_score": round(normalized_top_score or 0.0, 4),
            "score_type": score_type,
            "keyword_coverage": round(keyword_coverage, 4),
            "evidence_coverage": round(evidence_coverage, 4),
            "source_concentration": round(source_concentration, 4),
        },
    }