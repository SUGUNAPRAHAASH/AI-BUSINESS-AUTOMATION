"use client";

import { useEffect, useState } from "react";
import { FileText, Upload, CheckCircle, AlertTriangle, RefreshCw, FileCheck } from "lucide-react";

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
              Procurement & Supply
            </span>
            <span className="text-xs text-slate-500 font-medium hidden sm:inline">OCR Line Item Audit</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight mt-1 flex items-center gap-2.5">
            <FileText className="h-7 w-7 text-teal-600" />
            Dental Supply Invoice & Form OCR
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Automated clinical supplier bill audit: extracts line items, verifies pricing maths, and logs supplies.
          </p>
        </div>
        <button
          onClick={loadDocuments}
          className="p-2 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors shadow-2xs self-start sm:self-auto"
          title="Refresh Invoices"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Upload Box */}
      <div className="p-8 rounded-2xl bg-white border-2 border-dashed border-slate-200 hover:border-teal-400 transition-colors flex flex-col items-center justify-center text-center shadow-xs">
        <div className="p-4 rounded-full bg-teal-50 text-teal-700 mb-3 border border-teal-200">
          <Upload className="h-7 w-7" />
        </div>
        <h3 className="text-base font-bold text-slate-900">Upload Supplier Invoice or Lab Form</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md">
          Audits Henry Schein, Benco, or Patterson Dental invoices. Automatically parses dental products, verifies tax calculations, and logs supplies.
        </p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
          <label className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs cursor-pointer shadow-xs transition-colors">
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
            className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-teal-50 text-slate-700 hover:text-teal-900 font-semibold text-xs transition-colors border border-slate-200 flex items-center gap-1.5 shadow-2xs"
          >
            <span>⚡ 1-Click Demo: Henry Schein Dental Supply</span>
          </button>
        </div>
      </div>

      {/* Extraction Result Showcase */}
      {extractedResult && (
        <div className="p-6 rounded-2xl bg-white border border-teal-200/90 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <h3 className="text-base font-bold text-slate-900">Extracted Invoice Audit</h3>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
              Confidence: {Math.round(extractedResult.confidence * 100)}%
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
            <div>
              <span className="text-slate-500 block">Vendor</span>
              <span className="font-bold text-slate-900">{extractedResult.vendor_name}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Invoice #</span>
              <span className="font-bold text-slate-900">{extractedResult.invoice_number}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Date</span>
              <span className="font-bold text-slate-900">{extractedResult.invoice_date}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Total Audited</span>
              <span className="font-bold text-teal-700">${extractedResult.total?.toFixed(2)}</span>
            </div>
          </div>

          {/* Line items table */}
          {extractedResult.line_items?.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase">
                    <th className="p-2.5">Item Description</th>
                    <th className="p-2.5 text-center">Qty</th>
                    <th className="p-2.5 text-right">Unit Price</th>
                    <th className="p-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {extractedResult.line_items.map((item: any, i: number) => (
                    <tr key={i}>
                      <td className="p-2.5 font-medium text-slate-800">{item.description}</td>
                      <td className="p-2.5 text-center text-slate-600">{item.quantity}</td>
                      <td className="p-2.5 text-right text-slate-600">${item.unit_price?.toFixed(2)}</td>
                      <td className="p-2.5 text-right font-bold text-slate-900">${item.amount?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
