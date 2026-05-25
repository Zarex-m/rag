import {
  BookOpen,
  FileText,
  Folder,
  Loader2,
  MessageSquarePlus,
  Trash2,
  Upload
} from "lucide-react";
import type { ChangeEvent } from "react";
import type { DocumentItem } from "../types/api";

interface DocumentPanelProps {
  documents: DocumentItem[];
  deletingDocumentId: string | null;
  isUploading: boolean;
  onDelete: (document: DocumentItem) => void;
  onUpload: (file: File) => void;
}

export function DocumentPanel({
  documents,
  deletingDocumentId,
  isUploading,
  onDelete,
  onUpload
}: DocumentPanelProps) {
  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
      event.target.value = "";
    }
  }

  return (
    <aside className="document-panel">
      <div className="brand-row">
        <div className="brand-mark">R</div>
        <strong>RAG Chat</strong>
      </div>

      <nav className="sidebar-nav" aria-label="主导航">
        <button className="nav-item active" type="button">
          <MessageSquarePlus size={19} />
          <span>新聊天</span>
        </button>
        <label className={`nav-item upload-row ${isUploading ? "loading" : ""}`}>
          <Upload size={19} />
          <span>{isUploading ? "正在入库" : "上传资料"}</span>
          <input accept=".pdf,.txt,.md" type="file" onChange={handleFileChange} />
        </label>
        <button className="nav-item" type="button">
          <BookOpen size={19} />
          <span>知识库</span>
        </button>
      </nav>

      <section className="sidebar-section">
        <div className="section-title">
          <Folder size={16} />
          <span>已上传文档</span>
        </div>
        <div className="document-list">
          {documents.length > 0 ? (
            documents.map((document) => (
              <article className="document-item" key={document.document_id}>
                <FileText size={18} />
                <div className="document-copy">
                  <strong title={document.filename}>{document.filename}</strong>
                  <span>
                    {document.status}
                    {document.chunk_count ?? document.num_chunks
                      ? ` · ${document.chunk_count ?? document.num_chunks} chunks`
                      : ""}
                  </span>
                </div>
                <button
                  className="document-delete"
                  disabled={deletingDocumentId === document.document_id}
                  title="删除文档"
                  type="button"
                  onClick={() => onDelete(document)}
                >
                  {deletingDocumentId === document.document_id ? (
                    <Loader2 size={15} />
                  ) : (
                    <Trash2 size={15} />
                  )}
                </button>
              </article>
            ))
          ) : (
            <p className="sidebar-empty">还没有文档，先上传一份 PDF 或 TXT。</p>
          )}
        </div>
      </section>

      <div className="sidebar-user">
        <div className="avatar">ZA</div>
        <div>
          <strong>RAG 项目</strong>
          <span>Portfolio Demo</span>
        </div>
      </div>
    </aside>
  );
}
