"use client";

import { useState } from "react";
import { BookOpen, Search, RefreshCw, CheckCircle, FileText, Sparkles } from "lucide-react";

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
              Practice RAG Context
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">Grounded Vector Embeddings</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <BookOpen className="h-7 w-7 text-teal-600" />
            Clinical Knowledge Base
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Grounded clinical facts, fee schedules, doctor hours, and hybrid semantic retrieval.
          </p>
        </div>

        <button
          onClick={triggerReingest}
          disabled={ingesting}
          className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center gap-2 shadow-xs transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${ingesting ? "animate-spin" : ""}`} />
          <span>{ingesting ? "Re-Indexing..." : "Re-Index Knowledge Base"}</span>
        </button>
      </div>

      {ingestMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-900 flex items-center gap-2 shadow-2xs">
          <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
          <span>{ingestMessage}</span>
        </div>
      )}

      {/* Search Input */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="h-4 w-4 absolute left-4 top-3.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Test semantic search across practice facts (e.g. Saturday hours, veneers pricing, emergency)..."
            className="w-full bg-white border border-slate-200 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:border-teal-500 shadow-2xs"
          />
        </div>
        <button
          type="submit"
          disabled={searching}
          className="px-5 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition-colors shadow-2xs"
        >
          {searching ? "Searching..." : "Search RAG"}
        </button>
      </form>

      {/* Semantic Search Results */}
      {searchResults.length > 0 && (
        <div className="p-6 rounded-2xl bg-white border border-teal-200 shadow-xs space-y-3">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-teal-600" />
            Top Retrieved Chunks ({searchResults.length})
          </h3>
          <div className="space-y-2.5">
            {searchResults.map((r, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900">{r.title}</span>
                  <span className="text-teal-700 font-semibold text-[11px]">Score: {r.score?.toFixed(3)}</span>
                </div>
                <p className="text-slate-600 leading-relaxed">{r.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Grounded Practice Documents Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {kbDocs.map((doc, idx) => (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-white border border-slate-200 shadow-xs space-y-3 hover:border-slate-300 transition-colors"
          >
            <div className="flex items-center justify-between">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
                {doc.category}
              </span>
              <span className="text-xs text-slate-400 font-medium">{doc.chunks} chunks</span>
            </div>
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-slate-100 text-slate-700 shrink-0">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">{doc.title}</h4>
                <p className="text-xs text-slate-500 font-mono mt-0.5">{doc.source}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
