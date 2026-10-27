"use client";

import { useEffect, useState } from "react";
import { Send, RefreshCw, Activity, ShieldCheck, CheckCircle2 } from "lucide-react";

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
              Operations Audit
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">Event Logs & Dispatches</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <Send className="h-7 w-7 text-teal-600" />
            Dispatch & Practice Activity Logs
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time audit trail of outbound patient emails, HubSpot contacts, Airtable records, and clinical team notifications.
          </p>
        </div>
        <button
          onClick={loadOutbox}
          className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs self-start md:self-auto"
          title="Refresh Logs"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Outbox Cards */}
      <div className="space-y-3.5">
        {items.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 text-slate-400 text-sm">
            Activity log is currently quiet. Patient bookings and email dispatches will populate live logs here.
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-2xs hover:border-slate-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
                    {item.integration}
                  </span>
                  <span className="text-sm font-bold text-slate-900">{item.action}</span>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {new Date(item.created_at).toLocaleTimeString()} • {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 font-mono text-xs text-slate-700 overflow-x-auto">
                <pre>{JSON.stringify(item.payload, null, 2)}</pre>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
