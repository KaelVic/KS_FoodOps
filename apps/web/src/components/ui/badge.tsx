import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "cyan" | "violet" | "emerald" | "amber" | "crimson"
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantClasses = {
    default: "bg-slate-800 text-slate-300 border-slate-700",
    cyan: "bg-[rgba(0,240,255,0.1)] text-[#00f0ff] border-[rgba(0,240,255,0.3)] shadow-[0_0_10px_rgba(0,240,255,0.2)]",
    violet: "bg-[rgba(168,85,247,0.1)] text-[#c084fc] border-[rgba(168,85,247,0.3)] shadow-[0_0_10px_rgba(168,85,247,0.2)]",
    emerald: "bg-[rgba(16,185,129,0.1)] text-[#34d399] border-[rgba(16,185,129,0.3)] shadow-[0_0_10px_rgba(16,185,129,0.2)]",
    amber: "bg-[rgba(245,158,11,0.1)] text-[#fbbf24] border-[rgba(245,158,11,0.3)] shadow-[0_0_10px_rgba(245,158,11,0.2)]",
    crimson: "bg-[rgba(239,68,68,0.1)] text-[#f87171] border-[rgba(239,68,68,0.3)] shadow-[0_0_10px_rgba(239,68,68,0.2)]",
  }

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  )
}
