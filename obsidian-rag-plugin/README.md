# RAG 知识库助手 Obsidian 插件

这是一个最小可用的 Obsidian 插件，用于在 Obsidian 内调用本地 FastAPI RAG 后端。

## 本地安装

1. 启动后端服务，默认地址为 `http://localhost:8000`。
2. 将该目录复制到你的 Vault：

```text
<YourVault>/.obsidian/plugins/rag-assistant
```

3. 在 Obsidian 中开启 Community plugins。
4. 启用 `RAG 知识库助手`。
5. 点击左侧图标或通过命令面板打开右侧 RAG 面板。

## 设置

- API 地址：默认 `http://localhost:8000`
- 检索策略：默认 `hybrid_rerank`
- Top K：默认 `5`

## 说明

插件默认后端 `/api/chat` 返回如下结构：

```json
{
  "success": true,
  "data": {
    "answer": "...",
    "sources": [],
    "retrieval": {}
  }
}
```
