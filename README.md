# RAG Knowledge Base Assistant

这是一个基于 FastAPI、LangChain、Chroma、智谱 Embedding 和 DeepSeek 的知识库问答系统。项目支持文档入库、自动切分、向量检索、RAG 问答、引用溯源和轻量评估。

## 项目背景

本项目用于模拟企业知识库问答场景。用户可以上传 PDF / TXT / Markdown 文件，系统会自动完成文本解析、文本切分和向量化入库。用户提问时，系统会通过 Query Rewrite 和 Hybrid Retrieval 召回相关片段，再调用大模型生成基于上下文的回答，并返回引用来源。

## 技术栈

- Backend: FastAPI
- RAG Framework: LangChain
- Embedding: 智谱 embedding-3
- LLM: DeepSeek Chat
- Vector Store: Chroma
- Retrieval: Query Rewrite, MMR, BM25, RRF
- Frontend: React + Vite + TypeScript
- Evaluation: 自定义轻量 RAG Eval

## 核心功能

TODO: 简要列出当前已经实现的功能，例如文档上传、删除、重建索引、RAG 问答、引用溯源、Hybrid Retrieval、Eval。

## 系统架构

TODO: 可以放一张架构图，或者用 Mermaid 描述前端、后端、向量库和模型服务之间的关系。

## RAG 流程

### 1. 文档入库流程

TODO: 说明上传文件后，如何经过 loader、splitter、embedding，最后写入 Chroma 和 chunks.jsonl。

### 2. 检索流程

TODO: 说明 Query Rewrite、MMR 向量检索、BM25 关键词检索和 RRF 融合。

### 3. 生成流程

TODO: 说明如何将检索结果组织为 context，再调用 DeepSeek 生成答案，并返回 sources。

## 检索策略演进

TODO: 说明项目从 similarity search 到 MMR，再到 Hybrid Retrieval 的演进路线，以及每一步解决的问题。

## API 接口

### Health Check

TODO: 写 `GET/POST /api/health` 的说明，以你的实际接口为准。

### Upload Document

TODO: 写 `POST /api/documents/upload` 的请求和响应说明。

### List Documents

TODO: 写 `GET /api/documents` 的说明。

### Delete Document

TODO: 写 `DELETE /api/documents/{document_id}` 的说明。

### Rebuild Index

TODO: 写 `POST /api/documents/rebuild-index` 的说明。

### Chat

TODO: 写 `POST /api/chat` 的请求和响应示例。

## 统一响应与异常处理

TODO: 说明统一 API 返回结构，例如 success、code、message、data，以及全局异常处理的意义。

## 轻量评估

TODO: 说明 `scripts/eval_rag.py` 如何运行，评估哪些指标，以及 MMR / Hybrid Retrieval 如何对比。

## 快速启动

### 后端启动

TODO: 写虚拟环境、安装依赖、配置 `.env`、启动 FastAPI 的命令。

### 前端启动

TODO: 写进入 frontend、安装依赖、启动 Vite 的命令。

## 环境变量

TODO: 列出 `.env.example` 中需要配置的 key，比如 ZHIPU_API_KEY、DEEP_SEEK_API_KEY、CHAT_MODEL。

## 项目结构

TODO: 简要说明 backend、frontend、scripts、data、docs 等目录的作用。

## 当前效果

TODO: 可以放前端截图、Swagger 截图或 Eval 结果。

## 项目亮点

TODO: 总结 4-6 条最适合简历展示的亮点。

## 后续优化

TODO: 写未来可以继续做的方向，例如 reranker、更多文档类型、pgvector、多轮对话、RAGAS / LangSmith。
