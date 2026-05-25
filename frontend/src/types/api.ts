export type DocumentStatus = "uploaded" | "processing" | "indexed" | "failed";

export interface DocumentItem {
  document_id: string;
  filename: string;
  file_path?: string;
  status: DocumentStatus;
  chunk_count?: number;
  num_chunks?: number;
}

export interface SourceChunk {
  document_id?: string | null;
  title?: string;
  source?: string | null;
  page?: number | null;
  chunk_id?: string | null;
  content: string;
  score?: number | null;
}

export interface RetrievalInfo {
  query_rewrite?: string | null;
  latency_ms?: number;
  retrieval_time_ms?: number;
  top_k: number;
}

export interface ChatResponse {
  session_id?: string;
  message_id?: string;
  answer: string;
  sources: SourceChunk[];
  retrieval: RetrievalInfo;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}
