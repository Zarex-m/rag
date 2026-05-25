import type { ChatResponse, DocumentItem } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function listDocuments(): Promise<DocumentItem[]> {
  return request<DocumentItem[]>("/api/documents");
}

export async function uploadDocument(file: File): Promise<void> {
  const body = new FormData();
  body.append("file", file);

  await request<unknown>("/api/documents/upload", {
    method: "POST",
    body
  });
}

export async function deleteDocument(documentId: string): Promise<void> {
  await request<unknown>(`/api/documents/${documentId}`, {
    method: "DELETE"
  });
}

export async function askQuestion(params: {
  question: string;
  sessionId?: string;
  topK?: number;
}): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      question: params.question,
      session_id: params.sessionId,
      top_k: params.topK ?? 5
    })
  });
}
