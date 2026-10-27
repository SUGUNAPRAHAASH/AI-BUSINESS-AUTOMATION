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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-800 border border-rose-200">
              System Reliability
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">Dead-Letter Queue & Retries</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <AlertOctagon className="h-7 w-7 text-rose-600" />
            Failed Jobs & Dead-Letter Queue
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Dead-letter queue for failed outbound webhooks, automated retries, and manual intervention.
          </p>
        </div>
        <button
          onClick={loadJobs}
          className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs self-start sm:self-auto"
          title="Refresh Queue"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {jobs.length === 0 ? (
          <div className="p-12 text-center rounded-2xl bg-white border border-slate-200 text-slate-500 text-sm space-y-2">
            <CheckCircle className="h-8 w-8 text-emerald-500 mx-auto" />
            <p className="font-bold text-slate-800">Dead-letter queue is completely empty!</p>
            <p className="text-xs text-slate-400">All outbound webhooks and asynchronous tasks have succeeded without errors.</p>
          </div>
        ) : (
          jobs.map((job) => (
            <div
              key={job.id}
              className="p-5 rounded-2xl bg-white border border-rose-200 shadow-xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200">
                    {job.job_type}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">ID: {job.id.slice(0, 8)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-medium">Attempts: {job.attempts}</span>
                  <button
                    onClick={() => handleRetry(job.id)}
                    disabled={retryingId === job.id}
                    className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs flex items-center gap-1.5 transition-colors shadow-2xs"
                  >
                    <RotateCcw className={`h-3.5 w-3.5 ${retryingId === job.id ? "animate-spin" : ""}`} />
                    <span>Retry</span>
                  </button>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-rose-50/60 border border-rose-200/60 text-xs font-mono text-rose-900">
                {job.error}
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700 overflow-x-auto">
                <pre>{JSON.stringify(job.payload, null, 2)}</pre>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
