"use client";

import { useState } from "react";
import { Menu } from "lucide-react";
import Sidebar from "./Sidebar";
import ClinicLogo from "./ClinicLogo";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex flex-col md:flex-row h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-800">
      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200/80 shrink-0 z-20">
        <ClinicLogo size="sm" />
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors border border-slate-200"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      </header>

      {/* Fixed Sticky Sidebar */}
      <Sidebar
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Area: Independently scrollable, preventing sidebar from moving */}
      <main className="flex-1 min-w-0 h-screen overflow-y-auto bg-[#f8fafc] flex flex-col">
        {children}
      </main>
    </div>
  );
}
