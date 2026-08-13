import { CheckCircle2, Clock, Loader2, AlertTriangle } from "lucide-react";
import { cn } from "../../lib/utils";

export interface ExecutionStep {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  time?: string;
  details?: string;
}

interface ExecutionMonitorProps {
  steps: ExecutionStep[];
}

export function ExecutionMonitor({ steps }: ExecutionMonitorProps) {
  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-lg font-medium text-white mb-2">Execution Pipeline</h3>
      <div className="relative border-l border-glass-border ml-3 space-y-6 pb-4">
        {steps.map((step) => (
          <div key={step.id} className="relative pl-6">
            {/* Status Icon Marker */}
            <div className={cn(
              "absolute -left-3 top-0.5 flex h-6 w-6 items-center justify-center rounded-full border bg-bg-surface",
              step.status === "completed" && "border-system-green text-system-green",
              step.status === "running" && "border-system-blue text-system-blue",
              step.status === "pending" && "border-glass-border text-text-tertiary",
              step.status === "failed" && "border-system-red text-system-red"
            )}>
              {step.status === "completed" && <CheckCircle2 size={14} />}
              {step.status === "running" && <Loader2 size={14} className="animate-spin" />}
              {step.status === "pending" && <Clock size={14} />}
              {step.status === "failed" && <AlertTriangle size={14} />}
            </div>
            
            <div className="flex flex-col">
              <div className="flex items-center justify-between">
                <span className={cn(
                  "font-medium text-sm",
                  step.status === "pending" ? "text-text-secondary" : "text-white"
                )}>
                  {step.name}
                </span>
                {step.time && <span className="text-xs text-text-tertiary">{step.time}</span>}
              </div>
              {step.details && (
                <p className="mt-1 text-xs text-text-secondary leading-relaxed">
                  {step.details}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
