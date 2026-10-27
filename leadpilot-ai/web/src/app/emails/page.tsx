"use client";

import { useEffect, useState } from "react";
import {
  Mail,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Send,
  Plus,
  Sparkles,
  Inbox,
  Shield,
  CheckCircle2,
  X,
} from "lucide-react";

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
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  // Ingest / Simulate Email Modal
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [simFrom, setSimFrom] = useState("jessica.m@healthmail.com");
  const [simSubject, setSimSubject] = useState("Request to reschedule Saturday 11 AM consultation");
  const [simBody, setSimBody] = useState(
    "Hi BrightSmile front desk,\n\nI have a 30-min consultation booked for this Saturday at 11 AM with Dr. Sarah. Could I please reschedule to next Saturday or see if Dr. Alex has an open slot at 11 AM?\n\nThank you,\nJessica Miller"
  );
  const [simLoading, setSimLoading] = useState(false);

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
    setActionMessage(null);
    try {
      const res = await fetch(`/api/proxy/v1/emails/${id}/approve`, { method: "POST" });
      if (res.ok) {
        setActionMessage("✓ Draft approved and dispatched live to patient! Activity logged.");
        await loadEmails();
        const found = emails.find((e) => e.id === id);
        if (found) setSelectedEmail({ ...found, action: "approved" });
      }
    } finally {
      setProcessing(false);
    }
  }

  async function handleReject(id: string) {
    setProcessing(true);
    setActionMessage(null);
    try {
      const res = await fetch(`/api/proxy/v1/emails/${id}/reject`, { method: "POST" });
      if (res.ok) {
        setActionMessage("Draft rejected. Marked as rejected in inbox.");
        await loadEmails();
        const found = emails.find((e) => e.id === id);
        if (found) setSelectedEmail({ ...found, action: "rejected" });
      }
    } finally {
      setProcessing(false);
    }
  }

  async function handleSimulateEmail(e: React.FormEvent) {
    e.preventDefault();
    setSimLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/emails/triage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_id: `msg-${Date.now()}`,
          from_addr: simFrom,
          subject: simSubject,
          body: simBody,
        }),
      });
      if (res.ok) {
        setTestModalOpen(false);
        setActionMessage("✓ Incoming email triaged! Hospital intake alert sent to prahaashnms18@gmail.com.");
        await loadEmails();
      }
    } finally {
      setSimLoading(false);
    }
  }

  const samplePresets = [
    {
      title: "Reschedule Saturday Slot",
      from: "jessica.m@healthmail.com",
      subject: "Request to reschedule Saturday 11 AM consultation",
      body: "Hello, I currently have an 11 AM Saturday appointment with Dr. Sarah. Could I reschedule to 11:30 AM or next Saturday? Thanks!",
    },
    {
      title: "Acute Pain Urgency",
      from: "robert.c@domain.com",
      subject: "Severe tooth pain and swelling on right jaw",
      body: "Hi clinic, I woke up with severe throbbing tooth pain and facial swelling. Do you have emergency relief slots today?",
    },
    {
      title: "Invisalign Pricing Ingestion",
      from: "david.p@workmail.com",
      subject: "Invisalign treatment cost and weekend availability",
      body: "Hello BrightSmile team, what is your pricing for clear aligners and do you have Saturday 30-min scan consultations?",
    },
  ];

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
              Clinical Triage Desk
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">
              Automated Categorization • Hospital Alert Intimation • Human Approval
            </span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <Mail className="h-7 w-7 text-teal-600" />
            Email Triage & Human Review Desk
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Categorization, entity extraction, automated draft replies, and instant hospital notification dispatch.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setTestModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs md:text-sm flex items-center gap-2 shadow-xs transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>Simulate Incoming Patient Email</span>
          </button>
          <button
            onClick={loadEmails}
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs"
            title="Refresh Inbox"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Hospital Notice Banner */}
      <div className="p-4 rounded-2xl bg-teal-50/70 border border-teal-200/80 flex items-center justify-between text-xs text-teal-900">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-xl bg-teal-600/10 text-teal-700 flex items-center justify-center shrink-0">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <span className="font-bold">Dual Email Architecture Active:</span>
            <p className="text-teal-800 mt-0.5">
              1) Hospital administration notification is dispatched to <code>prahaashnms18@gmail.com</code>. 2) Upon approval or chat booking, patient confirmation is delivered directly to the patient&apos;s email.
            </p>
          </div>
        </div>
        <span className="hidden sm:inline-flex px-2.5 py-1 rounded-full bg-white text-teal-800 border border-teal-200 font-semibold shadow-2xs">
          Live Dispatch
        </span>
      </div>

      {actionMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-900 flex items-center gap-2 shadow-2xs">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[550px]">
        {/* Email Inbox Queue */}
        <div className="lg:col-span-5 rounded-2xl bg-white border border-slate-200 shadow-xs flex flex-col overflow-hidden">
          <div className="p-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between text-xs font-bold text-slate-600">
            <span className="flex items-center gap-1.5">
              <Inbox className="h-4 w-4 text-teal-600" />
              Inbox Queue ({emails.length})
            </span>
            <span>Priority</span>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {emails.length === 0 ? (
              <div className="p-12 text-center text-slate-400 text-xs space-y-2">
                <p>No emails in triage queue.</p>
                <button
                  onClick={() => setTestModalOpen(true)}
                  className="px-3 py-1.5 rounded-lg bg-teal-50 text-teal-700 font-semibold border border-teal-200 text-xs"
                >
                  Simulate a Patient Email
                </button>
              </div>
            ) : (
              emails.map((e) => (
                <div
                  key={e.id}
                  onClick={() => {
                    setSelectedEmail(e);
                    setActionMessage(null);
                  }}
                  className={`p-4 cursor-pointer transition-all ${
                    selectedEmail?.id === e.id
                      ? "bg-teal-50/70 border-l-4 border-teal-600"
                      : "hover:bg-slate-50/80"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 truncate max-w-[200px]">
                      {e.from_addr}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        e.priority === "high"
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {e.category}
                    </span>
                  </div>
                  <div className="text-xs text-slate-700 font-semibold truncate mt-1">
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

        {/* Selected Email Details & Live Draft */}
        <div className="lg:col-span-7 rounded-2xl bg-white border border-slate-200 shadow-xs p-6 flex flex-col justify-between">
          {selectedEmail ? (
            <div className="space-y-6">
              {/* Header Info */}
              <div className="border-b border-slate-100 pb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono">
                    {selectedEmail.message_id}
                  </span>
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                      selectedEmail.action === "approved"
                        ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                        : selectedEmail.action === "rejected"
                        ? "bg-rose-50 text-rose-800 border border-rose-200"
                        : "bg-amber-50 text-amber-800 border border-amber-200"
                    }`}
                  >
                    Action: {selectedEmail.action.toUpperCase()}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-slate-900">{selectedEmail.subject}</h2>
                <div className="text-xs text-slate-500 mt-1">
                  From: <strong>{selectedEmail.from_addr}</strong>
                </div>
              </div>

              {/* Patient Message */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                  Patient Incoming Message
                </label>
                <div className="mt-1.5 p-4 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-800 whitespace-pre-wrap leading-relaxed">
                  {selectedEmail.body}
                </div>
              </div>

              {/* AI Draft Response */}
              <div>
                <label className="text-xs font-bold text-teal-700 uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-teal-600" />
                  AI Suggested Clinical Draft Response
                </label>
                <div className="mt-1.5 p-4 rounded-xl bg-teal-50/50 border border-teal-200/80 text-sm text-slate-800 whitespace-pre-wrap leading-relaxed font-sans">
                  {selectedEmail.draft_reply}
                </div>
              </div>

              {/* Actions */}
              <div className="pt-4 border-t border-slate-100 flex gap-3">
                <button
                  disabled={processing || selectedEmail.action === "approved"}
                  onClick={() => handleApprove(selectedEmail.id)}
                  className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-xs transition-colors"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>{processing ? "Dispatching..." : "Approve & Deliver Draft Live"}</span>
                </button>
                <button
                  disabled={processing || selectedEmail.action === "rejected"}
                  onClick={() => handleReject(selectedEmail.id)}
                  className="px-5 py-2.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-semibold text-sm flex items-center gap-2 transition-colors"
                >
                  <XCircle className="h-4 w-4" />
                  <span>Reject</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 text-sm space-y-2">
              <Mail className="h-10 w-10 text-slate-300" />
              <p>Select an incoming email from the queue to review triage analysis and draft reply.</p>
            </div>
          )}
        </div>
      </div>

      {/* Simulate Incoming Patient Email Modal */}
      {testModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Mail className="h-4 w-4 text-teal-600" />
                  Simulate Incoming Patient Email
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Tests automatic AI triage, entity parsing, and hospital intake alert email.
                </p>
              </div>
              <button
                onClick={() => setTestModalOpen(false)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Quick Sample Presets */}
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                Quick Clinical Presets:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {samplePresets.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSimFrom(preset.from);
                      setSimSubject(preset.subject);
                      setSimBody(preset.body);
                    }}
                    className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-teal-50 hover:text-teal-800 border border-slate-200 transition-colors"
                  >
                    {preset.title}
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSimulateEmail} className="space-y-3.5 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Patient From Email</label>
                <input
                  type="email"
                  required
                  value={simFrom}
                  onChange={(e) => setSimFrom(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Subject</label>
                <input
                  type="text"
                  required
                  value={simSubject}
                  onChange={(e) => setSimSubject(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Email Body Content</label>
                <textarea
                  rows={4}
                  required
                  value={simBody}
                  onChange={(e) => setSimBody(e.target.value)}
                  className="w-full p-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 focus:outline-none focus:border-teal-500 font-sans"
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setTestModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-100 font-semibold text-slate-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={simLoading}
                  className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold shadow-xs transition-colors"
                >
                  {simLoading ? "Processing AI Triage..." : "Submit to Triage Desk"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
