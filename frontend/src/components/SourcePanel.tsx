import { ChevronRight, FileText, Search } from "lucide-react";
import type { ChatResponse } from "../types/api";

interface SourcePanelProps {
  result: ChatResponse | null;
}

export function SourcePanel({ result }: SourcePanelProps) {
  const latency = result?.retrieval.latency_ms ?? result?.retrieval.retrieval_time_ms;

  return (
    <aside className="source-panel">
      <div className="source-header">
        <div>
          <h2>引用来源</h2>
          <p>检索命中的上下文片段</p>
        </div>
        <Search size={19} />
      </div>

      {result ? (
        <>
          <div className="retrieval-box">
            <div>
              <span>Top K</span>
              <strong>{result.retrieval.top_k}</strong>
            </div>
            <div>
              <span>耗时</span>
              <strong>{latency ? `${latency} ms` : "-"}</strong>
            </div>
          </div>

          <div className="source-list">
            {result.sources.map((source, index) => (
              <article className="source-item" key={source.chunk_id ?? `${source.source}-${index}`}>
                <div className="source-title">
                  <FileText size={16} />
                  <strong>{source.title ?? source.source?.split("/").pop() ?? "未知资料"}</strong>
                  {source.score !== null && source.score !== undefined && (
                    <span>{source.score.toFixed(2)}</span>
                  )}
                </div>
                <p>{source.content}</p>
                <small>
                  <ChevronRight size={13} />
                  {source.page !== null && source.page !== undefined
                    ? `page ${Number(source.page) + 1}`
                    : "page unknown"}
                  {source.chunk_id ? ` · ${source.chunk_id}` : ""}
                </small>
              </article>
            ))}
          </div>
        </>
      ) : (
        <div className="source-empty">
          <Search size={22} />
          <p>提问后这里会显示引用片段、页码和 chunk 信息。</p>
        </div>
      )}
    </aside>
  );
}
