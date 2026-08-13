import React from "react";
import { cn } from "../../lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "gold" | "risk-low" | "risk-high";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    
    const baseStyles = "inline-flex items-center justify-center whitespace-nowrap rounded text-sm font-medium transition-all focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50 active:scale-95 cursor-pointer font-label-md";
    
    const variants = {
      default: "bg-[#bec6e0] text-[#283044] hover:opacity-90 font-bold",
      destructive: "bg-[#EF4444] text-white hover:bg-red-600 font-bold",
      outline: "border border-[#45464d] bg-transparent hover:bg-[#1f2a3c] text-[#d8e3fb]",
      secondary: "bg-[#1f2a3c] text-[#d8e3fb] border border-[#45464d] hover:bg-[#2a3548]",
      ghost: "hover:bg-[#1f2a3c] text-[#c6c6cd] hover:text-[#d8e3fb]",
      link: "text-[#bec6e0] underline-offset-4 hover:underline",
      gold: "bg-[#FCD34D] text-[#081425] hover:bg-amber-300 font-bold",
      "risk-low": "bg-[#10B981] text-[#081425] hover:brightness-110 font-bold",
      "risk-high": "bg-[#EF4444] text-white hover:bg-red-600 font-bold",
    };
    
    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-8 rounded px-3 text-xs",
      lg: "h-12 rounded px-8 text-base",
      icon: "h-10 w-10 p-0",
    };

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };

