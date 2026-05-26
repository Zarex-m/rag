import argparse
import asyncio
import json
import time
from pathlib import Path

from app.services.chat_service import answer_question

#从指定路径加载评估用例，文件格式是jsonl，每行一个json对象，包含问题和期望的关键词等信息。
def load_eval_cases(path: Path) -> list[dict]:
    cases = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))

    return cases

#判断文本中是否包含任意一个关键词，如果没有关键词列表，直接返回False。
def keyword_hit(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return False

    return any(keyword in text for keyword in keywords)

def source_file_hit(soources:list[dict],expected_source:str)->bool:
    if not expected_source:
        return False
    
    for source in soources:
        title=source.get("title","")
        file_path=source.get("file_path","")
        if expected_source in title or expected_source in file_path:
            return True
    return False

#评估单个用例
async def run_eval(case: dict, top_k: int, retrieval_strategy: str) -> dict:
    start_time = time.perf_counter()

    result = await answer_question(
        question=case["question"],
        top_k=top_k,
        retrieval_strategy=retrieval_strategy,
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)
    expected_keywords = case.get("expected_keywords", [])
    expected_source=case.get("expected_source", "")
    
    
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    source_text = "\n".join(source.get("content", "") for source in sources)

    return {
        "question": case["question"],
        "query_rewrite": result.get("retrieval", {}).get("query_rewrite"),
        "answer": answer,
        "source_count": len(sources),
        "latency_ms": latency_ms,
        "answer_keyword_hit": keyword_hit(answer, expected_keywords),
        "source_keyword_hit": keyword_hit(source_text, expected_keywords),
        "source_file_hit": source_file_hit(sources, expected_source),
        "expected_keywords": expected_keywords,
        "expected_source": expected_source,
    }

#主函数，读取评估集，逐题评估，写入结果，并打印结果
async def main() -> None:
    # 解析命令行参数，让你不用改代码，也能在命令行里指定输入文件、输出文件和 top_k。
    # 例如，你可以运行：
    # python scripts/eval_rag.py --input data/eval/my_questions.jsonl --output data/eval/my_results.jsonl --top-k 3 
    #这里就会接受到input，output还有top_k的值，分别是data/eval/my_questions.jsonl、data/eval/my_results.jsonl和3。
    parser = argparse.ArgumentParser()
    #评估输入文件路径
    parser.add_argument(
        "--input",
        default="data/eval/questions.jsonl",
    )
    #评估输出文件路径
    parser.add_argument(
        "--output",
        default=None,
    )
    #top_k参数，控制每个问题检索多少相关文档来生成答案，默认是5。
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )
    #检索策略参数，控制使用哪些方法，默认使用hybrid
    parser.add_argument(
    "--retrieval",
    default="hybrid",
    choices=["similarity", "mmr", "hybrid", "hybrid_rerank"]
)
    #解析命令行参数，得到一个args对象，里面就有了input、output和top_k的属性，可以在代码里使用它们。
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output or f"data/eval/results_{args.retrieval}.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    #获取评估用例列表，每个用例是一个字典，包含问题和期望的关键词等信息。
    cases = load_eval_cases(input_path)
    results = []

    output_path.write_text("", encoding="utf-8")
    
    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['question']}")
        result = await run_eval(case, top_k=args.top_k, retrieval_strategy=args.retrieval)
        results.append(result)

        with output_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(result, ensure_ascii=False) + "\n")

    total = len(results)
    answer_hits = sum(1 for item in results if item["answer_keyword_hit"])
    source_hits = sum(1 for item in results if item["source_keyword_hit"])
    source_file_hits=sum(1 for item in results if item["source_file_hit"])
    avg_latency = sum(item["latency_ms"] for item in results) / total if total else 0

    print("\nEval Summary")
    print("=" * 40)
    print(f"total: {total}")
    print(f"answer_keyword_hit_rate: {answer_hits / total:.2%}")
    print(f"source_keyword_hit_rate: {source_hits / total:.2%}")
    print(f"source_file_hit_rate: {source_file_hits / total:.2%}")
    print(f"avg_latency_ms: {avg_latency:.0f}")
    print(f"output: {output_path}")
    print(f"retrieval_strategy: {args.retrieval}")


if __name__ == "__main__":
    asyncio.run(main())
