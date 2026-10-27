"use client";

import { useEffect, useState } from "react";
import { Users, Filter, RefreshCw, X, CheckCircle, Mail, Phone, Calendar, ArrowRight, ShieldCheck } from "lucide-react";

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
              Patient Registry
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">HubSpot & Airtable Synced</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <Users className="h-7 w-7 text-teal-600" />
            Patient Leads & Consultation Requests
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time qualification, lead scoring, and live synchronization with HubSpot CRM.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-white border border-slate-200 rounded-xl px-3 py-1.5 text-xs shadow-2xs">
            <Filter className="h-3.5 w-3.5 text-slate-400" />
            <select
              value={filterScore}
              onChange={(e) => setFilterScore(e.target.value)}
              className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="">All Scores</option>
              <option value="hot">Hot Only</option>
              <option value="warm">Warm Only</option>
              <option value="cold">Cold Only</option>
            </select>
          </div>

          <button
            onClick={() => loadLeads()}
            className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs"
            title="Refresh Leads"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Leads Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50/80 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200 font-bold">
              <tr>
                <th className="p-4 pl-6">Patient</th>
                <th className="p-4">Treatment Interest</th>
                <th className="p-4">Score</th>
                <th className="p-4">Timeline / Budget</th>
                <th className="p-4">CRM Sync</th>
                <th className="p-4 pr-6 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {leads.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-12 text-center text-slate-400">
                    No patient leads found matching criteria.
                  </td>
                </tr>
              ) : (
                leads.map((l) => (
                  <tr
                    key={l.id}
                    onClick={() => setSelectedLead(l)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                  >
                    <td className="p-4 pl-6">
                      <div className="font-bold text-slate-900">{l.name || "Valued Visitor"}</div>
                      <div className="text-xs text-slate-500">{l.email || l.phone || "No direct contact"}</div>
                    </td>
                    <td className="p-4 text-slate-700 font-semibold">
                      {l.interest || "General Consultation"}
                    </td>
                    <td className="p-4">
                      <span
                        className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide ${
                          l.score === "hot"
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : l.score === "warm"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {l.score}
                      </span>
                    </td>
                    <td className="p-4 text-xs text-slate-600">
                      <div>{l.timeline_text || "Soon"}</div>
                      <div className="text-[11px] text-slate-400">{l.budget_text || "Standard"}</div>
                    </td>
                    <td className="p-4">
                      {l.crm_id ? (
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          <CheckCircle className="h-3 w-3 text-emerald-600" />
                          <span>HubSpot #{l.crm_id.slice(-6)}</span>
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">Local Synced</span>
                      )}
                    </td>
                    <td className="p-4 pr-6 text-right">
                      <span className="text-xs font-semibold text-teal-600 hover:text-teal-700 inline-flex items-center gap-1">
                        View Details <ArrowRight className="h-3 w-3" />
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Lead Drawer Modal */}
      {selectedLead && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 border border-slate-200 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">{selectedLead.name || "Patient Record"}</h3>
                <p className="text-xs text-slate-500 mt-0.5">Lead ID: {selectedLead.id}</p>
              </div>
              <button
                onClick={() => setSelectedLead(null)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-700"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200">
                <div>
                  <span className="text-slate-500 block">Email Address</span>
                  <span className="font-bold text-slate-900">{selectedLead.email || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Phone</span>
                  <span className="font-bold text-slate-900">{selectedLead.phone || "N/A"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Treatment Interest</span>
                  <span className="font-bold text-teal-700">{selectedLead.interest || "General Consultation"}</span>
                </div>
                <div>
                  <span className="text-slate-500 block">Lead Qualification Score</span>
                  <span className="font-bold uppercase text-slate-900">{selectedLead.score}</span>
                </div>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Scoring Rationale</span>
                <p className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-700">
                  {selectedLead.score_reason}
                </p>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Clinical Summary</span>
                <p className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-700">
                  {selectedLead.summary}
                </p>
              </div>

              <div>
                <span className="font-bold text-slate-700 block mb-1">Recommended Next Step</span>
                <p className="p-3 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 font-semibold">
                  {selectedLead.next_best_action}
                </p>
              </div>
            </div>

            <div className="pt-2 flex gap-3">
              <button
                onClick={() => setSelectedLead(null)}
                className="flex-1 py-2.5 rounded-xl border border-slate-200 font-semibold text-xs text-slate-600 hover:bg-slate-50"
              >
                Close
              </button>
              <button
                disabled={syncing}
                onClick={() => triggerFollowup(selectedLead.id)}
                className="flex-1 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-xs"
              >
                {syncing ? "Dispatching..." : "Send Follow-Up Intimation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
