const {
  ItemView,
  MarkdownRenderer,
  Notice,
  Plugin,
  PluginSettingTab,
  Setting,
  requestUrl,
} = require("obsidian");

const VIEW_TYPE_RAG_ASSISTANT = "rag-assistant-view";

const DEFAULT_SETTINGS = {
  apiBase: "http://localhost:8000",
  retrievalStrategy: "hybrid_rerank",
  topK: 5,
};

const QUICK_PROMPTS = [
  {
    label: "总结当前笔记",
    prompt: "请总结当前打开的笔记，并提炼出 3-5 个关键点。",
  },
  {
    label: "解释选中文本",
    prompt: "请解释我选中的这段内容，并结合知识库补充背景。",
  },
  {
    label: "查找相关笔记",
    prompt: "请根据当前主题，查找知识库中相关的笔记并说明它们的关系。",
  },
  {
    label: "问：FastAPI 依赖注入是什么？",
    prompt: "FastAPI 的依赖注入是什么？请结合我的笔记解释。",
  },
];

module.exports = class RagAssistantPlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());

    this.registerView(
      VIEW_TYPE_RAG_ASSISTANT,
      (leaf) => new RagAssistantView(leaf, this)
    );

    this.addRibbonIcon("message-circle", "RAG 知识库助手", async () => {
      await this.activateView();
    });

    this.addCommand({
      id: "open-rag-assistant",
      name: "打开 RAG 知识库助手",
      callback: async () => {
        await this.activateView();
      },
    });

    this.addCommand({
      id: "ask-rag-with-selection",
      name: "用选中文本向 RAG 提问",
      editorCallback: async (editor) => {
        await this.activateView();
        const selection = editor.getSelection();
        const leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_RAG_ASSISTANT)[0];
        if (leaf && leaf.view && leaf.view.setQuestion) {
          leaf.view.setQuestion(selection || "");
        }
      },
    });

    this.addSettingTab(new RagAssistantSettingTab(this.app, this));
  }

  onunload() {
    this.app.workspace.detachLeavesOfType(VIEW_TYPE_RAG_ASSISTANT);
  }

  async activateView() {
    let leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_RAG_ASSISTANT)[0];

    if (!leaf) {
      leaf = this.app.workspace.getRightLeaf(false);
      await leaf.setViewState({
        type: VIEW_TYPE_RAG_ASSISTANT,
        active: true,
      });
    }

    this.app.workspace.revealLeaf(leaf);
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
};

class RagAssistantView extends ItemView {
  constructor(leaf, plugin) {
    super(leaf);
    this.plugin = plugin;
    this.backendStatus = "unknown";
    this.isLoading = false;
  }

  getViewType() {
    return VIEW_TYPE_RAG_ASSISTANT;
  }

  getDisplayText() {
    return "RAG 知识库助手";
  }

  getIcon() {
    return "message-circle";
  }

  async onOpen() {
    this.render();
    await this.checkBackendStatus();
  }

  setQuestion(question) {
    if (this.inputEl) {
      this.inputEl.value = question;
      this.adjustInputHeight();
      this.updateSubmitState();
      this.inputEl.focus();
    }
  }

  render() {
    const container = this.containerEl.children[1];
    container.empty();
    container.addClass("rag-assistant-root");

    this.renderHeader(container);

    this.messagesEl = container.createDiv({ cls: "rag-messages" });
    this.renderWelcome();

    this.renderComposer(container);
  }

