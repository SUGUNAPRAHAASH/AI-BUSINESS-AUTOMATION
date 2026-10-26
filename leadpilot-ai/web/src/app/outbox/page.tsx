"use client";

import { useEffect, useState } from "react";
import { Send, RefreshCw, Layers } from "lucide-react";

interface OutboxItem {
  id: string;
  integration: string;
  action: string;
  payload: any;
  created_at: string;
}

export default function OutboxPage() {
  const [items, setItems] = useState<OutboxItem[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadOutbox() {
    setLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/admin/mock-outbox");
      if (res.ok) {
        const data = await res.json();
        setItems(data.outbox || []);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadOutbox();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Send className="h-6 w-6 text-teal-400" />
            Mock Outbox Inspector
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time visual audit of simulated outbound dispatches across Slack, HubSpot, Gmail, and Google Sheets
          </p>
        </div>
        <button
          onClick={loadOutbox}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Outbox Cards */}
      <div className="space-y-4">
        {items.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800 text-slate-500 text-sm">
            Mock outbox is currently empty. Run demo scenarios or chats to populate simulated dispatches.
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider bg-teal-500/10 text-teal-400 border border-teal-500/20">
                    {item.integration}
                  </span>
                  <span className="text-sm font-semibold text-white">{item.action}</span>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {new Date(item.created_at).toLocaleTimeString()} • {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-xs text-slate-300 overflow-x-auto">
                <pre>{JSON.stringify(item.payload, null, 2)}</pre>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
