import React, { useState } from "react";
import { cn } from "../../lib/utils";

export interface DatePickerProps {
  onChange?: (range: { start: string | null; end: string | null }) => void;
  placeholder?: string;
  className?: string;
}

export function DatePicker({ onChange, placeholder, className }: DatePickerProps) {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value || null;
    setStart(e.target.value);
    onChange?.({ start: val, end: end || null });
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value || null;
    setEnd(e.target.value);
    onChange?.({ start: start || null, end: val });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <input
        type="date"
        value={start}
        onChange={handleStartChange}
        className="flex h-10 w-full rounded-md border border-glass-border bg-neutral-900 px-3 py-2 text-sm text-text-primary focus:outline-none"
        placeholder={placeholder}
      />
      <span className="text-text-secondary text-xs">to</span>
      <input
        type="date"
        value={end}
        onChange={handleEndChange}
        className="flex h-10 w-full rounded-md border border-glass-border bg-neutral-900 px-3 py-2 text-sm text-text-primary focus:outline-none"
        placeholder={placeholder}
      />
    </div>
  );
}
