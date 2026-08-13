import React from "react";
import { cn } from "../../lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "gold";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-[#0f172a] text-[#bec6e0] border border-[#45464d]",
    secondary: "bg-[#1f2a3c] text-[#c6c6cd]",
    destructive: "bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 font-bold",
    success: "bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 font-bold",
    warning: "bg-[#F59E0B]/15 text-[#F59E0B] border border-[#F59E0B]/30 font-bold",
    gold: "bg-[#FCD34D]/15 text-[#FCD34D] border border-[#FCD34D]/30 font-bold",
    outline: "border border-[#45464d] text-[#d8e3fb]",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded px-2.5 py-0.5 text-xs font-mono font-medium transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };

