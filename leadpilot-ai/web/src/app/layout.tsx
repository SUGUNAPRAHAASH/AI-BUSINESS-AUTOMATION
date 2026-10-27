import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/AppShell";

export const metadata: Metadata = {
  title: "BrightSmile Health — Clinical Practice & AI Automation Hub",
  description: "Autonomous virtual operations team, multi-doctor scheduling, and clinical communication.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#f8fafc] text-slate-800 antialiased selection:bg-teal-600 selection:text-white">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
