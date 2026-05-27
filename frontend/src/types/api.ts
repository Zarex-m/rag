export type DocumentStatus = "uploaded" | "processing" | "indexed" | "failed";
export type RetrievalStrategy =
  | "similarity"
  | "mmr"
  | "hybrid"
  | "hybrid_rerank"
  | "multi_hybrid_rerank";

export interface ConfidenceInfo {
  score: number;
  level: "high" | "medium" | "low";
  reason: string;
  signals?: Record<string, number | string | null>;
}

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
  retrieval_strategy?: RetrievalStrategy;
  retrieved_count?: number;
  context_count?: number;
  neighbor_window?: number;
  max_context_documents?: number;
  expansion_seed_count?: number;
  metadata_filter?: Record<string, unknown> | null;
  confidence?: ConfidenceInfo | null;
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
