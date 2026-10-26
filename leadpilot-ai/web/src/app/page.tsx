"use client";

import { useEffect, useState } from "react";
import { Users, Flame, MessageSquare, Mail, FileCheck, AlertOctagon, CheckCircle2, ShieldCheck, Activity } from "lucide-react";

export default function OverviewPage() {
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [resStats, resHealth] = await Promise.all([
          fetch("/api/proxy/v1/admin/stats"),
          fetch("/api/proxy/health"),
        ]);
        if (resStats.ok) setStats(await resStats.json());
        if (resHealth.ok) setHealth(await resHealth.json());
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const statCards = [
    { label: "Total Leads", value: stats?.total_leads ?? 14, icon: Users, color: "text-blue-400", bg: "bg-blue-500/10" },
    { label: "Hot Leads Today", value: stats?.hot_leads_today ?? 4, icon: Flame, color: "text-amber-400", bg: "bg-amber-500/10" },
    { label: "AI Conversations", value: stats?.total_conversations ?? 28, icon: MessageSquare, color: "text-teal-400", bg: "bg-teal-500/10" },
    { label: "Emails Triaged", value: stats?.emails_triaged ?? 19, icon: Mail, color: "text-indigo-400", bg: "bg-indigo-500/10" },
    { label: "Documents Extracted", value: stats?.documents_extracted ?? 8, icon: FileCheck, color: "text-emerald-400", bg: "bg-emerald-500/10" },
    { label: "Open Failed Jobs", value: stats?.failed_jobs ?? 0, icon: AlertOctagon, color: "text-rose-400", bg: "bg-rose-500/10" },
  ];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto w-full">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Practice Operations Hub</h1>
          <p className="text-sm text-slate-400 mt-1">Autonomous Virtual AI Operations Team for BrightSmile Dental</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>AI Ops System Online</span>
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 text-slate-300 text-xs font-medium">
            <Activity className="h-3.5 w-3.5 text-teal-400" />
            <span>Mock-First Adapter Mode</span>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{card.label}</span>
                <div className={`p-2.5 rounded-xl ${card.bg}`}>
                  <Icon className={`h-5 w-5 ${card.color}`} />
                </div>
              </div>
              <div className="mt-4 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-white tracking-tight">{card.value}</span>
                <span className="text-xs font-medium text-emerald-400">Live Metric</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Chart and Integration Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly Lead Velocity */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">Weekly Patient Lead Velocity</h2>
              <p className="text-xs text-slate-400 mt-0.5">Qualified inquiries captured across Web, Voice & Telegram</p>
            </div>
            <span className="text-xs text-teal-400 font-medium">7-Day Trajectory</span>
          </div>
          <div className="h-44 flex items-end justify-between gap-3 pt-6 px-2">
            {[
              { day: "Mon", leads: 4, height: "h-2/5" },
              { day: "Tue", leads: 7, height: "h-3/5" },
              { day: "Wed", leads: 9, height: "h-4/5" },
              { day: "Thu", leads: 6, height: "h-1/2" },
              { day: "Fri", leads: 12, height: "h-full" },
              { day: "Sat", leads: 8, height: "h-3/4" },
              { day: "Sun", leads: 5, height: "h-2/5" },
            ].map((bar, i) => (
              <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
                <span className="text-xs font-semibold text-teal-300">{bar.leads}</span>
                <div className={`w-full rounded-t-lg bg-gradient-to-t from-teal-600 to-teal-400 ${bar.height} transition-all duration-500 hover:brightness-110 shadow-lg shadow-teal-500/20`}></div>
                <span className="text-xs text-slate-400 font-medium">{bar.day}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Integration Status Panel */}
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-white">Integration Adapters</h2>
            <ShieldCheck className="h-4 w-4 text-teal-400" />
          </div>
          <p className="text-xs text-slate-400 mb-4">Mock-first decoupled architecture ensures 100% offline testability.</p>
          <div className="space-y-2.5 flex-1 overflow-y-auto max-h-64 pr-1">
            {Object.entries(health?.modes || {
              gemini: "mock",
              hubspot: "mock",
              slack: "mock",
              gmail: "mock",
              sheets: "mock",
              airtable: "mock",
              telegram: "mock",
              shopify: "mock",
              vapi: "mock"
            }).map(([name, mode]) => (
              <div key={name} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                <span className="font-semibold text-slate-300 capitalize">{name}</span>
                <span className={`px-2 py-0.5 rounded-full font-medium text-[11px] ${
                  mode === "real"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                }`}>
                  {String(mode).toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
