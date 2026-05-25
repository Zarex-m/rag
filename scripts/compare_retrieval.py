import argparse

from app.rag.retrievers import build_retriever


def compact_text(text: str, max_chars: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[:max_chars]}..."


def print_results(title: str, question: str, top_k: int, max_chars: int) -> None:
    retriever = build_retriever(top_k=top_k, search_type=title)
    documents = retriever.invoke(question)

    print(f"\n{title.upper()} RESULTS")
    print("=" * 80)

    if not documents:
        print("No documents retrieved.")
        return

    for index, document in enumerate(documents, start=1):
        print(f"\n[{index}]")
        print(compact_text(document.page_content, max_chars))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare similarity and MMR retrieval results.")
    parser.add_argument("question", help="Question to retrieve against the vector store.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of chunks to return.")
    parser.add_argument("--max-chars", type=int, default=500, help="Max characters shown per chunk.")
    args = parser.parse_args()

    print(f"QUESTION: {args.question}")
    print_results("similarity", args.question, args.top_k, args.max_chars)
    print_results("mmr", args.question, args.top_k, args.max_chars)


if __name__ == "__main__":
    main()
