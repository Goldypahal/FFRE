import React, { useState, useEffect, useMemo } from "react";
import { api } from "../../lib/api";
import { useAuthStore } from "../../store/useAuthStore";
import { Button } from "../../components/ui/Button";

interface ReportItem {
  report_id: string;
  tenant_id: string;
  investigation_id?: string;
  title: string;
  report_type: string;
  generated_by: string;
  status: string;
  file_format: string;
  file_size: number;
  description?: string;
  created_at: string;
}

export function Reports() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");

  // Modal State
  const [isNewReportModalOpen, setIsNewReportModalOpen] = useState(false);
  const [selectedReportForView, setSelectedReportForView] = useState<ReportItem | null>(null);

  // Form State
  const [newTitle, setNewTitle] = useState("");
  const [newType, setNewType] = useState("Investigation Report");
  const [newFormat, setNewFormat] = useState("pdf");
  const [newInvId, setNewInvId] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Notification State
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  function notify(type: "success" | "error", message: string) {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 4000);
  }

  async function loadReports() {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter !== "All") params.append("status", statusFilter);
      if (typeFilter !== "All") params.append("report_type", typeFilter);
      if (searchTerm.trim()) params.append("search", searchTerm.trim());

      const res = await api.get<{ reports: ReportItem[]; total: number }>(
        `/reports?${params.toString()}`
      );
      setReports(res.reports || []);
    } catch (err: any) {
      console.error("Failed to load reports", err);
      notify("error", err.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, [statusFilter, typeFilter, searchTerm]);

  async function handleCreateReport(e: React.FormEvent) {
    e.preventDefault();
    try {
      setSubmitting(true);
      const created = await api.post<ReportItem>("/reports/generate", {
        title: newTitle.trim(),
        report_type: newType,
        investigation_id: newInvId.trim() || undefined,
        description: newDesc.trim() || undefined,
        file_format: newFormat,
      });

      setReports((prev) => [created, ...prev]);
      notify("success", `Report "${created.title}" successfully generated`);
      setIsNewReportModalOpen(false);
      setNewTitle("");
      setNewDesc("");
      setNewInvId("");
    } catch (err: any) {
      notify("error", err.message || "Failed to generate report");
    } finally {
      setSubmitting(false);
    }
  }

  function handleExport(report: ReportItem) {
    const token = useAuthStore.getState().token || localStorage.getItem("ffre_token") || "";
    const apiBase = import.meta.env.VITE_API_BASE_URL || "/api/v1";
    const url = `${apiBase}/reports/${report.report_id}/download?format=${report.file_format}`;

    // Fetch with auth to download blob
    fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => {
        if (!res.ok) throw new Error("Download failed");
        return res.blob();
      })
      .then((blob) => {
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `report_${report.report_id}.${report.file_format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        notify("success", `Exported ${report.title} (${report.file_format.toUpperCase()})`);
      })
      .catch((err) => {
        notify("error", err.message || "Failed to download report");
      });
  }

  async function handleDelete(reportId: string) {
    if (!window.confirm("Are you sure you want to delete this report?")) return;
    try {
      await api.delete(`/reports/${reportId}`);
      setReports((prev) => prev.filter((r) => r.report_id !== reportId));
      notify("success", "Report deleted successfully");
      if (selectedReportForView?.report_id === reportId) {
        setSelectedReportForView(null);
      }
    } catch (err: any) {
      notify("error", err.message || "Failed to delete report");
    }
  }

  function formatSize(bytes: number) {
    if (!bytes || bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  const completedCount = useMemo(() => reports.filter((r) => r.status === "Completed").length, [reports]);
  const sarCount = useMemo(() => reports.filter((r) => r.report_type.includes("SAR")).length, [reports]);
  const failedCount = useMemo(() => reports.filter((r) => r.status === "Failed").length, [reports]);

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
            <span className="text-amber-400 text-2xl">📊</span>
            <h1 className="text-2xl font-bold tracking-tight text-white">Compliance & Regulatory Reports</h1>
            <span className="px-2 py-0.5 rounded text-xs font-mono bg-amber-500/10 text-amber-400 border border-amber-500/20">
              FINCEN SAR & AUDIT READY
            </span>
          </div>
          <p className="text-sm text-slate-400 max-w-2xl">
            Generate, schedule, and export automated FinCEN Suspicious Activity Reports (SAR), daily fraud summaries, and executive audit dossiers.
          </p>
        </div>

        <Button
          className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold gap-2 shadow-lg shadow-amber-500/20"
          onClick={() => setIsNewReportModalOpen(true)}
        >
          <span>➕</span>
          <span>Generate New Report</span>
        </Button>
      </div>

      {/* Controls and Filters */}
      <div className="bg-slate-900/60 backdrop-blur border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">🔍</span>
          <input
            type="text"
            className="w-full bg-slate-950 border border-slate-700/80 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-400"
            placeholder="Search by title, type, or ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="flex flex-wrap gap-3 w-full md:w-auto items-center">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Status:</span>
            <select
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-amber-400"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="All">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="Failed">Failed</option>
              <option value="Generating">Generating</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Type:</span>
            <select
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-amber-400"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="All">All Types</option>
              <option value="SAR Regulatory Filing">SAR Regulatory Filing</option>
              <option value="Investigation Report">Investigation Report</option>
              <option value="Compliance Report">Compliance Report</option>
              <option value="Trend Report">Trend Report</option>
            </select>
          </div>
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950 text-slate-400 font-mono uppercase">
                <th className="p-4">Report Title</th>
                <th className="p-4">Type</th>
                <th className="p-4">Author / Engine</th>
                <th className="p-4">Status</th>
                <th className="p-4">Generated Date</th>
                <th className="p-4">File Size</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></div>
                      <span>Retrieving reports index...</span>
                    </div>
                  </td>
                </tr>
              ) : reports.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-12 text-center text-slate-400">
                    No reports found matching your criteria. Try adjusting filters or click "Generate New Report".
                  </td>
                </tr>
              ) : (
                reports.map((report) => (
                  <tr key={report.report_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-4">
                      <div className="font-semibold text-slate-100 text-sm mb-0.5">{report.title}</div>
                      {report.description && (
                        <div className="text-slate-400 text-xs truncate max-w-sm">{report.description}</div>
                      )}
                    </td>
                    <td className="p-4 font-mono text-slate-300">
                      <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px]">
                        {report.report_type}
                      </span>
                    </td>
                    <td className="p-4 text-slate-300 font-medium">{report.generated_by}</td>
                    <td className="p-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          report.status === "Completed"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : report.status === "Failed"
                            ? "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {report.status}
                      </span>
                    </td>
                    <td className="p-4 font-mono text-slate-400">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 font-mono text-slate-400">{formatSize(report.file_size)}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-xs border-slate-700 hover:bg-slate-800 text-slate-200 py-1 px-2.5 h-auto"
                          onClick={() => setSelectedReportForView(report)}
                        >
                          View
                        </Button>
                        <Button
                          size="sm"
                          className="text-xs bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-400/30 py-1 px-2.5 h-auto font-mono"
                          onClick={() => handleExport(report)}
                        >
                          PDF Export
                        </Button>
                        <button
                          onClick={() => handleDelete(report.report_id)}
                          className="text-slate-500 hover:text-rose-400 text-xs px-1"
                          title="Delete report"
                        >
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Report Statistics Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold font-mono text-white mb-1">{reports.length}</div>
          <div className="text-xs text-slate-400 font-mono uppercase">Total Reports</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold font-mono text-emerald-400 mb-1">{completedCount}</div>
          <div className="text-xs text-slate-400 font-mono uppercase">Completed & Verified</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold font-mono text-amber-400 mb-1">{sarCount}</div>
          <div className="text-xs text-slate-400 font-mono uppercase">SAR Filings</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold font-mono text-rose-400 mb-1">{failedCount}</div>
          <div className="text-xs text-slate-400 font-mono uppercase">Failed Dispatches</div>
        </div>
      </div>

      {/* New Report Modal */}
      {isNewReportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/60">
              <div className="flex items-center gap-2">
                <span className="text-amber-400">📄</span>
                <h3 className="font-bold text-white text-base">Generate New Report</h3>
              </div>
              <button
                onClick={() => setIsNewReportModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateReport} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Report Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Q3 AML Compliance Audit or SAR Dossier"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Report Type</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-amber-400 outline-none"
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                  >
                    <option value="Investigation Report">Investigation Report</option>
                    <option value="SAR Regulatory Filing">SAR Regulatory Filing</option>
                    <option value="Compliance Report">Compliance Report</option>
                    <option value="Trend Report">Trend Report</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Format</label>
                  <select
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:ring-1 focus:ring-amber-400 outline-none"
                    value={newFormat}
                    onChange={(e) => setNewFormat(e.target.value)}
                  >
                    <option value="pdf">PDF Document (ReportLab)</option>
                    <option value="json">JSON Metadata</option>
                    <option value="html">Interactive HTML</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Investigation ID (Optional linkage)
                </label>
                <input
                  type="text"
                  placeholder="e.g., inv_9876543210"
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                  value={newInvId}
                  onChange={(e) => setNewInvId(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Executive Summary / Scope</label>
                <textarea
                  rows={3}
                  placeholder="Document scope, suspicious activity narrative, or regulatory findings..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:ring-1 focus:ring-amber-400 outline-none"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                ></textarea>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  className="border-slate-700 text-slate-300"
                  onClick={() => setIsNewReportModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold"
                >
                  {submitting ? "Generating..." : "Compile & Generate Report"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Report Detail Modal */}
      {selectedReportForView && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl">
            <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/60">
              <div className="flex items-center gap-2">
                <span className="text-amber-400">📄</span>
                <h3 className="font-bold text-white text-base truncate max-w-md">
                  {selectedReportForView.title}
                </h3>
              </div>
              <button
                onClick={() => setSelectedReportForView(null)}
                className="text-slate-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Report ID</span>
                  <span className="text-amber-300 truncate block">{selectedReportForView.report_id.slice(0, 8)}...</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Type</span>
                  <span className="text-slate-200 truncate block">{selectedReportForView.report_type}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Status</span>
                  <span className="text-emerald-400 block">{selectedReportForView.status}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-500 block">Size</span>
                  <span className="text-slate-200 block">{formatSize(selectedReportForView.file_size)}</span>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2">
                  Executive Findings & Narrative
                </h4>
                <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {selectedReportForView.description || "Comprehensive multi-layered fraud reasoning report compiled automatically by the reasoning engine."}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800 flex justify-between items-center">
                <button
                  onClick={() => handleDelete(selectedReportForView.report_id)}
                  className="text-xs text-rose-400 hover:underline"
                >
                  Delete Report
                </button>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="border-slate-700 text-slate-300 text-xs"
                    onClick={() => setSelectedReportForView(null)}
                  >
                    Close
                  </Button>
                  <Button
                    className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs"
                    onClick={() => handleExport(selectedReportForView)}
                  >
                    Export {selectedReportForView.file_format.toUpperCase()}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}