"use client";

import { useState } from "react";
import { BookOpen, Search, RefreshCw, CheckCircle, FileText } from "lucide-react";

export default function KnowledgeBasePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestMessage, setIngestMessage] = useState<string | null>(null);

  const kbDocs = [
    { title: "Pricing & Fee Guide", source: "pricing.md", chunks: 6, category: "Treatments & Fees" },
    { title: "Operating Hours & Emergency", source: "opening_hours.md", chunks: 4, category: "Scheduling" },
    { title: "Frequently Asked Questions", source: "faq.md", chunks: 9, category: "Practice Q&A" },
    { title: "Clinical Services & Specialties", source: "services.md", chunks: 4, category: "Cosmetic & Implants" },
    { title: "Practice Policies & HIPAA", source: "policies.md", chunks: 3, category: "Billing & Cancellations" },
    { title: "Post-Treatment Aftercare", source: "aftercare.md", chunks: 3, category: "Patient Recovery" },
  ];

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await fetch(`/api/proxy/v1/kb/search?q=${encodeURIComponent(searchQuery)}`);
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } finally {
      setSearching(false);
    }
  }

  async function triggerReingest() {
    setIngesting(true);
    setIngestMessage(null);
    try {
      const res = await fetch("/api/proxy/v1/kb/ingest", { method: "POST" });
      if (res.ok) {
        setIngestMessage("Knowledge base documents successfully re-chunked and embedded!");
      }
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-teal-400" />
            Knowledge Base Management
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Grounded vector chunks and hybrid search index for BrightSmile Dental
          </p>
        </div>

        <button
          onClick={triggerReingest}
          disabled={ingesting}
          className="px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-medium text-xs flex items-center gap-2 transition-all shadow-md shadow-teal-600/20"
        >
          <RefreshCw className={`h-4 w-4 ${ingesting ? "animate-spin" : ""}`} />
          <span>{ingesting ? "Re-Ingesting..." : "Re-Ingest All Documents"}</span>
        </button>
      </div>

      {ingestMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>{ingestMessage}</span>
        </div>
      )}

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {kbDocs.map((doc, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-4 hover:border-slate-700 transition-colors"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-teal-400 uppercase tracking-wide">
                  {doc.category}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                  {doc.chunks} Chunks
                </span>
              </div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-400" />
                {doc.title}
              </h3>
              <p className="text-xs font-mono text-slate-500 mt-1">{doc.source}</p>
            </div>
            <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
              <span>Embedding Dim: 768</span>
              <span className="text-emerald-400 font-medium">HNSW Indexed</span>
            </div>
          </div>
        ))}
      </div>

      {/* Live Retrieval Tester */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div>
          <h3 className="text-base font-bold text-white">Interactive Hybrid Retrieval Query Tester</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Test vector cosine + BM25 keyword Reciprocal Rank Fusion against current database chunks
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. How much is teeth whitening and Saturday hours?"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-medium text-xs disabled:opacity-50"
          >
            {searching ? "Searching..." : "Test Query"}
          </button>
        </form>

        {searchResults.length > 0 && (
          <div className="space-y-3 pt-2">
            <span className="text-xs font-semibold text-slate-400">Top Retrieved Chunks (RRF Ranked):</span>
            <div className="space-y-2">
              {searchResults.map((r, i) => (
                <div key={i} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between font-semibold">
                    <span className="text-teal-400">{r.title} ({r.source})</span>
                    <span className="font-mono text-slate-400">RRF Score: {r.score}</span>
                  </div>
                  <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">{r.content}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
