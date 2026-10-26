"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Users,
  Mail,
  FileText,
  AlertTriangle,
  Send,
  BookOpen,
  Sparkles,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Live AI Chat", href: "/chat", icon: MessageSquare },
  { name: "Patient Leads", href: "/leads", icon: Users },
  { name: "Email Triage", href: "/emails", icon: Mail },
  { name: "Document Extraction", href: "/documents", icon: FileText },
  { name: "Failed Jobs", href: "/failed-jobs", icon: AlertTriangle },
  { name: "Mock Outbox", href: "/outbox", icon: Send },
  { name: "Knowledge Base", href: "/kb", icon: BookOpen },
];

export default function Sidebar() {
  const pathname = usePathname();

  // Hide sidebar when on embeddable /widget page
  if (pathname === "/widget") {
    return null;
  }

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950/80 backdrop-blur-md flex flex-col shrink-0 min-h-screen">
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20">
          <Sparkles className="h-5 w-5 text-slate-950" />
        </div>
        <div>
          <h1 className="font-bold text-base tracking-tight text-white">LeadPilot AI</h1>
          <p className="text-xs text-teal-400 font-medium">BrightSmile Dental Hub</p>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? "bg-teal-500/10 text-teal-400 border border-teal-500/20 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? "text-teal-400" : "text-slate-500"}`} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
        <span>LeadPilot v1.0 • Ops Active</span>
        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
      </div>
    </aside>
  );
}
