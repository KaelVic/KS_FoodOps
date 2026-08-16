import * as React from "react"
import { cn } from "@/lib/utils"

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean
  accent?: "none" | "cyan" | "violet" | "emerald" | "amber" | "crimson"
}

export function GlassPanel({
  className,
  hoverEffect = false,
  accent = "none",
  children,
  ...props
}: GlassPanelProps) {
  const accentClasses = {
    none: "",
    cyan: "border-t-[rgba(0,240,255,0.3)] shadow-[inset_0_1px_0_rgba(0,240,255,0.1)]",
    violet: "border-t-[rgba(168,85,247,0.3)] shadow-[inset_0_1px_0_rgba(168,85,247,0.1)]",
    emerald: "border-t-[rgba(16,185,129,0.3)] shadow-[inset_0_1px_0_rgba(16,185,129,0.1)]",
    amber: "border-t-[rgba(245,158,11,0.3)] shadow-[inset_0_1px_0_rgba(245,158,11,0.1)]",
    crimson: "border-t-[rgba(239,68,68,0.3)] shadow-[inset_0_1px_0_rgba(239,68,68,0.1)]",
  }

  return (
    <div
      className={cn(
        "glass-panel rounded-xl overflow-hidden relative",
        hoverEffect && "glass-panel-hover",
        accentClasses[accent],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
