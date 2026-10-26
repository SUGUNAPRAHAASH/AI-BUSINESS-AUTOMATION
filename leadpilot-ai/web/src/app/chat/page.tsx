"use client";

import { useState } from "react";
import { Send, Sparkles, User, AlertCircle, BookOpen, UserCheck } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Array<{ title: string; source: string; score: number }>;
  leadCaptured?: any;
  handoff?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! Welcome to BrightSmile Dental. I'm your front-desk AI assistant. How can I help you today with treatments, pricing, or appointment scheduling?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/proxy/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          channel: "web",
          tenant: "brightsmile",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const asstMsg: Message = {
          role: "assistant",
          content: data.answer,
          citations: data.citations,
          leadCaptured: data.lead_captured,
          handoff: data.handoff,
        };
        setMessages((prev) => [...prev, asstMsg]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, I encountered an error connecting to our clinic operations service.",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Network error communicating with the agent server.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "How much is teeth whitening and do you do weekend appointments?",
    "I'm interested in Invisalign, my name is Priya Nair, priya@example.com, start next month, budget 4000.",
    "Do you treat horses?",
  ];

  return (
    <div className="flex-1 flex flex-col h-screen max-w-5xl mx-auto w-full p-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-teal-400" />
            BrightSmile Clinical Support AI
          </h1>
          <p className="text-xs text-slate-400">Grounded by RAG Knowledge Base & Autonomous LangGraph State Machine</p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 font-medium">
          Live Agent
        </span>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto py-6 space-y-5">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-2xl ${
              m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                m.role === "user"
                  ? "bg-teal-600 text-white"
                  : "bg-slate-800 text-teal-400 border border-slate-700"
              }`}
            >
              {m.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            </div>

            <div className="space-y-2">
              <div
                className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-teal-600 text-white rounded-tr-none shadow-md shadow-teal-600/20"
                    : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm"
                }`}
              >
                {m.content}
              </div>

              {/* Citations */}
              {m.citations && m.citations.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
                    <BookOpen className="h-3 w-3 text-teal-400" /> Sources:
                  </span>
                  {m.citations.map((c, ci) => (
                    <span
                      key={ci}
                      className="text-[11px] px-2 py-0.5 rounded-md bg-slate-900 border border-slate-800 text-teal-300 font-mono"
                    >
                      {c.source} ({Math.round(c.score * 1000) / 10}%)
                    </span>
                  ))}
                </div>
              )}

              {/* Lead Capture Flag */}
              {m.leadCaptured && (
                <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
                  <UserCheck className="h-4 w-4 shrink-0 text-emerald-400" />
                  <div>
                    <span className="font-semibold">Lead Qualified: </span>
                    {m.leadCaptured.name} ({m.leadCaptured.email}) — <strong className="uppercase">{m.leadCaptured.score}</strong> ({m.leadCaptured.score_reason})
                  </div>
                </div>
              )}

              {/* Human Handoff Banner */}
              {m.handoff && (
                <div className="p-3 rounded-xl bg-amber-950/60 border border-amber-500/30 text-xs text-amber-300 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-400" />
                  <div>
                    <span className="font-semibold">Escalated to Human Desk: </span>
                    A notification was dispatched to the front-desk Slack channel for immediate human follow-up.
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 max-w-md mr-auto">
            <div className="h-8 w-8 rounded-full bg-slate-800 text-teal-400 flex items-center justify-center shrink-0">
              <Sparkles className="h-4 w-4 animate-spin" />
            </div>
            <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-400 animate-pulse"></span>
              <span>Consulting dental knowledge base & reasoning...</span>
            </div>
          </div>
        )}
      </div>

      {/* Suggested Quick Questions */}
      <div className="py-2 flex items-center gap-2 overflow-x-auto text-xs pb-3">
        <span className="text-slate-500 whitespace-nowrap">Try:</span>
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(p)}
            className="px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-teal-500/50 whitespace-nowrap transition-colors"
          >
            {p.length > 45 ? p.substring(0, 45) + "..." : p}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
        className="flex items-center gap-2 pt-2 border-t border-slate-800"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question or inquire about appointments..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-5 py-3 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-medium text-sm flex items-center gap-2 transition-all shadow-md shadow-teal-600/20"
        >
          <span>Send</span>
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
