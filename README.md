# Rag Knowledge Base Assistant
`这是一个基于fastapi，chorma，智谱embedding和deepseek的知识库问答系统。支持文档入库，自动切分上传，Rag问答，引用溯源和轻量评估`

# 项目背景
`本项目用于模拟企业知识库问答场景。用户可以上传PDF/TXT/Markdown文件，系统会自动完成文本解析，文本切分，向量化入库。用户提问时，系统会通过Query Rewrite和MMR检索找回相关片段，再调用大模型生成基于上下文的回答，并返回引用来源`

# 技术栈

- Backend: Fastapi
- Rag Framework: Langchain
- Embedding: 智谱embedding-3
- LLM: deepseek-chat
- Vector Store: Chroma
- Evaluation:自定义轻量RAG EVAL
