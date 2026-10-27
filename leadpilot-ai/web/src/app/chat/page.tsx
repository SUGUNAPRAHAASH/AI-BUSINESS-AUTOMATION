"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, User, AlertCircle, CheckCircle2, Calendar, Stethoscope, Clock, Mail } from "lucide-react";
import ClinicLogo from "@/components/ClinicLogo";

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
      content:
        "Hello and welcome to BrightSmile Health & Dental Clinic! I'm your virtual clinical receptionist. How can I assist you today with treatments, our doctor schedules, or booking your 30-minute consultation?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

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
          conversation_id: conversationId,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.conversation_id && !conversationId) {
          setConversationId(data.conversation_id);
        }
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
            content: "Sorry, I encountered an issue connecting to our practice scheduling engine. Please try again or call our desk at (555) 019-2831.",
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Network error connecting to clinic service. Please ensure connectivity.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const slotOptions = [
    { label: "📅 Saturday 11:00 AM Slot", value: "Do you have Saturday 11 AM available for a 30-min consultation?" },
    { label: "📅 Saturday 11:30 AM Slot", value: "Can I book Saturday 11:30 AM with Dr. Sarah Mitchell?" },
    { label: "🦷 Teeth Whitening ($299)", value: "How much is teeth whitening and what slots are open this Saturday?" },
    { label: "✨ Invisalign Scan ($4,200)", value: "I'd like to consult for Invisalign with Dr. Alex Rivera." },
  ];

  return (
    <div className="flex-1 flex flex-col h-full max-w-4xl mx-auto w-full p-3 sm:p-6 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 sm:pb-4 border-b border-slate-200/80 bg-white/80 backdrop-blur-xs px-3 sm:px-4 py-2.5 rounded-2xl border border-slate-200/60 shadow-2xs shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Stethoscope className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-extrabold text-slate-900 tracking-tight">
              BrightSmile Virtual Receptionist
            </h1>
            <p className="text-xs text-slate-500 hidden sm:block">
              Intelligent 30-min booking, conflict resolution & dual email notifications
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Live Agent</span>
          </span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto py-4 sm:py-6 space-y-4 px-1 sm:px-2">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 max-w-2xl ${
              m.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
            }`}
          >
            {/* Avatar */}
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold shadow-2xs ${
                m.role === "user"
                  ? "bg-teal-600 text-white"
                  : "bg-white text-teal-700 border border-slate-200"
              }`}
            >
              {m.role === "user" ? <User className="h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
            </div>

            <div className="space-y-2">
              {/* Message Bubble */}
              <div
                className={`p-3.5 sm:p-4 rounded-2xl text-sm leading-relaxed shadow-2xs ${
                  m.role === "user"
                    ? "bg-teal-600 text-white rounded-tr-none"
                    : "bg-white border border-slate-200 text-slate-800 rounded-tl-none font-sans"
                }`}
              >
                {m.content}
              </div>

              {/* Lead Capture & Dual Email Alert Banner */}
              {m.leadCaptured && (
                <div className="p-3.5 rounded-xl bg-teal-50 border border-teal-200/90 text-xs text-teal-900 space-y-2 shadow-2xs">
                  <div className="flex items-center gap-2 font-bold text-teal-950">
                    <CheckCircle2 className="h-4 w-4 text-teal-600 shrink-0" />
                    <span>Dual Confirmation Emails Dispatched:</span>
                  </div>
                  <div className="space-y-1 pl-6 text-[11px] text-teal-800">
                    <div className="flex items-center gap-1.5">
                      <Mail className="h-3 w-3 text-teal-600" />
                      <span><strong>Hospital Intake:</strong> Intimated practice admin at <code>prahaashnms18@gmail.com</code></span>
                    </div>
                    {m.leadCaptured.email && (
                      <div className="flex items-center gap-1.5">
                        <Mail className="h-3 w-3 text-teal-600" />
                        <span><strong>Patient Receipt:</strong> Sent consultation guide to <code>{m.leadCaptured.email}</code></span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Human Handoff Banner */}
              {m.handoff && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
                  <div>
                    <span className="font-semibold">Front-Desk Team Alerted: </span>
                    Our receptionist staff has been paged via Telegram and will follow up with you.
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 max-w-md mr-auto">
            <div className="h-8 w-8 rounded-full bg-white border border-slate-200 text-teal-600 flex items-center justify-center shrink-0">
              <Sparkles className="h-4 w-4 animate-spin" />
            </div>
            <div className="p-3.5 rounded-2xl bg-white border border-slate-200 text-xs text-slate-500 flex items-center gap-2 shadow-2xs">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse"></span>
              <span>Checking live doctor schedules & medical knowledge base...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Slot Quick Pills */}
      <div className="py-2 flex items-center gap-2 overflow-x-auto text-xs pb-2 shrink-0">
        <span className="text-slate-400 font-semibold whitespace-nowrap text-[11px] uppercase tracking-wider">
          Quick Inquire:
        </span>
        {slotOptions.map((opt, idx) => (
          <button
            key={idx}
            onClick={() => sendMessage(opt.value)}
            className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-teal-400 hover:bg-teal-50/80 text-slate-700 hover:text-teal-900 whitespace-nowrap transition-all shadow-2xs font-medium"
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
        className="flex items-center gap-2 pt-2 border-t border-slate-200/80 shrink-0"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question or enter your details (e.g., Saturday 11 AM, name, email, phone)..."
          className="flex-1 bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500 shadow-2xs transition-colors"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-5 py-3 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold text-sm flex items-center gap-2 transition-all shadow-xs"
        >
          <span>Send</span>
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
