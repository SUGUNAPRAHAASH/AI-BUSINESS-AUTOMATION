import React from "react";

interface ClinicLogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

export default function ClinicLogo({ size = "md", showText = true }: ClinicLogoProps) {
  const iconSize = size === "sm" ? "h-7 w-7" : size === "lg" ? "h-11 w-11" : "h-9 w-9";
  const titleClass = size === "sm" ? "text-sm" : size === "lg" ? "text-lg" : "text-base";
  const subClass = size === "sm" ? "text-[10px]" : "text-[11px]";

  return (
    <div className="flex items-center gap-3 select-none">
      <div className={`relative ${iconSize} shrink-0 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 p-1.5 shadow-md shadow-teal-600/15 flex items-center justify-center text-white ring-2 ring-teal-500/20`}>
        {/* Serene Wellness & Medical SVG Emblem */}
        <svg viewBox="0 0 32 32" fill="none" className="h-full w-full stroke-current" xmlns="http://www.w3.org/2000/svg">
          {/* Medical Shield */}
          <path
            d="M16 3C16 3 25 4.5 25 11C25 19.5 16 27 16 27C16 27 7 19.5 7 11C7 4.5 16 3 16 3Z"
            stroke="white"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="rgba(255, 255, 255, 0.12)"
          />
          {/* Clinical Cross */}
          <path
            d="M16 9V19M11 14H21"
            stroke="white"
            strokeWidth="2.4"
            strokeLinecap="round"
          />
          {/* Delicate Wellness Leaf Accent */}
          <circle cx="20.5" cy="8.5" r="1.5" fill="#a7f3d0" stroke="#a7f3d0" strokeWidth="0.5" />
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col leading-tight">
          <div className={`font-bold tracking-tight text-slate-900 ${titleClass} flex items-center gap-1.5`}>
            <span>BrightSmile</span>
            <span className="font-semibold text-teal-600">Health</span>
          </div>
          <span className={`font-medium text-slate-500 ${subClass}`}>
            Clinical Wellness & AI Hub
          </span>
        </div>
      )}
    </div>
  );
}
