"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  MessageSquare,
  Users,
  Mail,
  FileText,
  AlertTriangle,
  Send,
  BookOpen,
  X,
  ShieldCheck,
} from "lucide-react";
import ClinicLogo from "./ClinicLogo";

const NAV_ITEMS = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Appointments & Calendar", href: "/calendar", icon: Calendar, badge: "Live" },
  { name: "Live AI Chatbot", href: "/chat", icon: MessageSquare },
  { name: "Patient Inquiries", href: "/leads", icon: Users },
  { name: "Email Triage", href: "/emails", icon: Mail },
  { name: "Supply Invoice OCR", href: "/documents", icon: FileText },
  { name: "Failed Jobs", href: "/failed-jobs", icon: AlertTriangle },
  { name: "Activity Logs", href: "/outbox", icon: Send },
  { name: "Knowledge Base", href: "/kb", icon: BookOpen },
];

interface SidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export default function Sidebar({ mobileOpen = false, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();

  // Hide sidebar on widget view
  if (pathname === "/widget") {
    return null;
  }

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-slate-200/80 text-slate-800 select-none shadow-xs">
      {/* Header with Logo */}
      <div className="p-5 border-b border-slate-100 flex items-center justify-between">
        <ClinicLogo size="md" />
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
          Clinic Operations
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onCloseMobile}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-teal-50 text-teal-800 font-semibold border border-teal-200/80 shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon
                  className={`h-4 w-4 shrink-0 transition-colors ${
                    isActive ? "text-teal-600" : "text-slate-400 group-hover:text-slate-600"
                  }`}
                />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-teal-600 text-white tracking-wide uppercase">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Hospital System Status Badge */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/60">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-semibold text-slate-700">Practice Hub Online</span>
          </div>
          <span className="text-[11px] font-medium text-slate-400">Live</span>
        </div>
        <div className="mt-1 text-[11px] text-slate-500 truncate">
          Active: Dr. Sarah • Dr. Alex • Dr. Marcus
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sticky Fixed Sidebar: Stays firmly in place on scroll */}
      <aside className="hidden md:flex w-64 h-screen sticky top-0 shrink-0 flex-col z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-40 md:hidden transition-opacity"
          onClick={onCloseMobile}
        />
      )}

      {/* Mobile Slide-in Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 w-72 max-w-[85vw] bg-white z-50 md:hidden transform transition-transform duration-200 ease-in-out shadow-2xl ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
