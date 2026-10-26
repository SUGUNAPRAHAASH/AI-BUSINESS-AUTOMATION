"use client";

import { useEffect, useState } from "react";
import { Users, Filter, RefreshCw, X, CheckCircle, Mail, Phone, Calendar, ArrowRight } from "lucide-react";

interface Lead {
  id: string;
  name?: string;
  email?: string;
  phone?: string;
  interest?: string;
  budget_text?: string;
  timeline_text?: string;
  score: "hot" | "warm" | "cold";
  score_reason: string;
  summary: string;
  next_best_action: string;
  crm_id?: string;
  status: string;
  created_at?: string;
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [filterScore, setFilterScore] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  async function loadLeads() {
    setLoading(true);
    try {
      const url = filterScore
        ? `/api/proxy/v1/leads?score=${filterScore}`
        : "/api/proxy/v1/leads";
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLeads(data.leads || []);
      }
    } catch (err) {
      console.error("Error loading leads", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadLeads();
  }, [filterScore]);

  async function triggerFollowup(id: string) {
    setSyncing(true);
    try {
      await fetch(`/api/proxy/v1/leads/${id}/followup`, { method: "POST" });
      await loadLeads();
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="h-6 w-6 text-teal-400" />
            Patient Leads CRM
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Autonomous qualification, scoring, and HubSpot CRM synchronization
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={filterScore}
              onChange={(e) => setFilterScore(e.target.value)}
              className="bg-transparent text-white focus:outline-none cursor-pointer"
            >
              <option value="">All Scores</option>
              <option value="hot">Hot Only</option>
              <option value="warm">Warm Only</option>
              <option value="cold">Cold Only</option>
            </select>
          </div>

          <button
            onClick={() => loadLeads()}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Leads Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/80 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
              <tr>
                <th className="p-4 pl-6">Patient</th>
                <th className="p-4">Treatment Interest</th>
                <th className="p-4">Score</th>
                <th className="p-4">Timeline / Budget</th>
                <th className="p-4">CRM Sync</th>
                <th className="p-4 pr-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {leads.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-500">
                    No patient leads found matching criteria.
                  </td>
                </tr>
              ) : (
                leads.map((l) => (
                  <tr
                    key={l.id}
                    onClick={() => setSelectedLead(l)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="p-4 pl-6">
                      <div className="font-semibold text-white">{l.name || "Anonymous Visitor"}</div>
                      <div className="text-xs text-slate-400">{l.email || l.phone || "No direct contact"}</div>
                    </td>
                    <td className="p-4 text-slate-300 font-medium">
                      {l.interest || "General Inquiry"}
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide ${
                          l.score === "hot"
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : l.score === "warm"
                            ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {l.score}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-slate-400">
                      <div>{l.timeline_text || "Flexible"}</div>
                      <div className="text-slate-500">{l.budget_text || "Standard fee"}</div>
                    </td>
                    <td className="p-4">
                      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400">
                        <CheckCircle className="h-3.5 w-3.5" />
                        {l.crm_id ? "Synced to HubSpot" : "Mock Synced"}
                      </span>
                    </td>
                    <td className="p-4 pr-6 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedLead(l);
                        }}
                        className="text-xs text-teal-400 hover:text-teal-300 font-medium inline-flex items-center gap-1"
                      >
                        <span>View</span>
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Slide-over Drawer */}
      {selectedLead && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-sm">
          <div className="w-full max-w-lg bg-slate-900 border-l border-slate-800 p-6 flex flex-col justify-between shadow-2xl overflow-y-auto">
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h2 className="text-lg font-bold text-white">Lead Intelligence Detail</h2>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">ID: {selectedLead.id}</p>
                </div>
                <button
                  onClick={() => setSelectedLead(null)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Status & Name */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="text-base font-bold text-white">{selectedLead.name || "Anonymous Patient"}</div>
                  <div className="text-xs text-slate-400 mt-0.5 flex items-center gap-3">
                    {selectedLead.email && (
                      <span className="flex items-center gap-1"><Mail className="h-3 w-3 text-teal-400" /> {selectedLead.email}</span>
                    )}
                    {selectedLead.phone && (
                      <span className="flex items-center gap-1"><Phone className="h-3 w-3 text-teal-400" /> {selectedLead.phone}</span>
                    )}
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  {selectedLead.score}
                </span>
              </div>

              {/* Score Reason & AI Summary */}
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">AI Scoring Rubric Reason</label>
                  <p className="text-sm text-slate-200 mt-1 p-3 rounded-lg bg-slate-950 border border-slate-800">
                    {selectedLead.score_reason}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Clinical Summary</label>
                  <p className="text-sm text-slate-200 mt-1 p-3 rounded-lg bg-slate-950 border border-slate-800 leading-relaxed">
                    {selectedLead.summary}
                  </p>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Recommended Next Best Action</label>
                  <div className="text-sm text-teal-300 font-medium mt-1 p-3 rounded-lg bg-teal-950/40 border border-teal-500/30">
                    {selectedLead.next_best_action}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-6 border-t border-slate-800 flex gap-3">
              <button
                disabled={syncing}
                onClick={() => triggerFollowup(selectedLead.id)}
                className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-teal-600/20 disabled:opacity-50"
              >
                <Mail className="h-4 w-4" />
                <span>{syncing ? "Sending..." : "Dispatch Follow-up Email"}</span>
              </button>
              <button
                onClick={() => setSelectedLead(null)}
                className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
