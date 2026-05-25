import { ArrowUp, FileSearch, Loader2, Plus, Sparkles } from "lucide-react";
import type { ChangeEvent, FormEvent, KeyboardEvent } from "react";
import type { ChatMessage } from "../types/api";

interface ChatPanelProps {
  messages: ChatMessage[];
  question: string;
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;
  onQuestionChange: (value: string) => void;
  onUpload: (file: File) => void;
  onSubmit: () => void;
}

export function ChatPanel({
  messages,
  question,
  isLoading,
  isUploading,
  error,
  onQuestionChange,
  onUpload,
  onSubmit
}: ChatPanelProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onSubmit();
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
      event.target.value = "";
    }
  }

  const hasConversation = messages.length > 1;

  return (
    <main className="chat-panel">
      <header className="topbar">
        <button className="model-pill" type="button">
          <Sparkles size={16} />
          <span>RAG Assistant</span>
        </button>
        <div className="window-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </header>

      <section className={`conversation ${hasConversation ? "has-messages" : ""}`}>
        {!hasConversation ? (
          <div className="welcome-state">
            <h1>准备好了，随时开始</h1>
            <p>上传资料后直接提问，我会基于知识库回答并给出引用来源。</p>
            <div className="prompt-chips">
              <button type="button" onClick={() => onQuestionChange("这份资料的核心内容是什么？")}>
                <FileSearch size={17} />
                <span>总结资料</span>
              </button>
              <button type="button" onClick={() => onQuestionChange("请列出文档中的关键概念。")}>
                <Sparkles size={17} />
                <span>提取要点</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                <div className="message-avatar">{message.role === "user" ? "你" : "AI"}</div>
                <div className="message-bubble">
                  <p>{message.content}</p>
                </div>
              </article>
            ))}
            {isLoading && (
              <article className="message assistant">
                <div className="message-avatar">AI</div>
                <div className="message-bubble loading-bubble">
                  <Loader2 size={16} />
                  <p>正在检索并组织回答...</p>
                </div>
              </article>
            )}
          </div>
        )}
      </section>

      <footer className="composer-zone">
        {error && <div className="error-banner">{error}</div>}
        <form className="composer" onSubmit={handleSubmit}>
          <label className={`composer-tool ${isUploading ? "loading" : ""}`} title="添加资料">
            <Plus size={21} />
            <input accept=".pdf,.txt,.md" type="file" onChange={handleFileChange} />
          </label>
          <textarea
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="有问题，尽管问"
            rows={1}
          />
          <button className="send-button" disabled={isLoading || !question.trim()} type="submit">
            {isLoading ? <Loader2 size={18} /> : <ArrowUp size={18} />}
          </button>
        </form>
      </footer>
    </main>
  );
}
