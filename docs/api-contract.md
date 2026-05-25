# API Contract

## Health

`GET /api/health`

```json
{
  "status": "ok"
}
```

## Documents

`POST /api/documents/upload`

Form data:

- `file`: PDF, Markdown, TXT, or HTML file.

Response:

```json
{
  "document_id": "string",
  "filename": "example.pdf",
  "status": "processing",
  "message": "Document accepted."
}
```

`GET /api/documents`

```json
[
  {
    "document_id": "string",
    "filename": "example.pdf",
    "status": "indexed",
    "chunk_count": 12
  }
]
```

`DELETE /api/documents/{document_id}`

```json
{
  "document_id": "string",
  "status": "deleted"
}
```

## Chat

`POST /api/chat`

```json
{
  "question": "这份文档的核心结论是什么？",
  "session_id": "optional-session-id",
  "top_k": 5
}
```

Response:

```json
{
  "session_id": "string",
  "message_id": "string",
  "answer": "回答内容",
  "sources": [
    {
      "document_id": "string",
      "title": "example.pdf",
      "page": 1,
      "chunk_id": "chunk-001",
      "content": "命中的原文片段",
      "score": 0.88
    }
  ],
  "retrieval": {
    "query_rewrite": "改写后的查询",
    "latency_ms": 42,
    "top_k": 5
  }
}
```