  renderHeader(container) {
    const header = container.createDiv({ cls: "rag-header" });
    const titleRow = header.createDiv({ cls: "rag-header-main" });

    const titleGroup = titleRow.createDiv({ cls: "rag-title-group" });
    titleGroup.createDiv({ cls: "rag-title", text: "RAG 知识库助手" });
    titleGroup.createDiv({
      cls: "rag-subtitle",
      text: "在 Obsidian 中检索你的本地知识库",
    });

    this.refreshButton = titleRow.createEl("button", {
      cls: "rag-icon-button",
      attr: { "aria-label": "刷新后端状态" },
      text: "刷新",
    });
    this.refreshButton.addEventListener("click", async () => {
      await this.checkBackendStatus();
    });

    const toolbar = header.createDiv({ cls: "rag-toolbar" });
    this.statusBadge = toolbar.createSpan({ cls: "rag-badge-pill rag-status-unknown" });
    this.strategyBadge = toolbar.createSpan({
      cls: "rag-badge-pill",
      text: this.plugin.settings.retrievalStrategy,
    });
    this.topKBadge = toolbar.createSpan({
      cls: "rag-badge-pill",
      text: `Top ${this.plugin.settings.topK}`,
    });
    this.updateBackendBadge();
  }

  renderWelcome() {
    const empty = this.messagesEl.createDiv({ cls: "rag-empty" });
    empty.createDiv({ cls: "rag-empty-title", text: "向你的 Obsidian 知识库提问" });
    empty.createDiv({
      cls: "rag-empty-desc",
      text: "我会基于本地 RAG 后端检索笔记、PDF 和 Markdown，并在回答下方展示引用来源。",
    });

    const promptGrid = empty.createDiv({ cls: "rag-quick-prompts" });
    QUICK_PROMPTS.forEach((item) => {
      const button = promptGrid.createEl("button", {
        cls: "rag-quick-prompt",
        text: item.label,
      });
      button.addEventListener("click", () => {
        this.setQuestion(item.prompt);
      });
    });
  }

  renderComposer(container) {
    const composer = container.createDiv({ cls: "rag-composer" });
    this.inputEl = composer.createEl("textarea", {
      cls: "rag-input",
      attr: {
        placeholder: "向你的知识库提问...",
        rows: "1",
      },
    });

    this.inputEl.addEventListener("input", () => {
      this.adjustInputHeight();
      this.updateSubmitState();
    });

    this.inputEl.addEventListener("keydown", async (event) => {
      if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        await this.submitQuestion();
      }
    });

    const actions = composer.createDiv({ cls: "rag-actions" });
    actions.createSpan({
      cls: "rag-hint",
      text: "Cmd/Ctrl + Enter 发送",
    });

    this.submitButton = actions.createEl("button", {
      cls: "rag-submit",
      text: "发送",
    });
    this.submitButton.addEventListener("click", async () => {
      await this.submitQuestion();
    });

