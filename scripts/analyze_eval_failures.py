import json
from pathlib import Path

def load_results(path:Path)->list[dict]:
    """从结果文件中读取评估结果"""
    results=[]
    
    with path.open("r",encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def main():
    path=Path("data/eval/results_hybrid.jsonl")
    
    results=load_results(path)
    
    # 统计失败的案例
    failures=[
        item for item in results
        if not item["answer_keyword hit"]
        or not item["source_keyword hit"]
        or not item["source_file_hit"]
    ]
    
    print(f"总评估案例数: {len(results)}")
    print(f"失败案例数: {len(failures)}")
    

    # 逐个打印失败用例详情
    for index, item in enumerate(failures, start=1):
        # 分隔线，方便阅读
        print("=" * 80)

        # 当前失败用例编号和原始问题
        print(f"[{index}] {item['question']}")

        # 打印 query rewrite 后的问题
        print(f"query_rewrite: {item.get('query_rewrite')}")

        # 打印预期关键词
        print(f"expected_keywords: {item.get('expected_keywords')}")

        # 打印预期来源文件
        print(f"expected_source: {item.get('expected_source')}")

        # 打印答案关键词是否命中
        print(f"answer_hit: {item.get('answer_keyword_hit')}")

        # 打印检索来源内容是否命中关键词
        print(f"source_hit: {item.get('source_keyword_hit')}")

        # 打印检索来源文件是否命中
        print(f"source_file_hit: {item.get('source_file_hit')}")
        

if __name__ == "__main__":
    main()