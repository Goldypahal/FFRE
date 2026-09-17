import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  ShieldAlert,
  ShieldCheck,
  GitBranch,
  GitCommit,
  Clock,
  Coins,
  Cpu,
  Play,
  Pause,
  RotateCcw,
  SkipForward,
  SkipBack,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Search,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Layers,
  Sparkles,
  RefreshCw,
  Copy,
  Check,
  Sliders,
  Maximize2,
  Terminal,
} from "lucide-react";
import { api } from "../../lib/api";

interface GraphNode {
  id: string;
  name: string;
  category: "planning" | "retrieval" | "synthesis" | "validation" | "reasoning" | "scoring" | "reporting";
  status: "completed" | "running" | "pending" | "failed" | "warning";
  duration_ms: number;
  tokens: number;
  prompt_version: string;
  dependencies: string[];
  description: string;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
}

interface GraphData {
  investigation_id: string;
  status: string;
  graph_version: string;
  nodes: GraphNode[];
  metrics: {
    total_runtime_ms: number;
    average_node_runtime_ms: number;
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    estimated_cost_usd: number;
    completed_nodes: number;
    total_nodes: number;
  };
}

export function InvestigationDetails() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [investigation, setInvestigation] = useState<any>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // View state
  const [activeTab, setActiveTab] = useState<"dag" | "reasoning" | "attribution" | "confidence" | "logs">("dag");
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isReplaying, setIsReplaying] = useState(false);
  const [replayStep, setReplayStep] = useState<number>(0);
  const [copiedId, setCopiedId] = useState(false);

  // Review decision modal state
  const [reviewModalAction, setReviewModalAction] = useState<"APPROVE" | "REJECT" | "ESCALATE" | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  // Load details & graph topology
  const loadData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const [invRes, graphRes] = await Promise.all([
        api.get<any>(`/investigations/${id}`),
        api.get<GraphData>(`/graph/${id}`).catch(() => null),
      ]);
      setInvestigation(invRes);
      if (graphRes) {
        setGraphData(graphRes);
        setSelectedNode(graphRes.nodes[0] || null);
        setReplayStep(graphRes.nodes.length);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load investigation details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  // Replay timer effect
  useEffect(() => {
    let timer: any;
    if (isReplaying && graphData) {
      timer = setInterval(() => {
        setReplayStep((prev) => {
          if (prev >= graphData.nodes.length) {
            setIsReplaying(false);
            return prev;
          }
          const next = prev + 1;
          setSelectedNode(graphData.nodes[next - 1]);
          return next;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isReplaying, graphData]);

  const handleCopyId = () => {
    if (investigation?.investigation_id) {
      navigator.clipboard.writeText(investigation.investigation_id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  const handleReviewDecision = async () => {
    if (!id || !reviewModalAction) return;
    setSubmittingReview(true);
    try {
      await api.post(`/investigations/${id}/review`, {
        action: reviewModalAction,
        notes: reviewNotes || `Analyst reviewed decision: ${reviewModalAction}`,
      });
      setReviewModalAction(null);
      setReviewNotes("");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Failed to submit review action");
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <RefreshCw size={28} className="text-[#FCD34D] animate-spin" />
        <p className="font-mono text-sm text-[#728299]">Loading LangGraph AI reasoning telemetry...</p>
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="p-8 max-w-xl mx-auto bg-[#0c1a30] border border-red-500/40 rounded-xl text-center space-y-4 my-12">
        <AlertTriangle size={36} className="text-red-400 mx-auto" />
        <h2 className="text-xl font-bold text-white">Investigation Not Found</h2>
        <p className="text-sm text-[#909097]">{error || "Unable to retrieve requested investigation."}</p>
        <button
          onClick={() => navigate("/investigations")}
          className="px-4 py-2 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded text-sm text-[#d8e3fb] transition-colors"
        >
          Return to Queue
        </button>
      </div>
    );
  }

  const riskScore = Number(investigation.risk_score || 0);
  const confidencePct = Math.round(Number(investigation.confidence || 0.85) * 100);

  const getRiskBadge = (score: number) => {
    if (score >= 80) return { label: "CRITICAL RISK", bg: "bg-red-500/20 text-red-400 border-red-500/40" };
    if (score >= 60) return { label: "HIGH RISK", bg: "bg-amber-500/20 text-amber-400 border-amber-500/40" };
    if (score >= 30) return { label: "MEDIUM RISK", bg: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40" };
    return { label: "LOW RISK", bg: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40" };
  };

  const riskMeta = getRiskBadge(riskScore);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 font-sans">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#45464d]/60 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="p-1.5 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded-lg text-[#bec6e0] hover:text-white transition-colors"
          >
            <ArrowLeft size={16} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-[#728299]">CASE:</span>
              <span className="font-mono text-sm font-bold text-white">{investigation.investigation_id}</span>
              <button onClick={handleCopyId} className="text-[#728299] hover:text-[#FCD34D] transition-colors p-0.5">
                {copiedId ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
              </button>
            </div>
            <p className="text-xs text-[#728299] mt-0.5 font-mono">
              Transaction ID: <span className="text-[#bec6e0]">{investigation.transaction_id || "N/A"}</span> • Tenant:{" "}
              <span className="text-[#bec6e0]">{investigation.tenant_id || "default"}</span>
            </p>
          </div>
        </div>

        {/* Action Decision Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setReviewModalAction("APPROVE")}
            className="px-3.5 py-1.5 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/40 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <ShieldCheck size={14} /> Approve Case
          </button>
          <button
            onClick={() => setReviewModalAction("REJECT")}
            className="px-3.5 py-1.5 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/40 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <ShieldAlert size={14} /> Flag Fraud (Reject)
          </button>
          <button
            onClick={() => setReviewModalAction("ESCALATE")}
            className="px-3.5 py-1.5 bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-500/40 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all"
          >
            <AlertTriangle size={14} /> Escalate
          </button>
        </div>
      </div>

      {/* Chapter 31.3: Executive Summary & Confidence Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Risk Score */}
        <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-[#728299] uppercase tracking-wider">Overall Risk</span>
            <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded border ${riskMeta.bg}`}>
              {riskMeta.label}
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-white tracking-tight">{riskScore}</span>
            <span className="text-xs text-[#728299] font-mono">/ 100</span>
          </div>
          <div className="w-full bg-[#111c2d] rounded-full h-1.5 mt-3 overflow-hidden">
            <div
              className={`h-full ${riskScore >= 70 ? "bg-red-500" : riskScore >= 40 ? "bg-amber-500" : "bg-emerald-500"}`}
              style={{ width: `${riskScore}%` }}
            />
          </div>
        </div>

        {/* AI Confidence */}
        <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-[#728299] uppercase tracking-wider">AI Confidence</span>
            <span className="text-[10px] font-mono text-[#FCD34D] bg-[#FCD34D]/10 px-1.5 py-0.5 rounded border border-[#FCD34D]/20">
              BAYESIAN FUSION
            </span>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-bold text-[#FCD34D] tracking-tight">{confidencePct}%</span>
            <span className="text-xs text-[#728299] font-mono">Statistical Certainty</span>
          </div>
          <div className="w-full bg-[#111c2d] rounded-full h-1.5 mt-3 overflow-hidden">
            <div className="h-full bg-[#FCD34D]" style={{ width: `${confidencePct}%` }} />
          </div>
        </div>

        {/* Amount & Transaction */}
        <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-[#728299] uppercase tracking-wider">Transaction Value</span>
            <span className="text-[10px] font-mono text-[#bec6e0]">{investigation.currency || "USD"}</span>
          </div>
          <div className="mt-3">
            <span className="text-3xl font-bold text-white tracking-tight">
              ${Number(investigation.amount || 4250).toLocaleString(undefined, { minimumFractionDigits: 2 })}
            </span>
          </div>
          <p className="text-xs text-[#728299] mt-3 truncate font-mono">
            Merchant: <span className="text-[#bec6e0]">HighRisk Electronics</span>
          </p>
        </div>

        {/* Pipeline Health */}
        <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-[#728299] uppercase tracking-wider">LangGraph Trace</span>
            <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              {investigation.status}
            </span>
          </div>
          <div className="mt-3 flex items-center gap-4 text-xs font-mono text-[#bec6e0]">
            <div className="flex items-center gap-1.5">
              <Clock size={13} className="text-[#728299]" />
              <span>{graphData?.metrics.total_runtime_ms || 1840}ms</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Cpu size={13} className="text-[#728299]" />
              <span>{graphData?.metrics.total_tokens || 4880} tokens</span>
            </div>
          </div>
          <p className="text-[11px] font-mono text-[#728299] mt-3 truncate">
            Est. Cost: <span className="text-[#FCD34D]">${graphData?.metrics.estimated_cost_usd || 0.0098} USD</span>
          </p>
        </div>
      </div>

      {/* Navigation Tabs (Chapters 30 & 31) */}
      <div className="flex items-center border-b border-[#45464d]/60 gap-2 overflow-x-auto custom-scrollbar">
        <button
          onClick={() => setActiveTab("dag")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === "dag"
              ? "border-[#FCD34D] text-[#FCD34D] bg-[#111c2d]/40"
              : "border-transparent text-[#728299] hover:text-[#d8e3fb]"
          }`}
        >
          <GitBranch size={15} /> LangGraph Execution Monitor (Ch 30)
        </button>
        <button
          onClick={() => setActiveTab("reasoning")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === "reasoning"
              ? "border-[#FCD34D] text-[#FCD34D] bg-[#111c2d]/40"
              : "border-transparent text-[#728299] hover:text-[#d8e3fb]"
          }`}
        >
          <Sparkles size={15} /> AI Reasoning Tree (Ch 31.5)
        </button>
        <button
          onClick={() => setActiveTab("attribution")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === "attribution"
              ? "border-[#FCD34D] text-[#FCD34D] bg-[#111c2d]/40"
              : "border-transparent text-[#728299] hover:text-[#d8e3fb]"
          }`}
        >
          <Layers size={15} /> Evidence Attribution & Contradictions (Ch 31.7)
        </button>
        <button
          onClick={() => setActiveTab("confidence")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === "confidence"
              ? "border-[#FCD34D] text-[#FCD34D] bg-[#111c2d]/40"
              : "border-transparent text-[#728299] hover:text-[#d8e3fb]"
          }`}
        >
          <Sliders size={15} /> Confidence Composition (Ch 31.8)
        </button>
        <button
          onClick={() => setActiveTab("logs")}
          className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            activeTab === "logs"
              ? "border-[#FCD34D] text-[#FCD34D] bg-[#111c2d]/40"
              : "border-transparent text-[#728299] hover:text-[#d8e3fb]"
          }`}
        >
          <Terminal size={15} /> Execution Logs (Ch 30.16)
        </button>
      </div>

      {/* TAB 1: CHAPTER 30 - LANGGRAPH EXECUTION MONITOR */}
      {activeTab === "dag" && (
        <div className="space-y-4">
          {/* Controls & Replay Toolbar (Ch 30.5 & 30.15) */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0c1a30] border border-[#45464d] rounded-xl px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-xs font-mono text-[#728299] uppercase tracking-wider">Execution Replay:</span>
              <button
                onClick={() => {
                  if (replayStep >= (graphData?.nodes.length || 0)) setReplayStep(1);
                  setIsReplaying(!isReplaying);
                }}
                className="p-1.5 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded text-[#FCD34D] transition-colors"
                title={isReplaying ? "Pause" : "Play Execution"}
              >
                {isReplaying ? <Pause size={14} /> : <Play size={14} />}
              </button>
              <button
                onClick={() => {
                  setIsReplaying(false);
                  setReplayStep(1);
                  if (graphData?.nodes[0]) setSelectedNode(graphData.nodes[0]);
                }}
                className="p-1.5 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded text-[#bec6e0] transition-colors"
                title="Reset Replay"
              >
                <RotateCcw size={14} />
              </button>
              <button
                onClick={() => {
                  setReplayStep((p) => {
                    const next = Math.min(graphData?.nodes.length || 0, p + 1);
                    if (graphData?.nodes[next - 1]) setSelectedNode(graphData.nodes[next - 1]);
                    return next;
                  });
                }}
                className="p-1.5 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded text-[#bec6e0] transition-colors"
                title="Step Next"
              >
                <SkipForward size={14} />
              </button>
              <span className="text-xs font-mono text-[#bec6e0]">
                Step {replayStep} of {graphData?.nodes.length || 12}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono text-[#728299]">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span> Completed
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-pulse"></span> Running
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#45464d]"></span> Pending
              </span>
            </div>
          </div>

          {/* Main 2-Column Canvas + Inspector */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Interactive DAG Topology Canvas */}
            <div className="lg:col-span-7 bg-[#081425] border border-[#45464d] rounded-xl p-6 min-h-[500px] flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <GitBranch size={16} className="text-[#FCD34D]" />
                  <h3 className="text-sm font-bold text-white uppercase tracking-wider">Active DAG Topology</h3>
                </div>
                <span className="text-xs font-mono text-[#728299] bg-[#111c2d] px-2 py-0.5 rounded border border-[#45464d]/60">
                  {graphData?.graph_version || "v2.4.0-langgraph"}
                </span>
              </div>

              {/* Visual Node Grid */}
              <div className="space-y-6 relative z-10 py-4">
                {/* Level 1: Planner */}
                <div className="flex justify-center">
                  {graphData?.nodes
                    .filter((n) => n.id === "planner")
                    .map((node, idx) => {
                      const isSelected = selectedNode?.id === node.id;
                      const isReached = graphData.nodes.indexOf(node) < replayStep;
                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`w-64 p-3 rounded-lg cursor-pointer border transition-all ${
                            isSelected
                              ? "bg-[#16253d] border-[#FCD34D] shadow-lg shadow-[#FCD34D]/10"
                              : isReached
                              ? "bg-[#0f1d33] border-emerald-500/50 hover:border-emerald-400"
                              : "bg-[#0a1220] border-[#45464d]/40 opacity-50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono text-[#FCD34D] uppercase font-bold">1. Planning</span>
                            <span className="text-[10px] font-mono text-[#bec6e0]">{node.duration_ms}ms</span>
                          </div>
                          <p className="text-xs font-bold text-white mt-1">{node.name}</p>
                          <p className="text-[11px] text-[#728299] truncate mt-0.5">{node.description}</p>
                        </div>
                      );
                    })}
                </div>

                {/* Level 2: Concurrent Retrievers */}
                <div className="text-center">
                  <div className="inline-block px-2 py-0.5 text-[10px] font-mono text-[#728299] uppercase bg-[#111c2d] border border-[#45464d]/40 rounded mb-2">
                    Concurrent Domain Retrievers
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                    {graphData?.nodes
                      .filter((n) => n.category === "retrieval")
                      .map((node) => {
                        const isSelected = selectedNode?.id === node.id;
                        const isReached = (graphData?.nodes.indexOf(node) || 0) < replayStep;
                        return (
                          <div
                            key={node.id}
                            onClick={() => setSelectedNode(node)}
                            className={`p-2.5 rounded-lg cursor-pointer border transition-all text-left ${
                              isSelected
                                ? "bg-[#16253d] border-[#FCD34D] shadow-md shadow-[#FCD34D]/10"
                                : isReached
                                ? "bg-[#0f1d33] border-emerald-500/50 hover:border-emerald-400"
                                : "bg-[#0a1220] border-[#45464d]/40 opacity-50"
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-[9px] font-mono text-cyan-400 uppercase font-bold">Retriever</span>
                              <span className="text-[9px] font-mono text-[#728299]">{node.duration_ms}ms</span>
                            </div>
                            <p className="text-xs font-bold text-white mt-0.5 truncate">{node.name}</p>
                          </div>
                        );
                      })}
                  </div>
                </div>

                {/* Level 3: Fusion & Validation */}
                <div className="grid grid-cols-2 gap-3">
                  {graphData?.nodes
                    .filter((n) => ["evidence_aggregator", "evidence_validator"].includes(n.id))
                    .map((node) => {
                      const isSelected = selectedNode?.id === node.id;
                      const isReached = (graphData?.nodes.indexOf(node) || 0) < replayStep;
                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`p-3 rounded-lg cursor-pointer border transition-all ${
                            isSelected
                              ? "bg-[#16253d] border-[#FCD34D] shadow-lg shadow-[#FCD34D]/10"
                              : isReached
                              ? "bg-[#0f1d33] border-emerald-500/50 hover:border-emerald-400"
                              : "bg-[#0a1220] border-[#45464d]/40 opacity-50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono text-purple-400 uppercase font-bold">Fusion</span>
                            <span className="text-[10px] font-mono text-[#bec6e0]">{node.duration_ms}ms</span>
                          </div>
                          <p className="text-xs font-bold text-white mt-1">{node.name}</p>
                          <p className="text-[11px] text-[#728299] truncate mt-0.5">{node.description}</p>
                        </div>
                      );
                    })}
                </div>

                {/* Level 4: Reasoner & Critic Loop */}
                <div className="grid grid-cols-2 gap-3">
                  {graphData?.nodes
                    .filter((n) => ["reasoner", "critic"].includes(n.id))
                    .map((node) => {
                      const isSelected = selectedNode?.id === node.id;
                      const isReached = (graphData?.nodes.indexOf(node) || 0) < replayStep;
                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`p-3 rounded-lg cursor-pointer border transition-all ${
                            isSelected
                              ? "bg-[#16253d] border-[#FCD34D] shadow-lg shadow-[#FCD34D]/10"
                              : isReached
                              ? "bg-[#0f1d33] border-emerald-500/50 hover:border-emerald-400"
                              : "bg-[#0a1220] border-[#45464d]/40 opacity-50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono text-amber-400 uppercase font-bold">Reasoning</span>
                            <span className="text-[10px] font-mono text-[#bec6e0]">{node.tokens} tokens</span>
                          </div>
                          <p className="text-xs font-bold text-white mt-1">{node.name}</p>
                          <p className="text-[11px] text-[#728299] truncate mt-0.5">{node.description}</p>
                        </div>
                      );
                    })}
                </div>

                {/* Level 5: Final Scoring & Reporting */}
                <div className="grid grid-cols-2 gap-3">
                  {graphData?.nodes
                    .filter((n) => ["confidence_calculator", "reporter"].includes(n.id))
                    .map((node) => {
                      const isSelected = selectedNode?.id === node.id;
                      const isReached = (graphData?.nodes.indexOf(node) || 0) < replayStep;
                      return (
                        <div
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`p-3 rounded-lg cursor-pointer border transition-all ${
                            isSelected
                              ? "bg-[#16253d] border-[#FCD34D] shadow-lg shadow-[#FCD34D]/10"
                              : isReached
                              ? "bg-[#0f1d33] border-emerald-500/50 hover:border-emerald-400"
                              : "bg-[#0a1220] border-[#45464d]/40 opacity-50"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-mono text-emerald-400 uppercase font-bold">Conclusion</span>
                            <span className="text-[10px] font-mono text-[#bec6e0]">{node.duration_ms}ms</span>
                          </div>
                          <p className="text-xs font-bold text-white mt-1">{node.name}</p>
                          <p className="text-[11px] text-[#728299] truncate mt-0.5">{node.description}</p>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>

            {/* Chapter 30.6: Node Inspector Panel */}
            <div className="lg:col-span-5 bg-[#0c1a30] border border-[#45464d] rounded-xl p-5 flex flex-col justify-between font-sans">
              {selectedNode ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-base font-bold text-white">{selectedNode.name}</h4>
                        <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 rounded font-bold">
                          {selectedNode.status}
                        </span>
                      </div>
                      <p className="text-xs text-[#728299] font-mono mt-0.5">Node ID: {selectedNode.id}</p>
                    </div>
                    <span className="text-xs font-mono text-[#FCD34D] bg-[#111c2d] px-2 py-1 rounded border border-[#45464d]">
                      {selectedNode.prompt_version}
                    </span>
                  </div>

                  {/* Node Metrics */}
                  <div className="grid grid-cols-2 gap-2 bg-[#081425] p-3 rounded-lg border border-[#45464d]/40 text-xs font-mono">
                    <div>
                      <span className="text-[#728299]">Execution Time:</span>
                      <p className="text-white font-bold">{selectedNode.duration_ms} ms</p>
                    </div>
                    <div>
                      <span className="text-[#728299]">Tokens Ingested:</span>
                      <p className="text-white font-bold">{selectedNode.tokens} tokens</p>
                    </div>
                  </div>

                  {/* Description */}
                  <div>
                    <span className="text-xs font-mono text-[#728299] uppercase">Node Role:</span>
                    <p className="text-xs text-[#bec6e0] mt-1 leading-relaxed">{selectedNode.description}</p>
                  </div>

                  {/* Inputs State */}
                  <div>
                    <span className="text-xs font-mono text-[#728299] uppercase">Input State & Arguments:</span>
                    <pre className="bg-[#081425] border border-[#45464d]/40 rounded-lg p-3 text-[11px] font-mono text-[#d8e3fb] overflow-x-auto mt-1 custom-scrollbar">
                      {JSON.stringify(selectedNode.inputs || { investigation_id: id }, null, 2)}
                    </pre>
                  </div>

                  {/* Outputs State */}
                  <div>
                    <span className="text-xs font-mono text-[#728299] uppercase">Generated Inference / Output:</span>
                    <pre className="bg-[#081425] border border-[#45464d]/40 rounded-lg p-3 text-[11px] font-mono text-emerald-400 overflow-x-auto mt-1 custom-scrollbar">
                      {JSON.stringify(selectedNode.outputs || { status: "SUCCESS" }, null, 2)}
                    </pre>
                  </div>
                </div>
              ) : (
                <div className="text-center py-20 text-xs font-mono text-[#728299]">
                  Select a node from the DAG topology to inspect telemetry.
                </div>
              )}

              <div className="pt-4 border-t border-[#45464d]/60 mt-4 flex items-center justify-between text-[11px] font-mono text-[#728299]">
                <span>Dependency Graph: {selectedNode?.dependencies.join(", ") || "None (Root)"}</span>
                <span className="text-emerald-400">Deterministic Run</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CHAPTER 31.5 - AI REASONING TREE */}
      {activeTab === "reasoning" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Deductive Hierarchy Tree */}
          <div className="lg:col-span-7 bg-[#0c1a30] border border-[#45464d] rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Sparkles size={16} className="text-[#FCD34D]" /> Deductive Reasoning Hierarchy
              </h3>
              <span className="text-xs font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/30">
                VERDICT: SUSPECTED ATO FRAUD
              </span>
            </div>

            {/* Tree Nodes */}
            <div className="space-y-3 font-sans">
              {/* Branch 1 */}
              <div className="bg-[#081425] border border-[#45464d] rounded-lg p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-400"></span>
                    <span className="text-sm font-bold text-white">1. Hardware & Device Anomaly</span>
                  </div>
                  <span className="text-xs font-mono text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded">
                    Impact: +30 Risk (98% Conf)
                  </span>
                </div>
                <p className="text-xs text-[#bec6e0] leading-relaxed pl-4 border-l-2 border-red-500/40">
                  Request originated from an unrecognized hardware profile (iPhone 15 Pro, fingerprint hash{" "}
                  <code className="text-[#FCD34D] font-mono">hash-999-new</code>) with zero historical association to this
                  checking account.
                </p>
              </div>

              {/* Branch 2 */}
              <div className="bg-[#081425] border border-[#45464d] rounded-lg p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-red-400"></span>
                    <span className="text-sm font-bold text-white">2. Impossible Travel Physics Violation</span>
                  </div>
                  <span className="text-xs font-mono text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded">
                    Impact: +25 Risk (96% Conf)
                  </span>
                </div>
                <p className="text-xs text-[#bec6e0] leading-relaxed pl-4 border-l-2 border-red-500/40">
                  Physical travel velocity violation: Client IP localized to London, UK only 22 minutes after an in-person
                  card swipe occurred in Manhattan, New York (3,400+ miles delta).
                </p>
              </div>

              {/* Branch 3 */}
              <div className="bg-[#081425] border border-[#45464d] rounded-lg p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                    <span className="text-sm font-bold text-white">3. Velocity & Authentication Bypass</span>
                  </div>
                  <span className="text-xs font-mono text-amber-400 font-bold bg-amber-500/10 px-2 py-0.5 rounded">
                    Impact: +20 Risk (92% Conf)
                  </span>
                </div>
                <p className="text-xs text-[#bec6e0] leading-relaxed pl-4 border-l-2 border-amber-500/40">
                  Three consecutive failed biometric challenge attempts immediately followed by emergency SMS OTP fallback
                  to an out-of-region carrier proxy.
                </p>
              </div>

              {/* Branch 4 */}
              <div className="bg-[#081425] border border-[#45464d] rounded-lg p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-yellow-400"></span>
                    <span className="text-sm font-bold text-white">4. High-Risk Merchant Vector</span>
                  </div>
                  <span className="text-xs font-mono text-yellow-400 font-bold bg-yellow-500/10 px-2 py-0.5 rounded">
                    Impact: +15 Risk (89% Conf)
                  </span>
                </div>
                <p className="text-xs text-[#bec6e0] leading-relaxed pl-4 border-l-2 border-yellow-500/40">
                  Transaction destination is categorized under high-risk crypto off-ramping with a chargeback volatility
                  index of 0.85.
                </p>
              </div>
            </div>
          </div>

          {/* Chapter 31.4: AI Recommendation & Natural Language Synthesis */}
          <div className="lg:col-span-5 bg-[#0c1a30] border border-[#45464d] rounded-xl p-5 flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Automated Synthesized Report</h4>
                <span className="text-xs font-mono text-[#FCD34D]">AI Pipeline v2.4</span>
              </div>
              <div className="mt-4 p-4 bg-[#081425] border-l-4 border-[#FCD34D] rounded-r-lg space-y-3">
                <p className="text-xs font-mono text-[#FCD34D] uppercase font-bold">Investigator Summary:</p>
                <p className="text-xs text-[#d8e3fb] leading-relaxed italic">
                  "{investigation.report ||
                    "The alignment of device spoofing markers and geolocation hopping suggests a high-probability account takeover (ATO) scenario. Concurrence of 3 failed authentications and impossible transatlantic travel validates freezing funds."}"
                </p>
              </div>
            </div>

            <div className="p-4 bg-[#081425] border border-[#45464d] rounded-lg space-y-3">
              <span className="text-xs font-mono text-[#728299] uppercase">Required Protocol Action:</span>
              <p className="text-xs text-white font-medium">
                Recommendation: Freeze transaction funds and request mandatory live video-KYC re-verification.
              </p>
              <div className="flex items-center gap-2 pt-2">
                <button
                  onClick={() => setReviewModalAction("REJECT")}
                  className="w-full py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/40 rounded text-xs font-bold transition-all"
                >
                  Confirm Reject & Freeze
                </button>
                <button
                  onClick={() => setReviewModalAction("APPROVE")}
                  className="w-full py-2 bg-[#111c2d] hover:bg-[#1a293f] text-[#bec6e0] border border-[#45464d] rounded text-xs font-bold transition-all"
                >
                  Override & Approve
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: EVIDENCE ATTRIBUTION & CONTRADICTION VIEWER (Ch 31.7, 31.9) */}
      {activeTab === "attribution" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Corroborating Signals */}
            <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
                <h4 className="text-sm font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                  <CheckCircle2 size={16} /> Corroborating Evidential Vectors (4)
                </h4>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                  ALIGNED
                </span>
              </div>
              <div className="space-y-2.5">
                {[
                  {
                    claim: "Session established from foreign IP subnet",
                    source: "location_evidence",
                    hash: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                  },
                  {
                    claim: "Hardware fingerprint never seen on customer account",
                    source: "device_evidence",
                    hash: "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
                  },
                  {
                    claim: "Transaction velocity spike exceeded 300% 7-day average",
                    source: "transaction_evidence",
                    hash: "ca978112ca1bbdcafac231b39a23dc4da7860814964f70994c6a99292a115a35",
                  },
                  {
                    claim: "Merchant has active high-risk chargeback rating",
                    source: "merchant_evidence",
                    hash: "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
                  },
                ].map((item, idx) => (
                  <div key={idx} className="p-3 bg-[#081425] border border-[#45464d]/50 rounded-lg space-y-1">
                    <p className="text-xs font-medium text-white">{item.claim}</p>
                    <div className="flex items-center justify-between text-[10px] font-mono text-[#728299] pt-1">
                      <span>Source: {item.source}</span>
                      <span className="truncate max-w-[180px]">SHA-256: {item.hash.slice(0, 16)}...</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Contradiction Matrix (Ch 31.9) */}
            <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
                <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                  <AlertTriangle size={16} /> Contradiction Matrix & Conflicts (1)
                </h4>
                <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">
                  CONFLICT DETECTED
                </span>
              </div>
              <div className="p-4 bg-[#081425] border border-amber-500/30 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Customer KYC Credential vs Geolocation</span>
                  <span className="text-[10px] font-mono text-amber-400">Conflict Score: 0.72</span>
                </div>
                <p className="text-xs text-[#bec6e0] leading-relaxed">
                  Customer account status is marked as <strong className="text-emerald-400 font-mono">VERIFIED</strong>{" "}
                  with clean 4-year tenure in New York, yet the current transaction initiated with an unauthenticated
                  session token from an IP registered to an anonymous hosting provider in London.
                </p>
                <div className="pt-2 text-[11px] font-mono text-[#FCD34D] border-t border-[#45464d]/40">
                  Critic Resolution: Weight shifted toward hardware & telemetry markers.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: CONFIDENCE COMPOSITION BREAKDOWN (Ch 31.8) */}
      {activeTab === "confidence" && (
        <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Confidence Composition Breakdown (Ch 31.8)
              </h3>
              <p className="text-xs text-[#728299] mt-0.5 font-mono">
                Multivariate weighted statistical attribution of the overall {confidencePct}% confidence score.
              </p>
            </div>
            <span className="text-xs font-mono text-[#FCD34D] bg-[#111c2d] px-2.5 py-1 rounded border border-[#45464d]">
              Total Weight: 100%
            </span>
          </div>

          <div className="space-y-4">
            {[
              {
                category: "Device Intelligence & Fingerprinting",
                weight: 35,
                score: 98,
                color: "bg-red-500",
                desc: "Evaluates emulator indicators, OS spoofing, and canvas fingerprint deviation.",
              },
              {
                category: "Geolocation & Impossible Travel Physics",
                weight: 25,
                score: 96,
                color: "bg-amber-500",
                desc: "Measures geodesic travel velocity and VPN/datacenter egress IPs.",
              },
              {
                category: "Authentication Flow & Velocity Spikes",
                weight: 20,
                score: 92,
                color: "bg-yellow-500",
                desc: "Analyzes rapid retries, credential stuffing signatures, and OTP bypass.",
              },
              {
                category: "Merchant Risk Category & Counterparty Graphs",
                weight: 15,
                score: 89,
                color: "bg-purple-500",
                desc: "Assesses merchant historical chargeback rating and fraud clustering.",
              },
              {
                category: "Customer Profile & Baseline Verification",
                weight: 5,
                score: 75,
                color: "bg-blue-500",
                desc: "Accounts for customer age of account and historical average spend.",
              },
            ].map((v, i) => (
              <div key={i} className="p-4 bg-[#081425] border border-[#45464d]/50 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">{v.category}</span>
                  <div className="flex items-center gap-3 font-mono text-xs">
                    <span className="text-[#728299]">Contribution: {v.weight}%</span>
                    <span className="text-[#FCD34D] font-bold">Signal Score: {v.score}/100</span>
                  </div>
                </div>
                <div className="w-full bg-[#111c2d] rounded-full h-2 overflow-hidden">
                  <div className={`h-full ${v.color}`} style={{ width: `${v.score}%` }} />
                </div>
                <p className="text-[11px] text-[#728299]">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: EXECUTION LOGS (Ch 30.16) */}
      {activeTab === "logs" && (
        <div className="bg-[#081425] border border-[#45464d] rounded-xl p-5 space-y-3 font-mono">
          <div className="flex items-center justify-between border-b border-[#45464d]/60 pb-3">
            <div className="flex items-center gap-2 text-white text-xs font-bold uppercase">
              <Terminal size={15} className="text-[#FCD34D]" />
              <span>Immutable Execution & Audit Log Stream</span>
            </div>
            <span className="text-xs text-[#728299]">{(investigation.audit_logs || []).length} Entries</span>
          </div>

          <div className="max-h-96 overflow-y-auto custom-scrollbar space-y-1.5 text-xs">
            {(investigation.audit_logs || []).map((l: any, idx: number) => (
              <div
                key={idx}
                className="flex items-start justify-between p-2 bg-[#0c1a30] hover:bg-[#111c2d] rounded border border-[#45464d]/30 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="text-[#728299] shrink-0 text-[10px]">
                    {l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : "00:00:00"}
                  </span>
                  <span className="px-1.5 py-0.5 text-[10px] rounded font-bold uppercase bg-[#1a293f] text-[#FCD34D] border border-[#FCD34D]/20 shrink-0">
                    {l.action}
                  </span>
                  <span className="text-[#bec6e0]">{l.details || l.action}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review Decision Confirmation Modal */}
      {reviewModalAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#0c1a30] border border-[#45464d] rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              {reviewModalAction === "APPROVE" ? (
                <ShieldCheck size={18} className="text-emerald-400" />
              ) : reviewModalAction === "REJECT" ? (
                <ShieldAlert size={18} className="text-red-400" />
              ) : (
                <AlertTriangle size={18} className="text-amber-400" />
              )}
              Confirm Analyst Decision: {reviewModalAction}
            </h3>
            <p className="text-xs text-[#bec6e0] leading-relaxed">
              You are recording an immutable analyst determination for Case{" "}
              <span className="font-mono text-white">{investigation.investigation_id}</span>. This action will update the
              case disposition, generate compliance audit logs, and trigger notification webhooks.
            </p>

            <div>
              <label className="block text-xs font-mono text-[#728299] uppercase mb-1">
                Analyst Rationalization / Notes:
              </label>
              <textarea
                rows={3}
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                placeholder="Provide clinical audit justification for decision..."
                className="w-full bg-[#081425] border border-[#45464d] rounded-lg p-2.5 text-xs text-white placeholder:text-[#728299] focus:outline-none focus:border-[#FCD34D]"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setReviewModalAction(null)}
                className="px-4 py-2 bg-[#111c2d] hover:bg-[#1a293f] border border-[#45464d] rounded text-xs text-[#bec6e0] font-semibold transition-colors"
              >
                Cancel
              </button>
              <button
                disabled={submittingReview}
                onClick={handleReviewDecision}
                className="px-4 py-2 bg-[#FCD34D] hover:bg-amber-400 text-black rounded text-xs font-bold transition-all disabled:opacity-50"
              >
                {submittingReview ? "Submitting..." : "Submit Decision"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}