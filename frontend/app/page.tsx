"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type Role = "user" | "assistant" | "system";

type Message = {
  role: Role;
  content: string;
};

type Stats = {
  target_name?: string;
  message_count?: number;
  target_message_count?: number;
  example_count?: number;
  source_files?: string[];
  errors?: string[];
};

type ChatResponse = {
  reply: string;
  retrieved_examples: Array<{ input: string; output: string; score?: number }>;
  persona_ready: boolean;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  const [stats, setStats] = useState<Stats>({});
  const [messages, setMessages] = useState<Message[]>([
    { role: "system", content: "先点击重新构建，系统会从 ./聊天记录/ 读取数据并生成本地 persona。" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [rebuilding, setRebuilding] = useState(false);
  const [error, setError] = useState("");
  const [lastExamples, setLastExamples] = useState<ChatResponse["retrieved_examples"]>([]);

  const personaReady = Boolean(stats.message_count && stats.example_count);
  const statusLabel = personaReady ? "Persona ready" : "Needs rebuild";

  async function loadStats() {
    const response = await fetch(`${apiBase}/stats`);
    if (!response.ok) throw new Error(await response.text());
    const data = await response.json();
    setStats(data);
  }

  async function refreshStats() {
    setError("");
    try {
      await loadStats();
    } catch {
      setError("无法连接后端，请确认 FastAPI 已启动在 http://localhost:8000。");
    }
  }

  useEffect(() => {
    refreshStats();
  }, []);

  async function rebuild() {
    setRebuilding(true);
    setError("");
    setMessages((items) => [...items, { role: "system", content: "正在重新构建本地数据，请稍等……" }]);
    try {
      const response = await fetch(`${apiBase}/rebuild`, { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setStats(data.stats);
      setMessages((items) => [...items, { role: "system", content: `已完成构建：${data.stats.message_count} 条消息，${data.stats.example_count} 个样例。` }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "重新构建失败";
      setError(message.includes("Failed to fetch") ? `无法连接后端：${apiBase}` : message);
      setMessages((items) => [...items, { role: "system", content: "重新构建失败，请检查后端窗口日志和浏览器错误提示。" }]);
    } finally {
      setRebuilding(false);
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const content = input.trim();
    if (!content || loading) return;
    setInput("");
    setLoading(true);
    setError("");
    const nextMessages = [...messages, { role: "user" as const, content }];
    setMessages(nextMessages);
    try {
      const context = nextMessages.slice(-6).map((item) => `${item.role}: ${item.content}`);
      const response = await fetch(`${apiBase}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, context, top_k: 5 })
      });
      if (!response.ok) throw new Error(await response.text());
      const data: ChatResponse = await response.json();
      setMessages((items) => [...items, { role: "assistant", content: data.reply }]);
      setLastExamples(data.retrieved_examples || []);
      loadStats().catch(() => undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "发送失败");
      setMessages((items) => [...items, { role: "system", content: "请求失败，请检查后端和 API 配置。" }]);
    } finally {
      setLoading(false);
    }
  }

  const sourceFiles = useMemo(() => (stats.source_files || []).join("、") || "尚未读取", [stats.source_files]);

  return (
    <main className="page">
      <div className="shell hero">
        <section className="panel">
          <div className="brand"><span className="mark" /> Digital Persona</div>
          <h1>Local-first AI persona studio.</h1>
          <p className="lead">
            从本地聊天记录中清洗消息、提取语言习惯、构建风格样例，并通过 OpenAI-compatible API 生成接近目标人物语气的回复。
          </p>
          <div className="actions">
            <button className="primary" onClick={rebuild} disabled={rebuilding}>
              {rebuilding ? "构建中…" : "重新构建数据"}
            </button>
            <button className="secondary" onClick={refreshStats}>
              刷新状态
            </button>
          </div>
          {error && <div className="error">{error}</div>}
          <div className="status-grid">
            <div className="status-card"><span>目标人物</span><strong>{stats.target_name || "未配置"}</strong></div>
            <div className="status-card"><span>消息 / 样例</span><strong>{stats.message_count || 0} / {stats.example_count || 0}</strong></div>
            <div className="status-card"><span>目标发言</span><strong>{stats.target_message_count || 0}</strong></div>
            <div className="status-card"><span>来源文件</span><strong>{sourceFiles}</strong></div>
          </div>
          {Boolean(stats.errors?.length) && <div className="examples">解析提示：{stats.errors?.join("；")}</div>}
          {lastExamples.length > 0 && (
            <div className="examples">
              <strong>最近检索样例</strong>
              {lastExamples.slice(0, 3).map((item, index) => (
                <div key={index}>「{item.input}」→「{item.output}」</div>
              ))}
            </div>
          )}
        </section>

        <section className="chat-card">
          <div className="chat-header">
            <div>
              <div className="brand" style={{ color: "var(--on-dark-soft)" }}>Chat Simulator</div>
              <div style={{ marginTop: 6, color: "var(--on-dark-soft)" }}>风格模拟，不代表真人本人。</div>
            </div>
            <span className="badge"><span className="dot" />{statusLabel}</span>
          </div>
          <div className="messages">
            {messages.map((item, index) => (
              <div className={`message ${item.role}`} key={`${item.role}-${index}`}>{item.content}</div>
            ))}
            {loading && <div className="message assistant">正在想……</div>}
          </div>
          <form className="composer" onSubmit={submit}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入一句话，系统会检索相关历史片段并生成风格化回复…"
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <button className="primary" disabled={loading || !input.trim()}>{loading ? "发送中" : "发送"}</button>
          </form>
        </section>
      </div>
    </main>
  );
}
