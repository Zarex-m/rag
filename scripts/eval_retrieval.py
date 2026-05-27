import argparse
import asyncio
import json
from pathlib import Path

from app.rag.hybrid_retriever import hybrid_retrieve, hybrid_retrieve_multi_query
from app.rag.retrievers import build_retriever


def load_eval_cases(path: Path) -> list[dict]:
    cases = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))

    return cases


def compact_text(text: str, max_chars: int = 300) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[:max_chars]}..."


def keyword_hit(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return False
    return any(keyword in text for keyword in keywords)


def keyword_hit_count(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)


def keyword_hit_rate(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 0.0
    return keyword_hit_count(text, keywords) / len(keywords)


def get_source_name(source: str | None) -> str:
    if not source:
        return "unknown"
    return Path(source).name


def source_file_hit(documents, expected_source: str, limit: int | None = None) -> bool:
    if not expected_source:
        return False

    candidates = documents[:limit] if limit else documents

    for document in candidates:
        source = document.metadata.get("source", "")
        filename = get_source_name(source)
        if expected_source in source or expected_source in filename:
            return True

    return False


async def retrieve_documents(
    question: str,
    retrieval_strategy: str,
    top_k: int,
):
    if retrieval_strategy == "hybrid":
        return await hybrid_retrieve(question, top_k=top_k, use_reranker=False)

    if retrieval_strategy == "hybrid_rerank":
        return await hybrid_retrieve(question, top_k=top_k, use_reranker=True)

    if retrieval_strategy == "multi_hybrid_rerank":
        queries = [
            question,
            f"{question} 定义 关系 性质",
            f"{question} 公式 步骤 对比",
        ]

        return await hybrid_retrieve_multi_query(
            queries=queries,
            top_k=top_k,
            use_reranker=True,
            rerank_query=question,
        )

    retriever = build_retriever(top_k=top_k, search_type=retrieval_strategy)
    return await retriever.ainvoke(question)


async def run_eval_case(case: dict, retrieval_strategy: str, top_k: int) -> dict:
    question = case["question"]
    expected_keywords = case.get("expected_keywords", [])
    expected_source = case.get("expected_source", "")

    documents = await retrieve_documents(
        question=question,
        retrieval_strategy=retrieval_strategy,
        top_k=top_k,
    )

    source_text = "\n".join(document.page_content for document in documents)
    retrieved_sources = [
        {
            "rank": index,
            "title": get_source_name(document.metadata.get("source")),
            "source": document.metadata.get("source"),
            "page": document.metadata.get("page"),
            "chunk_id": document.metadata.get("chunk_id"),
            "score": document.metadata.get("reranker_score")
            or document.metadata.get("rrf_score")
            or document.metadata.get("bm25_score"),
            "content": compact_text(document.page_content),
        }
        for index, document in enumerate(documents, start=1)
    ]

    return {
        "question": question,
        "expected_source": expected_source,
        "expected_keywords": expected_keywords,
        "retrieved_count": len(documents),
        "top1_source_file_hit": source_file_hit(documents, expected_source, limit=1),
        "top3_source_file_hit": source_file_hit(documents, expected_source, limit=3),
        "topk_source_file_hit": source_file_hit(documents, expected_source),
        "source_keyword_hit": keyword_hit(source_text, expected_keywords),
        "source_keyword_hit_count": keyword_hit_count(source_text, expected_keywords),
        "source_keyword_hit_rate": keyword_hit_rate(source_text, expected_keywords),
        "retrieved_sources": retrieved_sources,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality without LLM generation.")
    parser.add_argument("--input", default="data/eval/questions.jsonl")
    parser.add_argument("--output", default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--retrieval",
        default="hybrid_rerank",
        choices=[
            "similarity",
            "mmr",
            "hybrid",
            "hybrid_rerank",
            "multi_hybrid_rerank",
        ],
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output or f"data/eval/retrieval_{args.retrieval}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cases = load_eval_cases(input_path)
    results = []

    output_path.write_text("", encoding="utf-8")

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['question']}")
        result = await run_eval_case(
            case=case,
            retrieval_strategy=args.retrieval,
            top_k=args.top_k,
        )
        results.append(result)

        with output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    total = len(results)
    top1_hits = sum(item["top1_source_file_hit"] for item in results)
    top3_hits = sum(item["top3_source_file_hit"] for item in results)
    topk_hits = sum(item["topk_source_file_hit"] for item in results)
    keyword_hits = sum(item["source_keyword_hit"] for item in results)
    avg_keyword_hit_rate = sum(item["source_keyword_hit_rate"] for item in results) / total if total else 0

    print("\nRetrieval Eval Summary")
    print("=" * 40)
    print(f"total: {total}")
    print(f"top1_source_file_hit_rate: {top1_hits / total:.2%}")
    print(f"top3_source_file_hit_rate: {top3_hits / total:.2%}")
    print(f"topk_source_file_hit_rate: {topk_hits / total:.2%}")
    print(f"source_keyword_hit_rate: {keyword_hits / total:.2%}")
    print(f"avg_source_keyword_coverage: {avg_keyword_hit_rate:.2%}")
    print(f"output: {output_path}")
    print(f"retrieval_strategy: {args.retrieval}")


if __name__ == "__main__":
    asyncio.run(main())
