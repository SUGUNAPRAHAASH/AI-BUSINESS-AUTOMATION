import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "LeadPilot AI — Virtual Operations Team & Automation Hub",
  description: "Enterprise-grade AI operations, lead capture, email triage, and document automation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="flex bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-teal-500 selection:text-white">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {children}
        </main>
      </body>
    </html>
  );
}
