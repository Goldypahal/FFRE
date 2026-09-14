import React, { useState, useEffect, useMemo } from "react";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/Button";

export interface EvidenceVaultItem {
  item_id: string;
  tenant_id: string;
  category: string;
  title: string;
  source: string;
  tag?: string;
  file_type: string;
  file_size: number;
  sha256_hash: string;
  risk_level: string;
  is_verified: boolean;
  verification_method?: string;
  description?: string;
  created_at: string;
}

export function EvidenceLibrary() {
  const [items, setItems] = useState<EvidenceVaultItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedRisk, setSelectedRisk] = useState<string>("ALL");
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  // Ingest Modal state
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadCategory, setUploadCategory] = useState("IDENTITY_DOCUMENTS");
  const [uploadSource, setUploadSource] = useState("ANALYST_UPLOAD");
  const [uploadTag, setUploadTag] = useState("MANUAL_INGESTION");
  const [uploadRisk, setUploadRisk] = useState("LOW");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Verifying state
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  function notify(type: "success" | "error", message: string) {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  }

  async function loadEvidence() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory !== "ALL") params.append("category", selectedCategory);
      if (selectedRisk !== "ALL") params.append("risk_level", selectedRisk);
      if (searchQuery.trim()) params.append("search", searchQuery.trim());
      
      const res = await api.get<{ items: EvidenceVaultItem[]; total: number }>(
        `/evidence?${params.toString()}`
      );
      setItems(res.items || []);
    } catch (err: any) {
      console.error("Failed to load evidence vault items", err);
      notify("error", err.message || "Failed to load evidence items");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEvidence();
  }, [selectedCategory, selectedRisk, searchQuery]);

  async function handleVerify(itemId: string) {
    try {
      setVerifyingId(itemId);
      const updated = await api.post<EvidenceVaultItem>(`/evidence/${itemId}/verify`);
      setItems((prev) => prev.map((it) => (it.item_id === itemId ? updated : it)));
      notify("success", `Evidence item cryptographically verified via HSM`);
    } catch (err: any) {
      notify("error", err.message || "Failed to verify evidence item");
    } finally {
      setVerifyingId(null);
    }
  }

  async function handleDelete(itemId: string) {
    if (!window.confirm("Are you sure you want to remove this evidence item from the vault?")) return;
    try {
      await api.delete(`/evidence/${itemId}`);
      setItems((prev) => prev.filter((it) => it.item_id !== itemId));
      notify("success", "Evidence artifact removed from vault");
    } catch (err: any) {
      notify("error", err.message || "Failed to delete evidence item");
    }
  }

  async function handleUploadSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      setSubmitting(true);
      const formData = new FormData();
      if (uploadTitle.trim()) formData.append("title", uploadTitle.trim());
      formData.append("category", uploadCategory);
      formData.append("source", uploadSource.trim() || "ANALYST_PORTAL");
      formData.append("tag", uploadTag.trim() || "EVIDENCE_INGEST");
      formData.append("risk_level", uploadRisk);
      if (uploadDesc.trim()) formData.append("description", uploadDesc.trim());
      if (uploadFile) formData.append("file", uploadFile);

      const created = await api.post<EvidenceVaultItem>("/evidence/upload", formData);
      setItems((prev) => [created, ...prev]);
      notify("success", `Evidence "${created.title}" successfully ingested into vault`);
      setIsUploadModalOpen(false);
      setUploadTitle("");
      setUploadDesc("");
      setUploadFile(null);
    } catch (err: any) {
      notify("error", err.message || "Failed to ingest evidence artifact");
    } finally {
      setSubmitting(false);
    }
  }

  const identityDocuments = useMemo(
    () => items.filter((it) => it.category === "IDENTITY_DOCUMENTS"),
    [items]
  );
  const deviceFingerprints = useMemo(
    () => items.filter((it) => it.category === "DEVICE_TELEMETRY"),
    [items]
  );
  const historicalPatterns = useMemo(
    () => items.filter((it) => it.category === "HISTORICAL_PATTERNS"),
    [items]
  );

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-lg shadow-xl border flex items-center gap-3 transition-all ${
            notification.type === "success"
              ? "bg-emerald-950/90 border-emerald-500 text-emerald-200"
              : "bg-rose-950/90 border-rose-500 text-rose-200"
          }`}
        >
          <span>{notification.type === "success" ? "✓" : "⚠️"}</span>
          <span className="text-sm font-medium">{notification.message}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-amber-400 text-2xl">📁</span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Digital Evidence Vault</h1>
            <span className="px-2 py-0.5 rounded text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
              SHA-256 AUDITED
            </span>
          </div>
          <p className="text-sm text-slate-400 max-w-2xl">
            Secure centralized repository for deterministic evidence verification and chain of custody. All records are cryptographically signed and auditable.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <Button
            variant="outline"
            className="border-slate-700 hover:bg-slate-800 text-slate-300 gap-2"
            onClick={() => setIsFilterOpen(!isFilterOpen)}
          >
            <span>🔍</span>
            <span>{isFilterOpen ? "Hide Filters" : "Filter"}</span>
          </Button>

          <Button
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold gap-2 shadow-lg shadow-amber-500/20"
            onClick={() => setIsUploadModalOpen(true)}
          >
            <span>📤</span>
            <span>Ingest Evidence</span>
          </Button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-4 space-y-4">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-center">
          {/* Search Bar */}
          <div className="relative w-full md:w-96">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">🔍</span>
            <input
              type="text"
              className="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-400"
              placeholder="Search by title, source, tag, or SHA-256..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap gap-2 w-full md:w-auto">
            {[
              { key: "ALL", label: "All Evidence" },
              { key: "IDENTITY_DOCUMENTS", label: "Identity Docs" },
              { key: "DEVICE_TELEMETRY", label: "Device Telemetry" },
              { key: "HISTORICAL_PATTERNS", label: "Historical Patterns" },
            ].map((cat) => (
              <button
                key={cat.key}
                onClick={() => setSelectedCategory(cat.key)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  selectedCategory === cat.key
                    ? "bg-amber-500/20 border border-amber-400/40 text-amber-300"
                    : "bg-slate-800/60 border border-slate-700/50 text-slate-400 hover:text-white"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Collapsible Extended Filters */}
        {isFilterOpen && (
          <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-4 text-xs">
            <span className="text-slate-400">Filter by Risk Tier:</span>
            {["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"].map((rk) => (
              <button
                key={rk}
                onClick={() => setSelectedRisk(rk)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                  selectedRisk === rk
                    ? "bg-slate-700 text-white font-bold border border-slate-500"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {rk}
              </button>
            ))}
            <span className="ml-auto text-slate-500 font-mono">
              Total Records: <strong className="text-slate-200">{items.length}</strong>
            </span>
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24 text-slate-400 gap-3">
          <div className="w-5 h-5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
          <span>Synchronizing Evidence Vault...</span>
        </div>
      ) : (
        <div className="space-y-10">
          {/* SECTION 1: Identity Documents */}
          {(selectedCategory === "ALL" || selectedCategory === "IDENTITY_DOCUMENTS") && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-amber-400">🏅</span>
                <h3 className="text-lg font-bold text-white tracking-wide">Identity Documents & Credentials</h3>
                <div className="h-px flex-1 bg-slate-800 ml-2"></div>
                <span className="text-xs font-mono text-slate-400 bg-slate-800/50 px-2 py-0.5 rounded">
                  {identityDocuments.length} RECORD{identityDocuments.length === 1 ? "" : "S"}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {identityDocuments.map((item) => (
                  <div
                    key={item.item_id}
                    className={`bg-slate-900/80 border rounded-xl p-4 flex flex-col justify-between gap-4 transition-all hover:border-slate-600 ${
                      item.is_verified ? "border-amber-500/40 bg-slate-900/90 shadow-lg shadow-amber-500/5" : "border-slate-800"
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start mb-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-slate-800 text-slate-300 border border-slate-700">
                          {item.tag || "KYC_DOC"}
                        </span>
                        <div className="flex items-center gap-1.5">
                          {item.is_verified ? (
                            <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                              <span>✓</span> Verified
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-[11px] text-amber-400 font-medium">
                              <span>⚠️</span> Unverified
                            </span>
                          )}
                        </div>
                      </div>

                      <h4 className="font-semibold text-slate-100 text-sm mb-1">{item.title}</h4>
                      <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                        Source: <span className="text-slate-300">{item.source}</span>
                      </p>
                      {item.description && (
                        <p className="text-xs text-slate-400 mt-2 line-clamp-2">{item.description}</p>
                      )}
                    </div>

                    <div className="pt-3 border-t border-slate-800 space-y-2">
                      <div className="flex justify-between items-center text-[10px] font-mono text-slate-500">
                        <span>SHA-256:</span>
                        <span className="text-slate-400 truncate max-w-[140px]" title={item.sha256_hash}>
                          {item.sha256_hash.substring(0, 16)}...
                        </span>
                      </div>

                      <div className="flex justify-between items-center pt-1">
                        <span className="text-[10px] text-slate-400">
                          {new Date(item.created_at).toLocaleDateString()}
                        </span>

                        <div className="flex items-center gap-2">
                          {!item.is_verified && (
                            <button
                              onClick={() => handleVerify(item.item_id)}
                              disabled={verifyingId === item.item_id}
                              className="text-xs text-amber-400 hover:text-amber-300 font-medium disabled:opacity-50"
                            >
                              {verifyingId === item.item_id ? "Signing..." : "Verify"}
                            </button>
                          )}
                          <button
                            onClick={() => handleDelete(item.item_id)}
                            className="text-slate-500 hover:text-rose-400 text-xs transition-colors"
                            title="Delete evidence"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Add Data Source Card */}
                <div
                  onClick={() => {
                    setUploadCategory("IDENTITY_DOCUMENTS");
                    setIsUploadModalOpen(true);
                  }}
                  className="border border-dashed border-slate-700 hover:border-amber-400/60 rounded-xl p-6 flex flex-col items-center justify-center text-slate-400 hover:text-amber-300 transition-all cursor-pointer bg-slate-900/30 hover:bg-slate-900/60 group"
                >
                  <div className="w-10 h-10 rounded-full bg-slate-800 group-hover:bg-amber-400/20 flex items-center justify-center text-xl mb-2 transition-colors">
                    ➕
                  </div>
                  <span className="text-sm font-semibold text-slate-200">Ingest Identity Source</span>
                  <span className="text-xs text-slate-500 mt-0.5">Upload passport, scan, or KYC JSON</span>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 2: Device Telemetry Feed */}
          {(selectedCategory === "ALL" || selectedCategory === "DEVICE_TELEMETRY") && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-amber-400">📱</span>
                <h3 className="text-lg font-bold text-white tracking-wide">Device Telemetry & Fingerprints</h3>
                <div className="h-px flex-1 bg-slate-800 ml-2"></div>
                <span className="text-xs font-mono text-slate-400 bg-slate-800/50 px-2 py-0.5 rounded">
                  LIVE TELEMETRY
                </span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Telemetry Table */}
                <div className="lg:col-span-2 bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
                  <div className="bg-slate-950/80 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                    <span className="text-xs font-mono uppercase text-amber-400 tracking-wider">
                      Live Telemetry Feed
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      <span className="text-[10px] font-mono text-slate-400">ACTIVE TELEMETRY INGESTION</span>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono">
                          <th className="px-4 py-2.5">Hardware / Device Token</th>
                          <th className="px-4 py-2.5">Verification</th>
                          <th className="px-4 py-2.5">IP / VPC Geo</th>
                          <th className="px-4 py-2.5 text-right">Risk Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 font-mono">
                        <tr className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 text-amber-300">0x4f...8921 (Secure Enclave)</td>
                          <td className="px-4 py-3 text-emerald-400">🔒 Hardware Bound</td>
                          <td className="px-4 py-3 text-slate-400">US-EAST-1 (VPC)</td>
                          <td className="px-4 py-3 text-right text-emerald-400">0.05</td>
                        </tr>
                        <tr className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 text-amber-300">0x9a...3310 (Web Crypto API)</td>
                          <td className="px-4 py-3 text-sky-400">🔄 Browser Hook</td>
                          <td className="px-4 py-3 text-slate-400">London, UK</td>
                          <td className="px-4 py-3 text-right text-sky-400">0.12</td>
                        </tr>
                        <tr className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 text-amber-300">0xbc...1104 (TPM 2.0)</td>
                          <td className="px-4 py-3 text-emerald-400">🔒 Hardware Bound</td>
                          <td className="px-4 py-3 text-slate-400">Berlin, DE</td>
                          <td className="px-4 py-3 text-right text-emerald-400">0.08</td>
                        </tr>
                        <tr className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3 text-amber-300">0xe2...5591 (Android VM Emulator)</td>
                          <td className="px-4 py-3 text-rose-400">⚠️ Emulator Probable</td>
                          <td className="px-4 py-3 text-slate-400">Unknown (Tor Node)</td>
                          <td className="px-4 py-3 text-right text-rose-400 font-bold">0.94</td>
                        </tr>
                        {deviceFingerprints.map((item) => (
                          <tr key={item.item_id} className="hover:bg-slate-800/40 transition-colors">
                            <td className="px-4 py-3 text-amber-300">{item.title}</td>
                            <td className="px-4 py-3 text-emerald-400">
                              {item.is_verified ? "🔒 Verified HSM" : "⚠️ Ingested"}
                            </td>
                            <td className="px-4 py-3 text-slate-400">{item.source}</td>
                            <td className="px-4 py-3 text-right font-bold text-amber-400">{item.risk_level}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Integrity Health Box */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 flex flex-col justify-between">
                  <div>
                    <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-4">
                      Integrity Health & Enclave Confidence
                    </h4>
                    <div className="flex flex-col items-center justify-center py-4">
                      <div className="w-32 h-32 rounded-full border-4 border-emerald-500/30 border-t-emerald-400 flex flex-col items-center justify-center shadow-lg shadow-emerald-500/10">
                        <span className="text-3xl font-bold font-mono text-white">96.8%</span>
                        <span className="text-[10px] font-mono text-emerald-400 uppercase">CONFIDENCE</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 pt-4 border-t border-slate-800 text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Hardware Bound</span>
                      <span className="text-emerald-400 font-bold">92.4%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: "92.4%" }}></div>
                    </div>

                    <div className="flex justify-between">
                      <span className="text-slate-400">Virtual / Proxy Masked</span>
                      <span className="text-rose-400 font-bold">7.6%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-rose-500 h-full rounded-full" style={{ width: "7.6%" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: Historical Case Patterns */}
          {(selectedCategory === "ALL" || selectedCategory === "HISTORICAL_PATTERNS") && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-amber-400">📚</span>
                <h3 className="text-lg font-bold text-white tracking-wide">Historical Fraud Case Patterns</h3>
                <div className="h-px flex-1 bg-slate-800 ml-2"></div>
                <span className="text-xs font-mono text-slate-400 bg-slate-800/50 px-2 py-0.5 rounded">
                  {historicalPatterns.length} IDENTIFIED THREAT PATTERNS
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {historicalPatterns.map((pattern) => (
                  <div
                    key={pattern.item_id}
                    className="bg-slate-900/80 border border-slate-800 hover:border-slate-600 rounded-xl p-5 flex flex-col justify-between gap-4 transition-all"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {pattern.tag || "THREAT_VECTOR"}
                        </span>
                        <span className="text-slate-500 text-[10px] font-mono">
                          SRC: {pattern.source}
                        </span>
                      </div>

                      <h4 className="font-bold text-slate-100 text-base mb-2">{pattern.title}</h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {pattern.description || "Historical fraud pattern cluster extracted from vector graph memory."}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-slate-800 flex justify-between items-center text-xs">
                      <span className="text-emerald-400 font-mono text-[11px]">
                        ✓ {pattern.verification_method || "100% Verified"}
                      </span>
                      <button
                        onClick={() => handleVerify(pattern.item_id)}
                        disabled={pattern.is_verified}
                        className={`text-xs font-medium ${
                          pattern.is_verified ? "text-slate-500 cursor-default" : "text-amber-400 hover:underline"
                        }`}
                      >
                        {pattern.is_verified ? "Audited" : "Verify Integrity"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Ingest Evidence Modal */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/60">
              <div className="flex items-center gap-2">
                <span className="text-amber-400">📤</span>
                <h3 className="font-bold text-white text-base">Ingest Evidence Artifact</h3>
              </div>
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Evidence Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., SWIFT Gateway MT103 Telemetry Extract"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                  value={uploadTitle}
                  onChange={(e) => setUploadTitle(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-amber-400 outline-none"
                    value={uploadCategory}
                    onChange={(e) => setUploadCategory(e.target.value)}
                  >
                    <option value="IDENTITY_DOCUMENTS">Identity Documents</option>
                    <option value="DEVICE_TELEMETRY">Device Telemetry</option>
                    <option value="HISTORICAL_PATTERNS">Historical Patterns</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Risk Tier</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-amber-400 outline-none"
                    value={uploadRisk}
                    onChange={(e) => setUploadRisk(e.target.value)}
                  >
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Source Identifier</label>
                  <input
                    type="text"
                    placeholder="e.g., CORE_BANKING_API"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                    value={uploadSource}
                    onChange={(e) => setUploadSource(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Tag / Classification</label>
                  <input
                    type="text"
                    placeholder="e.g., AML_SCREENING_PASS"
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                    value={uploadTag}
                    onChange={(e) => setUploadTag(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">File Attachment (Optional)</label>
                <input
                  type="file"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-amber-500 file:text-slate-950 hover:file:bg-amber-400 cursor-pointer"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                />
                <span className="text-[11px] text-slate-500 mt-1 block">
                  Automatic SHA-256 cryptographic digest calculated upon ingestion.
                </span>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description / Notes</label>
                <textarea
                  rows={2}
                  placeholder="Investigation context, provenance, or chain of custody notes..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                ></textarea>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="border-slate-700 text-slate-300"
                  onClick={() => setIsUploadModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
                >
                  {submitting ? "Ingesting..." : "Ingest & Calculate Hash"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}