    this.adjustInputHeight();
    this.updateSubmitState();
  }

  async checkBackendStatus() {
    this.backendStatus = "unknown";
    this.updateBackendBadge();

    try {
      const apiBase = this.plugin.settings.apiBase.replace(/\/$/, "");
      const response = await requestUrl({
        url: `${apiBase}/api/health`,
        method: "POST",
      });
      if (response.status < 200 || response.status >= 300) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      this.backendStatus = "connected";
    } catch (error) {
      this.backendStatus = "disconnected";
    }

    this.updateBackendBadge();
  }

  updateBackendBadge() {
    if (!this.statusBadge) {
      return;
    }

    this.statusBadge.removeClass("rag-status-connected");
    this.statusBadge.removeClass("rag-status-disconnected");
    this.statusBadge.removeClass("rag-status-unknown");

    if (this.backendStatus === "connected") {
      this.statusBadge.addClass("rag-status-connected");
      this.statusBadge.setText("本地后端已连接");
      return;
    }

    if (this.backendStatus === "disconnected") {
      this.statusBadge.addClass("rag-status-disconnected");
      this.statusBadge.setText("后端未连接");
      return;
    }

    this.statusBadge.addClass("rag-status-unknown");
    this.statusBadge.setText("正在检查后端");
  }

  async submitQuestion() {
    const question = this.inputEl.value.trim();
    if (!question || this.isLoading) {
      return;
    }

    this.inputEl.value = "";
    this.adjustInputHeight();
    this.clearEmptyState();
    this.addMessage("user", question);
    const loadingEl = this.addMessage("assistant", "正在检索知识库...");
    loadingEl.addClass("rag-loading");
    this.setLoading(true);

    try {
      const data = await this.askBackend(question);
      await this.renderAssistantResult(loadingEl, data);
      this.backendStatus = "connected";
      this.updateBackendBadge();
    } catch (error) {
      this.backendStatus = "disconnected";
      this.updateBackendBadge();
      loadingEl.empty();
      loadingEl.removeClass("rag-loading");
      loadingEl.addClass("rag-error-card");
      loadingEl.createDiv({ cls: "rag-error-title", text: "请求失败" });
      loadingEl.createDiv({
        cls: "rag-error-message",
        text: "无法连接本地 RAG 后端，请检查后端地址和服务是否已启动。",
      });
      if (error && error.message) {
        loadingEl.createDiv({ cls: "rag-error-detail", text: error.message });
      }
      new Notice("RAG 请求失败，请检查后端服务。");
    } finally {
      this.setLoading(false);
    }
  }

  async askBackend(question) {
    const apiBase = this.plugin.settings.apiBase.replace(/\/$/, "");
    const response = await requestUrl({
      url: `${apiBase}/api/chat`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        top_k: this.plugin.settings.topK,
        retrieval_strategy: this.plugin.settings.retrievalStrategy,
      }),
    });

    if (response.status < 200 || response.status >= 300) {
      throw new Error(`Request failed: ${response.status}`);
    }

    const payload = response.json;
    if (!payload || payload.success === false) {
      throw new Error(payload && payload.message ? payload.message : "Invalid API response.");
    }

    return payload.data || payload;
  }

  addMessage(role, text) {
    const row = this.messagesEl.createDiv({ cls: `rag-message rag-${role}` });
    row.createDiv({
      cls: "rag-avatar",
      text: role === "user" ? "你" : "AI",
    });
    const bubble = row.createDiv({ cls: "rag-bubble" });
    bubble.setText(text);
    this.scrollMessagesToBottom();
    return bubble;
  }

  async renderAssistantResult(bubble, data) {
    bubble.empty();
    bubble.removeClass("rag-loading");

    const answer = bubble.createDiv({ cls: "rag-answer markdown-rendered" });
    await MarkdownRenderer.render(
      this.app,
      data.answer || "",
      answer,
      this.getActiveSourcePath(),
      this
    );

    this.renderSources(bubble, data.sources || []);
    this.renderRetrievalDetails(bubble, data.retrieval || {});
    this.scrollMessagesToBottom();
  }

  renderSources(parent, sources) {
    if (!sources.length) {
      return;
    }

    const wrapper = parent.createDiv({ cls: "rag-section" });
    wrapper.createDiv({ cls: "rag-section-title", text: `引用来源 (${sources.length})` });

    const visibleSources = sources.slice(0, 3);
    const hiddenSources = sources.slice(3);

    visibleSources.forEach((source, index) => {
      this.renderSourceCard(wrapper, source, index);
    });

    if (hiddenSources.length > 0) {
      const details = wrapper.createEl("details", { cls: "rag-more-sources" });
      details.createEl("summary", { text: `查看其余 ${hiddenSources.length} 条来源` });
      hiddenSources.forEach((source, index) => {
        this.renderSourceCard(details, source, index + visibleSources.length);
      });
    }
  }

  renderSourceCard(parent, source, index) {
    const card = parent.createDiv({ cls: "rag-source-card" });
    const header = card.createDiv({ cls: "rag-source-card-header" });
    const titleBlock = header.createDiv({ cls: "rag-source-title-block" });
    titleBlock.createDiv({
      cls: "rag-source-title",
      text: `${index + 1}. ${this.getSourceDisplayTitle(source)}`,
    });

    titleBlock.createDiv({
      cls: "rag-source-type",
      text: this.formatSourceType(source),
    });

    if (source.source_type === "obsidian" && source.vault_relative_path) {
      const openButton = header.createEl("button", {
        cls: "rag-source-open",
        text: "打开笔记",
      });
      openButton.addEventListener("click", async () => {
        await this.openObsidianSource(source);
      });
    }

    const metaItems = this.buildSourceMeta(source);
    if (metaItems.length > 0) {
      const meta = card.createDiv({ cls: "rag-source-meta-row" });
      metaItems.forEach((item) => {
        meta.createSpan({ cls: "rag-source-meta-chip", text: item });
      });
    }

    if (Array.isArray(source.tags) && source.tags.length > 0) {
      const tags = card.createDiv({ cls: "rag-source-tags" });
      source.tags.forEach((tag) => {
        tags.createSpan({ cls: "rag-tag-chip", text: `#${tag}` });
      });
    }

    const preview = card.createDiv({ cls: "rag-source-preview", text: source.content || "" });
    const details = card.createEl("details", { cls: "rag-source-full" });
    details.createEl("summary", { text: "展开全文" });
    details.createDiv({ cls: "rag-source-full-content", text: source.content || "" });

    if (!source.content || source.content.length < 120) {
      preview.addClass("rag-source-preview-short");
      details.addClass("rag-hidden");
    }
  }

  renderRetrievalDetails(parent, retrieval) {
    const details = parent.createEl("details", { cls: "rag-retrieval-details" });
    details.createEl("summary", { text: "检索详情" });

    const grid = details.createDiv({ cls: "rag-retrieval-grid" });
    this.renderRetrievalItem(grid, "查询改写", retrieval.query_rewrite || "无");
    this.renderRetrievalItem(
      grid,
      "检索策略",
      retrieval.retrieval_strategy || this.plugin.settings.retrievalStrategy
    );
    this.renderRetrievalItem(grid, "检索耗时", `${retrieval.retrieval_time_ms || 0} ms`);
    this.renderRetrievalItem(grid, "召回数量", `${retrieval.retrieved_count || 0}`);
    this.renderRetrievalItem(grid, "上下文数量", `${retrieval.context_count || 0}`);
  }

  renderRetrievalItem(parent, label, value) {
    const item = parent.createDiv({ cls: "rag-retrieval-item" });
    item.createDiv({ cls: "rag-retrieval-label", text: label });
    item.createDiv({ cls: "rag-retrieval-value", text: value });
  }

  formatSourceType(source) {
    if (source.source_type === "obsidian") {
      return "Obsidian 笔记";
    }

    if (source.page !== null && source.page !== undefined) {
      return `PDF / page ${source.page}`;
    }

    return "知识库片段";
  }

  getSourceDisplayTitle(source) {
    const title = source.title || "";

    if (title && !/^未命名(?:\s*\d+)?(?:\.md)?$/i.test(title.trim())) {
      return title;
    }

    const fallback = this.extractReadableTitle(source.content || "");
    if (fallback) {
      return fallback;
    }

    if (source.vault_relative_path) {
      return source.vault_relative_path.split("/").pop();
    }

    return title || "unknown";
  }

  extractReadableTitle(content) {
    const lines = content
      .split(/\r?\n/)
      .map((line) =>
        line
          .replace(/^#+\s*/, "")
          .replace(/^[`>*\-\s]+/, "")
          .replace(/\*\*/g, "")
          .replace(/`/g, "")
          .trim()
      )
      .filter(Boolean);

    if (!lines.length) {
      return "";
    }

    const firstLine = lines[0].replace(/\s+/g, " ");
    return firstLine.length > 34 ? `${firstLine.slice(0, 34)}...` : firstLine;
  }

  async openObsidianSource(source) {
    const candidates = this.buildOpenPathCandidates(source);

    for (const path of candidates) {
      const file = this.app.vault.getAbstractFileByPath(path);
      if (file && file.path && file.path.endsWith(".md") && !file.children) {
        await this.app.workspace.getLeaf(false).openFile(file);
        return;
      }
    }

    if (source.vault_relative_path) {
      await this.app.workspace.openLinkText(source.vault_relative_path, "", false);
      return;
    }

    new Notice("没有找到对应的 Obsidian 笔记。");
  }

  buildOpenPathCandidates(source) {
    const candidates = [];
    const addCandidate = (value) => {
      if (!value) {
        return;
      }
      const normalized = value.replace(/\\/g, "/").replace(/^\/+/, "");
      if (normalized && !candidates.includes(normalized)) {
        candidates.push(normalized);
      }
    };

    addCandidate(source.vault_relative_path);

    const sourcePath = source.source || "";
    const basePath = this.getVaultBasePath();
    if (sourcePath && basePath && sourcePath.startsWith(`${basePath}/`)) {
      addCandidate(sourcePath.slice(basePath.length + 1));
    }

    if (sourcePath) {
      const marker = "/obisidian/";
      const markerIndex = sourcePath.indexOf(marker);
      if (markerIndex >= 0) {
        addCandidate(sourcePath.slice(markerIndex + marker.length));
      }
      addCandidate(sourcePath.split("/").pop());
    }

    return candidates;
  }

  getVaultBasePath() {
    const adapter = this.app.vault.adapter;
    if (adapter && typeof adapter.getBasePath === "function") {
      return adapter.getBasePath().replace(/\\/g, "/").replace(/\/$/, "");
    }
    return "";
  }

  buildSourceMeta(source) {
    const items = [];

    if (source.folder) {
      items.push(source.folder);
    }

    if (source.page !== null && source.page !== undefined) {
      items.push(`page ${source.page}`);
    }

    if (source.score !== null && source.score !== undefined) {
      items.push(`score ${Number(source.score).toFixed(3)}`);
    }

    if (source.chunk_id) {
      items.push(this.shortenChunkId(source.chunk_id));
    }

    return items;
  }

  shortenChunkId(chunkId) {
    const text = String(chunkId);
    const match = text.match(/chunk-\d+$/);
    if (match) {
      return match[0];
    }
    return text.length > 18 ? `${text.slice(0, 15)}...` : text;
  }

  getActiveSourcePath() {
    const file = this.app.workspace.getActiveFile();
    return file ? file.path : "";
  }

  clearEmptyState() {
    const empty = this.messagesEl.querySelector(".rag-empty");
    if (empty) {
      empty.remove();
    }
  }

  setLoading(isLoading) {
    this.isLoading = isLoading;
    this.inputEl.disabled = isLoading;
    this.updateSubmitState();
  }

  updateSubmitState() {
    if (!this.submitButton || !this.inputEl) {
      return;
    }

    this.submitButton.disabled = this.isLoading || !this.inputEl.value.trim();
  }

  adjustInputHeight() {
    if (!this.inputEl) {
      return;
    }

    this.inputEl.style.height = "auto";
    const nextHeight = Math.min(this.inputEl.scrollHeight, 160);
    this.inputEl.style.height = `${nextHeight}px`;
  }

  scrollMessagesToBottom() {
    if (this.messagesEl) {
      this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }
  }
}

class RagAssistantSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "RAG 知识库助手" });

    new Setting(containerEl)
      .setName("API 地址")
      .setDesc("你的 FastAPI 后端地址。")
      .addText((text) =>
        text
          .setPlaceholder("http://localhost:8000")
          .setValue(this.plugin.settings.apiBase)
          .onChange(async (value) => {
            this.plugin.settings.apiBase = value.trim() || DEFAULT_SETTINGS.apiBase;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("检索策略")
      .setDesc("发送给 /api/chat 的检索策略。")
      .addDropdown((dropdown) =>
        dropdown
          .addOption("similarity", "similarity")
          .addOption("mmr", "mmr")
          .addOption("hybrid", "hybrid")
          .addOption("hybrid_rerank", "hybrid_rerank")
          .setValue(this.plugin.settings.retrievalStrategy)
          .onChange(async (value) => {
            this.plugin.settings.retrievalStrategy = value;
            await this.plugin.saveSettings();
          })
      );

    new Setting(containerEl)
      .setName("Top K")
      .setDesc("每次从后端请求的 chunk 数量。")
      .addSlider((slider) =>
        slider
          .setLimits(1, 10, 1)
          .setValue(this.plugin.settings.topK)
          .setDynamicTooltip()
          .onChange(async (value) => {
            this.plugin.settings.topK = value;
            await this.plugin.saveSettings();
          })
      );
  }
}
