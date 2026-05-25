import asyncio

from app.rag.hybrid_retriever import hybrid_retrieve


async def main() -> None:
    docs = await hybrid_retrieve("二维随机变量", top_k=5)

    print("retrieved:", len(docs))

    for index, doc in enumerate(docs, start=1):
        print("=" * 40)
        print("rank:", index)
        print("rrf_score:", doc.metadata.get("rrf_score"))
        print("bm25_score:", doc.metadata.get("bm25_score"))
        print("chunk_id:", doc.metadata.get("chunk_id"))
        print(doc.page_content[:300])


if __name__ == "__main__":
    asyncio.run(main())
