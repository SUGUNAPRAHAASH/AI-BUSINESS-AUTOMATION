"use client";

import { useEffect, useState } from "react";
import { Mail, CheckCircle, XCircle, AlertTriangle, Clock, RefreshCw, Send } from "lucide-react";

interface EmailItem {
  id: string;
  message_id: string;
  from_addr: string;
  subject: string;
  body: string;
  category: string;
  entities: any;
  priority: string;
  draft_reply: string;
  action: string;
  created_at: string;
}

export default function EmailsPage() {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<EmailItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  async function loadEmails() {
    setLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/emails");
      if (res.ok) {
        const data = await res.json();
        const list = data.emails || [];
        setEmails(list);
        if (list.length > 0 && !selectedEmail) {
          setSelectedEmail(list[0]);
        }
      }
    } catch (err) {
      console.error("Error loading emails", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEmails();
  }, []);

  async function handleApprove(id: string) {
    setProcessing(true);
    try {
      await fetch(`/api/proxy/v1/emails/${id}/approve`, { method: "POST" });
      await loadEmails();
    } finally {
      setProcessing(false);
    }
  }

  async function handleReject(id: string) {
    setProcessing(true);
    try {
      await fetch(`/api/proxy/v1/emails/${id}/reject`, { method: "POST" });
      await loadEmails();
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Mail className="h-6 w-6 text-teal-400" />
            Email Triage & Human Approval
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Categorization, entity extraction, and automated reply drafts for BrightSmile front desk
          </p>
        </div>
        <button
          onClick={loadEmails}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Split View: List on left, Draft & Actions on right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[600px]">
        {/* Email Inbox List */}
        <div className="lg:col-span-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs font-semibold text-slate-400">
            <span>Inbox Queue ({emails.length})</span>
            <span>Status</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
            {emails.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No triaged emails in inbox.
              </div>
            ) : (
              emails.map((e) => (
                <div
                  key={e.id}
                  onClick={() => setSelectedEmail(e)}
                  className={`p-4 cursor-pointer transition-colors ${
                    selectedEmail?.id === e.id
                      ? "bg-teal-500/10 border-l-4 border-teal-500"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-white truncate max-w-[200px]">
                      {e.from_addr}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                        e.priority === "high"
                          ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {e.category}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-medium truncate mt-1">
                    {e.subject}
                  </div>
                  <div className="text-xs text-slate-500 line-clamp-2 mt-1">
                    {e.body}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Selected Email & Draft Reply View */}
        <div className="lg:col-span-7 rounded-2xl bg-slate-900/60 border border-slate-800 p-6 flex flex-col justify-between">
          {selectedEmail ? (
            <div className="space-y-6">
              {/* Header Details */}
              <div className="border-b border-slate-800 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                    {selectedEmail.message_id}
                  </span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                      selectedEmail.action === "approved"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : selectedEmail.action === "rejected"
                        ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                    }`}
                  >
                    Action: {selectedEmail.action}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white">{selectedEmail.subject}</h2>
                <div className="text-xs text-slate-400 mt-1">From: {selectedEmail.from_addr}</div>
              </div>

              {/* Incoming Body */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Patient Message</label>
                <div className="mt-1.5 p-4 rounded-xl bg-slate-950 border border-slate-800 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {selectedEmail.body}
                </div>
              </div>

              {/* AI Draft Reply */}
              <div>
                <label className="text-xs font-semibold text-teal-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Send className="h-3.5 w-3.5" /> AI Generated Draft Response
                </label>
                <div className="mt-1.5 p-4 rounded-xl bg-teal-950/20 border border-teal-500/30 text-sm text-slate-200 whitespace-pre-wrap leading-relaxed font-sans">
                  {selectedEmail.draft_reply}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-4 border-t border-slate-800 flex gap-3">
                <button
                  disabled={processing || selectedEmail.action === "approved"}
                  onClick={() => handleApprove(selectedEmail.id)}
                  className="flex-1 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-md shadow-emerald-600/20"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>{processing ? "Sending..." : "Approve & Send Draft"}</span>
                </button>
                <button
                  disabled={processing || selectedEmail.action === "rejected"}
                  onClick={() => handleReject(selectedEmail.id)}
                  className="px-5 py-2.5 rounded-xl bg-rose-600/10 hover:bg-rose-600/20 border border-rose-500/30 text-rose-400 font-medium text-sm flex items-center gap-2"
                >
                  <XCircle className="h-4 w-4" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-sm">
              Select an email from the inbox to review triage details and draft reply.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
