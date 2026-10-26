"use client";

import { useEffect, useState } from "react";
import { AlertOctagon, RefreshCw, CheckCircle, RotateCcw } from "lucide-react";

interface FailedJob {
  id: string;
  job_type: string;
  payload: any;
  error: string;
  attempts: number;
  status: string;
  created_at: string;
  last_attempt_at?: string;
}

export default function FailedJobsPage() {
  const [jobs, setJobs] = useState<FailedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [retryingId, setRetryingId] = useState<string | null>(null);

  async function loadJobs() {
    setLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/admin/failed-jobs");
      if (res.ok) {
        const data = await res.json();
        setJobs(data.failed_jobs || []);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadJobs();
  }, []);

  async function handleRetry(jobId: string) {
    setRetryingId(jobId);
    try {
      const res = await fetch(`/api/proxy/v1/admin/failed-jobs/${jobId}/retry`, {
        method: "POST",
      });
      if (res.ok) {
        await loadJobs();
      }
    } catch (err) {
      console.error("Retry failed", err);
    } finally {
      setRetryingId(null);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <AlertOctagon className="h-6 w-6 text-rose-400" />
            Reliability & Failed Jobs Queue
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Dead-letter failure queue with exponential backoff and operator manual re-execution
          </p>
        </div>
        <button
          onClick={loadJobs}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-950/80 uppercase tracking-wider text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="p-4 pl-6">Job ID</th>
              <th className="p-4">Type</th>
              <th className="p-4">Error Cause</th>
              <th className="p-4">Attempts</th>
              <th className="p-4">Status</th>
              <th className="p-4 pr-6 text-right">Retry Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {jobs.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500 text-sm">
                  <CheckCircle className="h-6 w-6 text-emerald-400 mx-auto mb-2" />
                  No failed jobs in queue. System running with 100% operational success.
                </td>
              </tr>
            ) : (
              jobs.map((j) => (
                <tr key={j.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="p-4 pl-6 font-mono text-slate-300">{j.id.substring(0, 18)}...</td>
                  <td className="p-4 font-semibold text-white uppercase">{j.job_type}</td>
                  <td className="p-4 text-rose-300 max-w-xs truncate">{j.error}</td>
                  <td className="p-4 text-slate-400">{j.attempts} tries</td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-0.5 rounded-full font-semibold ${
                        j.status === "resolved"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                      }`}
                    >
                      {j.status}
                    </span>
                  </td>
                  <td className="p-4 pr-6 text-right">
                    <button
                      disabled={retryingId === j.id || j.status === "resolved"}
                      onClick={() => handleRetry(j.id)}
                      className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 disabled:opacity-40 text-white font-medium text-xs inline-flex items-center gap-1.5 transition-all shadow-sm"
                    >
                      <RotateCcw className={`h-3 w-3 ${retryingId === j.id ? "animate-spin" : ""}`} />
                      <span>{retryingId === j.id ? "Retrying..." : "Retry Job"}</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
