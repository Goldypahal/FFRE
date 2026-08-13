import { Database, Search, ExternalLink } from "lucide-react";
import { Badge } from "../ui/Badge";

export interface EvidenceItem {
  id: string;
  source: string;
  type: "document" | "transaction" | "database" | "external";
  snippet: string;
  relevanceScore: number;
}

interface EvidenceExplorerProps {
  evidence: EvidenceItem[];
}

export function EvidenceExplorer({ evidence }: EvidenceExplorerProps) {
  return (
    <div className="flex flex-col gap-4 h-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-medium text-white">Evidence Retrieved</h3>
        <Badge variant="secondary">{evidence.length} sources</Badge>
      </div>

      <div className="flex-1 overflow-auto space-y-4 pr-2">
        {evidence.map((item) => (
          <div key={item.id} className="glass-panel p-4 hover:bg-white/5 transition-colors cursor-pointer group">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-sm font-medium text-text-secondary">
                <Database size={14} className="text-system-blue" />
                {item.source}
              </div>
              <Badge variant={item.relevanceScore > 0.8 ? "warning" : "outline"} className="text-[10px] px-2 py-0">
                {Math.round(item.relevanceScore * 100)}% match
              </Badge>
            </div>
            
            <p className="text-sm text-white leading-relaxed line-clamp-3 mb-3">
              "{item.snippet}"
            </p>
            
            <div className="flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-xs text-text-tertiary uppercase tracking-wider">{item.type}</span>
              <button className="text-xs text-system-blue hover:text-blue-400 flex items-center gap-1">
                View Source <ExternalLink size={12} />
              </button>
            </div>
          </div>
        ))}

        {evidence.length === 0 && (
          <div className="flex flex-col items-center justify-center h-48 text-text-tertiary">
            <Search size={32} className="mb-2 opacity-20" />
            <p className="text-sm">No evidence retrieved yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
