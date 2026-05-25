# Backend Roadmap

## Phase 1: Write the First Route

Goal: understand FastAPI routing by writing the smallest route yourself.

1. Create a virtual environment.
2. Install dependencies with `pip install -r requirements-dev.txt`.
3. Run `uvicorn app.main:app --reload --app-dir backend`.
4. Add a health router in `backend/app/api/routes_health.py`.
5. Register it in `backend/app/main.py`.
6. Open `/docs` and test your endpoint.

## Phase 2: Document Upload

Implement `backend/app/api/routes_documents.py`.

What to add:

- Generate a real `document_id`.
- Save uploaded files into `data/raw/{document_id}/`.
- Record metadata in SQLite.
- Return `processing`, `indexed`, or `failed`.

Start here:

- `backend/app/services/document_service.py`
- `backend/app/services/ingest_service.py`
- `backend/app/db/models.py`

## Phase 3: Ingestion Pipeline

Implement:

- `backend/app/rag/loaders.py`
- `backend/app/rag/splitters.py`
- `backend/app/rag/embeddings.py`
- `backend/app/rag/vectorstore.py`

Recommended first version:

1. Load PDF with `PyPDFLoader`.
2. Split with `RecursiveCharacterTextSplitter`.
3. Add metadata: `document_id`, `source`, `page`, `chunk_id`.
4. Store chunks in Chroma.

## Phase 4: Real Chat

The request path should become:

```text
question -> retriever -> context builder -> prompt -> LLM -> answer + sources
```

Start with `backend/app/services/chat_service.py`, then improve:

- return source chunks
- return scores
- handle empty retrieval results
- add conversation history

## Phase 5: Upgrade Retrieval

After the basic version works, add:

- query rewrite
- multi-query retrieval
- BM25 keyword search
- vector + keyword fusion
- reranker
- LangGraph workflow in `backend/app/rag/graph.py`

## Phase 6: Evaluation

Create a small eval set with 20-50 questions.

Track:

- retrieval hit rate
- answer faithfulness
- citation accuracy
- latency
- failure cases
