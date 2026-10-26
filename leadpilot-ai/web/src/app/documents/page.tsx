"use client";

import { useEffect, useState } from "react";
import { FileText, Upload, CheckCircle, AlertTriangle, RefreshCw } from "lucide-react";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [extractedResult, setExtractedResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function loadDocuments() {
    setLoading(true);
    try {
      const res = await fetch("/api/proxy/v1/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/proxy/v1/documents/extract", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setExtractedResult(data);
        await loadDocuments();
      }
    } catch (err) {
      console.error("Upload error", err);
    } finally {
      setUploading(false);
    }
  }

  function loadDemoInvoice() {
    setExtractedResult({
      vendor_name: "Henry Schein Dental Supply",
      invoice_number: "HS-DENT-88412",
      invoice_date: "2026-10-25",
      subtotal: 1240.00,
      tax: 105.40,
      total: 1345.40,
      confidence: 0.98,
      validation_errors: [],
      line_items: [
        { description: "Opalescence 35% Teeth Whitening Gel Syringes (Pk/4)", quantity: 5, unit_price: 68.00, amount: 340.00 },
        { description: "Nitrile Examination Gloves - Powder Free Medium (Box/100)", quantity: 10, unit_price: 22.00, amount: 220.00 },
        { description: "Septodont Septocaine Articaine Dental Anesthetic (50/Pk)", quantity: 4, unit_price: 85.00, amount: 340.00 },
        { description: "3M Filtek Supreme Ultra Universal Composite Syringe", quantity: 5, unit_price: 68.00, amount: 340.00 }
      ]
    });
  }

  return (
    <div className="p-8 max-w-7xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <FileText className="h-6 w-6 text-teal-400" />
            Dental Supply Invoice & Form OCR
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Automated clinical supplier bill audit: extracts line items, verifies pricing maths, and flags supplier overcharges
          </p>
        </div>
        <button
          onClick={loadDocuments}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Upload Box */}
      <div className="p-8 rounded-2xl bg-slate-900/40 border-2 border-dashed border-slate-800 hover:border-teal-500/50 transition-colors flex flex-col items-center justify-center text-center">
        <div className="p-4 rounded-full bg-teal-500/10 text-teal-400 mb-3">
          <Upload className="h-8 w-8" />
        </div>
        <h3 className="text-base font-semibold text-white">Upload Supplier Invoice or Lab Form</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md">
          Audits Henry Schein, Benco, or Patterson Dental invoices. Automatically parses dental products, verifies tax calculations, and logs supplies.
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
          <label className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-500 text-white font-medium text-xs cursor-pointer shadow-md shadow-teal-600/20 transition-all">
            <span>{uploading ? "Extracting..." : "Upload Invoice File"}</span>
            <input
              type="file"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.txt"
            />
          </label>
          <button
            type="button"
            onClick={loadDemoInvoice}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-teal-300 font-medium text-xs transition-all border border-slate-700 flex items-center gap-1.5 shadow-sm"
          >
            <span>⚡ 1-Click Demo: Henry Schein Dental Supply</span>
          </button>
        </div>
      </div>

      {/* Extraction Result Showcase */}
      {extractedResult && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-teal-500/30 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Latest Extraction Result</h3>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20">
                Confidence: {Math.round(extractedResult.confidence * 100)}%
              </span>
            </div>
          </div>

          {extractedResult.validation_errors?.length > 0 && (
            <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 text-xs text-rose-300 space-y-1">
              <div className="font-semibold flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4 text-rose-400" /> Mathematical Discrepancy Flagged:
              </div>
              {extractedResult.validation_errors.map((err: string, i: number) => (
                <div key={i}>• {err}</div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs">
            <div>
              <span className="text-slate-500">Vendor:</span>
              <div className="font-bold text-white text-sm mt-0.5">{extractedResult.vendor_name}</div>
            </div>
            <div>
              <span className="text-slate-500">Invoice Number:</span>
              <div className="font-bold text-teal-400 font-mono text-sm mt-0.5">{extractedResult.invoice_number}</div>
            </div>
            <div>
              <span className="text-slate-500">Date:</span>
              <div className="font-medium text-white text-sm mt-0.5">{extractedResult.invoice_date}</div>
            </div>
            <div>
              <span className="text-slate-500">Grand Total:</span>
              <div className="font-extrabold text-emerald-400 text-sm mt-0.5">${extractedResult.total?.toFixed(2)}</div>
            </div>
          </div>

          <div className="rounded-xl overflow-hidden border border-slate-800">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                <tr>
                  <th className="p-3">Item Description</th>
                  <th className="p-3">Qty</th>
                  <th className="p-3">Unit Price</th>
                  <th className="p-3 text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
                {extractedResult.line_items?.map((item: any, i: number) => (
                  <tr key={i}>
                    <td className="p-3 text-white font-medium">{item.description}</td>
                    <td className="p-3 text-slate-300">{item.quantity}</td>
                    <td className="p-3 text-slate-300">${item.unit_price?.toFixed(2)}</td>
                    <td className="p-3 text-right font-mono text-teal-300">${item.amount?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Historical Extracted Documents */}
      <div className="space-y-3">
        <h3 className="text-base font-bold text-white">Extracted Documents Archive</h3>
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800 overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 uppercase tracking-wider text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-4 pl-6">Filename</th>
                <th className="p-4">Vendor</th>
                <th className="p-4">Invoice #</th>
                <th className="p-4">Total</th>
                <th className="p-4">Confidence</th>
                <th className="p-4 pr-6">Date Extracted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500">
                    No documents uploaded yet. Use the upload area above to extract invoices.
                  </td>
                </tr>
              ) : (
                documents.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4 pl-6 font-semibold text-white">{d.filename || "invoice.pdf"}</td>
                    <td className="p-4 text-slate-300">{d.data?.vendor_name || "Dental Supplies"}</td>
                    <td className="p-4 font-mono text-teal-400">{d.data?.invoice_number || "INV-001"}</td>
                    <td className="p-4 font-semibold text-emerald-400">${d.data?.total || "0.00"}</td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 font-semibold">
                        {Math.round((d.confidence || 0.95) * 100)}%
                      </span>
                    </td>
                    <td className="p-4 pr-6 text-slate-500">{new Date(d.created_at).toLocaleDateString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
