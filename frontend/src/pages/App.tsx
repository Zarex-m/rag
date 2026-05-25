import { useEffect, useState } from "react";
import { askQuestion, deleteDocument, listDocuments, uploadDocument } from "../api/client";
import { ChatPanel } from "../components/ChatPanel";
import { DocumentPanel } from "../components/DocumentPanel";
import { SourcePanel } from "../components/SourcePanel";
import type { ChatMessage, ChatResponse, DocumentItem } from "../types/api";

export function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "你好，我会基于你的知识库回答问题，并在右侧展示引用来源。"
    }
  ]);
  const [question, setQuestion] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [latestResult, setLatestResult] = useState<ChatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function refreshDocuments() {
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "文档列表加载失败");
    }
  }

  async function handleUpload(file: File) {
    setError(null);
    setIsUploading(true);

    try {
      await uploadDocument(file);
      await refreshDocuments();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "文档上传失败");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDeleteDocument(document: DocumentItem) {
    const confirmed = window.confirm(`确定删除「${document.filename}」吗？`);
    if (!confirmed) {
      return;
    }

    setError(null);
    setDeletingDocumentId(document.document_id);

    try {
      await deleteDocument(document.document_id);
      setDocuments((current) =>
        current.filter((item) => item.document_id !== document.document_id)
      );
      await refreshDocuments();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "文档删除失败");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function handleSubmit() {
    const trimmed = question.trim();
    if (!trimmed || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed
    };

    setMessages((current) => [...current, userMessage]);
    setQuestion("");
    setIsLoading(true);
    setError(null);

    try {
      const result = await askQuestion({ question: trimmed, sessionId });
      setSessionId(result.session_id);
      setLatestResult(result);
      setMessages((current) => [
        ...current,
        {
          id: result.message_id ?? crypto.randomUUID(),
          role: "assistant",
          content: result.answer
        }
      ]);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "问答请求失败";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "这次请求没有成功，请检查后端服务和模型网络连接。"
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <DocumentPanel
        documents={documents}
        deletingDocumentId={deletingDocumentId}
        isUploading={isUploading}
        onDelete={handleDeleteDocument}
        onUpload={handleUpload}
      />
      <ChatPanel
        messages={messages}
        question={question}
        isLoading={isLoading}
        isUploading={isUploading}
        error={error}
        onQuestionChange={setQuestion}
        onUpload={handleUpload}
        onSubmit={handleSubmit}
      />
      <SourcePanel result={latestResult} />
    </div>
  );
}
