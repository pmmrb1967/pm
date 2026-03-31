"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  onBoardUpdate: () => void;
};

export const AIChatSidebar = ({ onBoardUpdate }: Props) => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current && typeof bottomRef.current.scrollIntoView === "function") {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { role: "user", content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await api.chat(text, history);
      setMessages([...nextMessages, { role: "assistant", content: res.reply }]);
      if (res.board_updated) {
        onBoardUpdate();
      }
    } catch {
      setError("Failed to reach the AI. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <>
      {/* Toggle button — hidden when sidebar is open to avoid overlap */}
      {!open && <button
        onClick={() => setOpen(true)}
        aria-label="Open AI chat"
        className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-[var(--secondary-purple)] text-white shadow-[var(--shadow)] hover:opacity-90"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M3 5h14M3 10h10M3 15h7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>}

      {/* Sidebar panel */}
      {open && (
        <aside
          data-testid="ai-sidebar"
          className="fixed bottom-0 right-0 top-0 z-40 flex w-[360px] flex-col border-l border-[var(--stroke)] bg-white shadow-[var(--shadow)]"
        >
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
                AI Assistant
              </p>
              <p className="mt-0.5 text-sm font-semibold text-[var(--navy-dark)]">
                Ask me anything about your board
              </p>
            </div>
            <button
              onClick={() => setOpen(false)}
              aria-label="Dismiss AI chat"
              className="text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M1 1L15 15M15 1L1 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>

          {/* Message list */}
          <div className="flex-1 overflow-y-auto px-4 py-4">
            {messages.length === 0 && (
              <p className="text-center text-xs text-[var(--gray-text)]">
                Ask me to add, move, or describe cards on your board.
              </p>
            )}
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`mb-3 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-6 ${
                    msg.role === "user"
                      ? "bg-[var(--secondary-purple)] text-white"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--navy-dark)]"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="mb-3 flex justify-start">
                <div className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 text-sm text-[var(--gray-text)]">
                  Thinking…
                </div>
              </div>
            )}
            {error && (
              <p className="mt-2 text-center text-xs text-red-500">{error}</p>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-[var(--stroke)] p-4">
            <div className="flex gap-2">
              <textarea
                aria-label="Message"
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                placeholder="Type a message… (Enter to send)"
                className="flex-1 resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3 py-2 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)] disabled:opacity-60"
              />
              <button
                onClick={send}
                disabled={loading || !input.trim()}
                aria-label="Send message"
                className="self-end rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </div>
        </aside>
      )}
    </>
  );
};
