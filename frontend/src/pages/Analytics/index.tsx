import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/Button";

interface AnalyticsKPIs {
  total_investigations: number;
  completed_count: number;
  escalated_count: number;
  running_count: number;
  failed_count: number;
  escalation_rate: number;
  automation_efficiency: number;
  avg_confidence: number;
  avg_risk_score: number;
  evidence_vault_count: number;
  reports_count: number;
  avg_resolution_time: string;
}

interface RiskDistributionItem {
  range: string;
  count: number;
  color: string;
}

interface StatusItem {
  status: string;
  count: number;
}

interface VolumeTrendItem {
  month: string;
  value: number;
}

interface GeoHeatmapItem {
  region: string;
  value: number;
}

interface AnalyticsData {
  tenant_id: string;
  kpis: AnalyticsKPIs;
  risk_distribution: RiskDistributionItem[];
  status_breakdown: StatusItem[];
  volume_trend: VolumeTrendItem[];
  geo_heatmap: GeoHeatmapItem[];
}

interface InvestigationSummary {
  investigation_id: string;
  txn_id?: string;
  status: string;
  risk_score?: number;
  confidence?: number;
  created_at: string;
}

export function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [recentInvestigations, setRecentInvestigations] = useState<InvestigationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d" | "1y">("30d");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [hoveredTrendIndex, setHoveredTrendIndex] = useState<number | null>(null);

  const fetchAnalytics = async () => {
    setIsRefreshing(true);
    setError(null);
    try {
      const summary = await api.get<AnalyticsData>("/analytics/summary");
      setData(summary);

      // Fetch recent investigations for live activity stream
      try {
        const invResp = await api.get<{ investigations: InvestigationSummary[] }>("/investigations?limit=8");
        if (invResp && invResp.investigations) {
          setRecentInvestigations(invResp.investigations);
        }
      } catch {
        // Non-critical fallback if investigation table is empty
      }

      setLastUpdated(new Date());
    } catch (err: any) {
      console.error("Failed to load analytics:", err);
      setError(err.message || "Failed to load operational intelligence data");
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-12 h-12 border-4 border-investment-gold border-t-transparent rounded-full animate-spin"></div>
        <p className="text-on-surface-variant font-mono text-sm tracking-wide">
          AGGREGATING OPERATIONAL INTELLIGENCE...
        </p>
      </div>
    );
  }

  const kpis = data?.kpis || {
    total_investigations: 0,
    completed_count: 0,
    escalated_count: 0,
    running_count: 0,
    failed_count: 0,
    escalation_rate: 0,
    automation_efficiency: 0,
    avg_confidence: 0,
    avg_risk_score: 0,
    evidence_vault_count: 0,
    reports_count: 0,
    avg_resolution_time: "0s",
  };

  const volumeTrend = data?.volume_trend || [];
  const maxTrendVal = Math.max(...volumeTrend.map((v) => v.value), 10);
  const totalRiskCount = data?.risk_distribution?.reduce((acc, curr) => acc + curr.count, 0) || 1;

  return (
    <div className="space-y-8 pb-16">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-display-sm font-headline text-on-surface tracking-tight">
              Operational Intelligence
            </h1>
            <span className="px-2.5 py-0.5 text-xs font-mono font-medium rounded-full bg-investment-gold/10 text-investment-gold border border-investment-gold/30">
              Live Aggregations
            </span>
          </div>
          <p className="text-on-surface-variant text-sm mt-1">
            Real-time multi-tenant telemetry, automated triage metrics, and systemic fraud distribution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Time range selector */}
          <div className="inline-flex rounded-lg bg-surface-container p-1 border border-outline-variant text-xs">
            {(["7d", "30d", "90d", "1y"] as const).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 rounded-md font-medium transition-all ${
                  timeRange === range
                    ? "bg-surface-container-high text-investment-gold shadow-sm font-semibold"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {range.toUpperCase()}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={fetchAnalytics}
            disabled={isRefreshing}
            className="flex items-center gap-2 border-outline-variant text-xs"
          >
            <span className={`inline-block ${isRefreshing ? "animate-spin" : ""}`}>🔄</span>
            {isRefreshing ? "Syncing..." : "Refresh"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-risk-high/10 border border-risk-high/30 text-risk-high flex items-center justify-between text-sm">
          <span>{error}</span>
          <Button size="sm" variant="outline" onClick={fetchAnalytics}>
            Retry
          </Button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Investigations */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-5 hover:border-outline-variant transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">Total Pipeline</span>
            <span className="text-lg">📊</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-headline text-on-surface">
              {kpis.total_investigations.toLocaleString()}
            </span>
            <span className="text-xs text-risk-low font-medium">Active Pool</span>
          </div>
          <div className="mt-2 text-xs text-on-surface-variant flex items-center justify-between">
            <span>Completed: {kpis.completed_count}</span>
            <span>Running: {kpis.running_count}</span>
          </div>
        </div>

        {/* Automation Efficiency */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-5 hover:border-outline-variant transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">Automation Rate</span>
            <span className="text-lg">🤖</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-headline text-investment-gold">
              {kpis.automation_efficiency}%
            </span>
            <span className="text-xs text-risk-low font-medium">Autonomous</span>
          </div>
          <div className="mt-2 text-xs text-on-surface-variant">
            Escalation rate: <span className="font-mono text-on-surface">{kpis.escalation_rate}%</span>
          </div>
        </div>

        {/* Confidence & Risk */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-5 hover:border-outline-variant transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">Mean Confidence</span>
            <span className="text-lg">🎯</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-headline text-on-surface">
              {kpis.avg_confidence}%
            </span>
            <span className="text-xs text-investment-gold font-medium">Score: {kpis.avg_risk_score}</span>
          </div>
          <div className="mt-2 text-xs text-on-surface-variant">
            Resolution time: <span className="font-mono text-on-surface">{kpis.avg_resolution_time}</span>
          </div>
        </div>

        {/* Vault & Reports */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-5 hover:border-outline-variant transition-colors shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-wider text-on-surface-variant">Compliance Assets</span>
            <span className="text-lg">🔒</span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold font-headline text-on-surface">
              {kpis.evidence_vault_count + kpis.reports_count}
            </span>
            <span className="text-xs text-risk-low font-medium">Cryptographic</span>
          </div>
          <div className="mt-2 text-xs text-on-surface-variant flex items-center justify-between">
            <span>Evidence: {kpis.evidence_vault_count}</span>
            <span>Reports: {kpis.reports_count}</span>
          </div>
        </div>
      </div>

      {/* Visual Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monthly Volume Trend SVG Chart (2 columns) */}
        <div className="lg:col-span-2 bg-surface-container-low border border-outline-variant/60 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold font-headline text-on-surface">
                  Investigation Trajectory & Volume Trends
                </h3>
                <p className="text-xs text-on-surface-variant">
                  Monthly intake throughput across deterministic verification pipelines
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono text-investment-gold bg-investment-gold/10 px-2.5 py-1 rounded-md border border-investment-gold/20">
                <span>Peak: {maxTrendVal} Cases</span>
              </div>
            </div>

            {/* SVG Visual Chart */}
            <div className="relative mt-6 pt-4 pb-2">
              <svg viewBox="0 0 600 200" className="w-full h-48 overflow-visible">
                <defs>
                  <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#d4af37" stopOpacity="0.35" />
                    <stop offset="100%" stopColor="#d4af37" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Horizontal Guide Lines */}
                {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
                  const y = 180 - ratio * 140;
                  return (
                    <g key={i}>
                      <line
                        x1="30"
                        y1={y}
                        x2="580"
                        y2={y}
                        stroke="currentColor"
                        className="text-outline-variant/30"
                        strokeDasharray="4 4"
                      />
                      <text
                        x="20"
                        y={y + 4}
                        fill="currentColor"
                        className="text-on-surface-variant text-[10px] font-mono"
                        textAnchor="end"
                      >
                        {Math.round(ratio * maxTrendVal)}
                      </text>
                    </g>
                  );
                })}

                {/* Area & Line */}
                {volumeTrend.length > 0 && (() => {
                  const points = volumeTrend.map((item, idx) => {
                    const step = 530 / Math.max(volumeTrend.length - 1, 1);
                    const x = 40 + idx * step;
                    const y = 180 - (item.value / maxTrendVal) * 140;
                    return { x, y, item };
                  });

                  const lineD = points.reduce((acc, p, idx) => {
                    return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
                  }, "");

                  const areaD = `${lineD} L ${points[points.length - 1].x} 180 L ${points[0].x} 180 Z`;

                  return (
                    <>
                      <path d={areaD} fill="url(#trendGradient)" />
                      <path
                        d={lineD}
                        fill="none"
                        stroke="#d4af37"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />

                      {/* Interactive Dots */}
                      {points.map((p, idx) => (
                        <g
                          key={idx}
                          className="cursor-pointer group"
                          onMouseEnter={() => setHoveredTrendIndex(idx)}
                          onMouseLeave={() => setHoveredTrendIndex(null)}
                        >
                          <circle
                            cx={p.x}
                            cy={p.y}
                            r={hoveredTrendIndex === idx ? 6 : 4}
                            fill="#1e1e24"
                            stroke="#d4af37"
                            strokeWidth={hoveredTrendIndex === idx ? 3 : 2}
                            className="transition-all duration-200"
                          />
                          {hoveredTrendIndex === idx && (
                            <g transform={`translate(${p.x}, ${p.y - 12})`}>
                              <rect
                                x="-35"
                                y="-25"
                                width="70"
                                height="22"
                                rx="4"
                                fill="#111827"
                                stroke="#d4af37"
                                strokeWidth="1"
                              />
                              <text
                                x="0"
                                y="-10"
                                fill="#ffffff"
                                fontSize="11"
                                fontWeight="bold"
                                textAnchor="middle"
                                fontFamily="monospace"
                              >
                                {p.item.value} cases
                              </text>
                            </g>
                          )}
                          <text
                            x={p.x}
                            y="198"
                            fill="currentColor"
                            className="text-on-surface-variant text-[11px] font-mono"
                            textAnchor="middle"
                          >
                            {p.item.month}
                          </text>
                        </g>
                      ))}
                    </>
                  );
                })()}
              </svg>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-outline-variant/40 flex items-center justify-between text-xs text-on-surface-variant">
            <span>Deterministic Graph Ingestion Pipeline</span>
            <span className="font-mono">Sync Interval: Realtime</span>
          </div>
        </div>

        {/* Risk Distribution Breakdown */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold font-headline text-on-surface">
              Risk Severity Spectrum
            </h3>
            <p className="text-xs text-on-surface-variant mb-6">
              Distribution of case confidence and threat classification
            </p>

            {/* Segmented Bar */}
            <div className="h-4 w-full rounded-full overflow-hidden flex bg-surface-container-highest">
              {data?.risk_distribution?.map((item, idx) => {
                const pct = ((item.count / totalRiskCount) * 100).toFixed(1);
                return (
                  <div
                    key={idx}
                    style={{ width: `${pct}%`, backgroundColor: item.color }}
                    title={`${item.range}: ${item.count} (${pct}%)`}
                    className="h-full transition-all duration-300 hover:opacity-80"
                  />
                );
              })}
            </div>

            {/* Legend / Counters */}
            <div className="mt-6 space-y-3">
              {data?.risk_distribution?.map((item, idx) => {
                const pct = ((item.count / totalRiskCount) * 100).toFixed(1);
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-surface-container/50 border border-outline-variant/30"
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className="w-3 h-3 rounded-full shrink-0"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-xs font-medium text-on-surface">{item.range}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-mono font-semibold text-on-surface">
                        {item.count}
                      </span>
                      <span className="text-xs font-mono text-on-surface-variant w-12 text-right">
                        {pct}%
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-outline-variant/40 flex items-center justify-between text-xs text-on-surface-variant">
            <span>Automated Scoring Engine</span>
            <span className="font-mono text-investment-gold">ISO-20022</span>
          </div>
        </div>
      </div>

      {/* Second Tier: Status Breakdown & Regional Activity */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Status Breakdown */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-6 shadow-sm">
          <h3 className="text-base font-semibold font-headline text-on-surface mb-1">
            Investigation Status Pipeline
          </h3>
          <p className="text-xs text-on-surface-variant mb-6">
            State distribution of transactions processed through multi-agent arbitration
          </p>

          <div className="space-y-4">
            {data?.status_breakdown?.map((item, idx) => {
              const total = kpis.total_investigations || 1;
              const pct = Math.round((item.count / total) * 100);
              return (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-on-surface font-medium">{item.status}</span>
                    <span className="font-mono text-on-surface-variant">
                      {item.count} cases ({pct}%)
                    </span>
                  </div>
                  <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        item.status.includes("Completed")
                          ? "bg-risk-low"
                          : item.status.includes("Escalated")
                          ? "bg-risk-high"
                          : item.status.includes("Failed")
                          ? "bg-risk-critical"
                          : "bg-investment-gold"
                      }`}
                      style={{ width: `${Math.max(pct, item.count > 0 ? 4 : 0)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Regional Activity */}
        <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-6 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h3 className="text-base font-semibold font-headline text-on-surface">
              Global Geolocation Heatmap
            </h3>
            <span className="text-xs font-mono text-on-surface-variant">Jurisdictions</span>
          </div>
          <p className="text-xs text-on-surface-variant mb-6">
            Cross-border remittance density and geofenced velocity flags
          </p>

          <div className="space-y-4">
            {data?.geo_heatmap?.map((item, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-on-surface font-medium">{item.region}</span>
                  <span className="font-mono text-on-surface-variant">{item.value}% Remittance</span>
                </div>
                <div className="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
                  <div
                    className="h-full bg-investment-gold/80 rounded-full transition-all duration-500"
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Live Recent Investigation Stream */}
      <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="text-base font-semibold font-headline text-on-surface">
              Live Investigation Activity
            </h3>
            <p className="text-xs text-on-surface-variant">
              Recent algorithmic assessments and reasoning traces
            </p>
          </div>
          <Link
            to="/investigations"
            className="text-xs font-mono text-investment-gold hover:underline flex items-center gap-1.5"
          >
            <span>View Full Investigation Queue</span>
            <span>&rarr;</span>
          </Link>
        </div>

        {recentInvestigations.length === 0 ? (
          <div className="text-center py-10 text-on-surface-variant text-sm font-mono">
            No live investigations logged in current tenant context.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-outline-variant/40 text-on-surface-variant font-mono uppercase">
                  <th className="pb-3 font-semibold">Investigation ID</th>
                  <th className="pb-3 font-semibold">Transaction ID</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Risk Score</th>
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20">
                {recentInvestigations.map((inv) => (
                  <tr key={inv.investigation_id} className="hover:bg-surface-container/40 transition-colors">
                    <td className="py-3 font-mono font-medium text-investment-gold">
                      {inv.investigation_id}
                    </td>
                    <td className="py-3 font-mono text-on-surface-variant">
                      {inv.txn_id || "N/A"}
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono ${
                          inv.status === "COMPLETED" || inv.status === "CLOSED_APPROVE"
                            ? "bg-risk-low/20 text-risk-low"
                            : inv.status === "ESCALATED" || inv.status === "WAITING_HUMAN"
                            ? "bg-risk-high/20 text-risk-high"
                            : inv.status === "FAILED"
                            ? "bg-risk-critical/20 text-risk-critical"
                            : "bg-investment-gold/20 text-investment-gold"
                        }`}
                      >
                        {inv.status}
                      </span>
                    </td>
                    <td className="py-3 font-mono">
                      {inv.risk_score !== undefined && inv.risk_score !== null ? (
                        <div className="flex items-center gap-2">
                          <span
                            className={`font-semibold ${
                              inv.risk_score >= 0.7
                                ? "text-risk-high"
                                : inv.risk_score >= 0.35
                                ? "text-risk-medium"
                                : "text-risk-low"
                            }`}
                          >
                            {inv.risk_score.toFixed(2)}
                          </span>
                          <div className="w-14 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                inv.risk_score >= 0.7
                                  ? "bg-risk-high"
                                  : inv.risk_score >= 0.35
                                  ? "bg-risk-medium"
                                  : "bg-risk-low"
                              }`}
                              style={{ width: `${inv.risk_score * 100}%` }}
                            />
                          </div>
                        </div>
                      ) : (
                        <span className="text-on-surface-variant/50">--</span>
                      )}
                    </td>
                    <td className="py-3 text-on-surface-variant">
                      {inv.created_at ? new Date(inv.created_at).toLocaleString() : "Just now"}
                    </td>
                    <td className="py-3 text-right">
                      <Link
                        to={`/investigations/${inv.investigation_id}`}
                        className="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-container-high border border-outline-variant text-on-surface font-medium hover:text-investment-gold transition-colors inline-block"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer Meta */}
      <div className="flex items-center justify-between text-xs text-on-surface-variant font-mono pt-4 border-t border-outline-variant/30">
        <span>Tenant Context: {data?.tenant_id || "default_tenant"}</span>
        <span>Telemetry Stream: Active ({lastUpdated.toLocaleTimeString()})</span>
      </div>
    </div>
  );
}