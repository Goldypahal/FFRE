import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../components/ui/Button";
import { api } from "../../lib/api";

interface InvestigationItem {
  investigation_id: string;
  transaction_id: string;
  status: string;
  confidence?: number;
  customer_name?: string;
  amount?: number;
  currency?: string;
  risk_score?: number;
  created_at?: string;
}

export function Investigations() {
  const [investigations, setInvestigations] = useState<InvestigationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");

  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newTransactionId, setNewTransactionId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadInvestigations() {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      if (statusFilter !== "ALL") {
        queryParams.append("status", statusFilter);
      }
      if (searchQuery.trim()) {
        queryParams.append("txn_id", searchQuery.trim());
      }
      const url = queryParams.toString() ? `/investigations?${queryParams.toString()}` : "/investigations";
      const data = await api.get<{ investigations: InvestigationItem[] }>(url);
      setInvestigations(data.investigations || []);
    } catch (err) {
      console.error("Failed to load investigations", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadInvestigations();
  }, [statusFilter, searchQuery]);

  async function handleCreateInvestigation(e: React.FormEvent) {
    e.preventDefault();
    if (!newTransactionId.trim()) return;
    try {
      setSubmitting(true);
      setError(null);
      await api.post("/investigations", {
        transaction_id: newTransactionId.trim(),
        user_id: "user_1",
      });
      setIsCreateDialogOpen(false);
      setNewTransactionId("");
      loadInvestigations();
    } catch (err: any) {
      setError(err.message || "Failed to start investigation.");
    } finally {
      setSubmitting(false);
    }
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "RUNNING":
        return <span className="px-2 py-1 text-xs font-mono bg-blue-500/20 text-blue-400 rounded-full">
          <span className="w-2 h-2 inline-block bg-blue-400 rounded-full mr-1"></span> Running
        </span>;
      case "COMPLETED":
        return <span className="px-2 py-1 text-xs font-mono bg-emerald-500/20 text-emerald-400 rounded-full">
          Completed
        </span>;
      case "ESCALATED":
        return <span className="px-2 py-1 text-xs font-mono bg-amber-500/20 text-amber-400 rounded-full">
          Escalated
        </span>;
      case "CLOSED_APPROVE":
        return <span className="px-2 py-1 text-xs font-mono bg-emerald-500/20 text-emerald-400 rounded-full">
          Approved
        </span>;
      case "CLOSED_REJECT":
        return <span className="px-2 py-1 text-xs font-mono bg-rose-500/20 text-rose-400 rounded-full">
          Rejected
        </span>;
      case "FAILED":
        return <span className="px-2 py-1 text-xs font-mono bg-rose-500/20 text-rose-500 rounded-full">
          Failed
        </span>;
      default:
        return <span className="px-2 py-1 text-xs font-mono bg-gray-500/20 text-gray-400 rounded-full">
          {status}
        </span>;
    }
  }

  return (
    <>
      {/* Header (same as other pages) */}
      <header className="bg-surface dark:bg-surface flex justify-between items-center h-16 w-full px-margin border-b border-outline-variant fixed top-0 z-50">
        <div className="flex items-center gap-stack-md">
          <span className="font-headline-md text-headline-md font-bold text-investment-gold tracking-tight">FFIRE</span>
          <div className="hidden md:flex ml-stack-lg gap-gutter h-full items-center">
            <Link to="/" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Dashboard
            </Link>
            <Link to="/investigations" className="text-on-surface hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center font-bold">
              Investigation Queue
            </Link>
            <Link to="/analytics" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Analytics
            </Link>
            <Link to="/reports" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Reports
            </Link>
          </div>
        </div>
        <div className="flex items-center gap-gutter">
          <div className="hidden lg:flex items-center bg-surface-container rounded px-stack-sm py-1 border border-outline-variant">
            <div className="flex items-center">
              <span>🔍</span>
            </div>
            <input className="bg-transparent border-none focus:ring-0 text-sm text-on-surface w-48" placeholder="Quick Search..." type="text"/>
          </div>
          <div className="flex items-center gap-stack-md">
            <div className="flex items-center">
              <span>🔔</span>
            </div>
            <div className="flex items-center">
              <span>⚙️</span>
            </div>
            <div className="w-8 h-8 rounded-full bg-surface-container-high border border-outline-variant overflow-hidden">
              <div className="w-full h-full flex items-center justify-center bg-surface-container-high text-on-surface-variant text-xs">
                AC
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 pb-20 px-margin max-w-container-max mx-auto">
        {/* Page Header */}
        <div className="mb-12">
          <h1 className="font-display-lg text-display-lg text-on-surface mb-4">Investigations Queue</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-3xl mx-auto">
            Monitor and manage active investigations. View real-time status, risk scores, and initiate new analyses.
          </p>
        </div>

        {/* Controls and Filters */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex flex-col md:flex-row md:items-start md:gap-4 w-full md:w-auto">
            <div className="flex-1 md:w-48">
              <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Search Investigations</label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
                  <span>🔍</span>
                </div>
                <input
                  className="w-full pl-10 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
                  placeholder="Search by transaction ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
            <div className="flex-1 md:w-48">
              <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Filter by Status</label>
              <select
                className="w-full pl-4 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="RUNNING">Running</option>
                <option value="COMPLETED">Completed</option>
                <option value="ESCALATED">Escalated</option>
                <option value="CLOSED_APPROVE">Approved</option>
                <option value="CLOSED_REJECT">Rejected</option>
                <option value="FAILED">Failed</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCreateDialogOpen(true)}
              className="px-4 py-2 bg-investment-gold text-surface font-semibold rounded hover:opacity-90 transition-all"
            >
              New Investigation
            </button>
          </div>
        </div>

        {/* Investigations Table */}
        <div className="bg-surface-container-low rounded-xl border border-outline-variant overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-surface-container-high">
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">ID</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Transaction ID</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Risk Score</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Amount</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Customer</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Created</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {loading && investigations.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-on-surface-variant">
                      Loading investigations...
                    </td>
                  </tr>
                ) : investigations.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="p-8 text-center text-on-surface-variant">
                      No investigations found. Try adjusting your filters or creating a new investigation.
                    </td>
                  </tr>
                ) : (
                  investigations.map((inv) => (
                    <tr key={inv.investigation_id} className="hover:bg-surface-container-high transition-colors">
                      <td className="p-4 text-on-surface-variant font-mono">{inv.investigation_id.slice(0, 8)}...</td>
                      <td className="p-4 text-on-surface">{inv.transaction_id}</td>
                      <td className="p-4">{getStatusBadge(inv.status)}</td>
                      <td className="p-4 text-on-surface">
                        {inv.risk_score !== undefined ? (
                          <>
                            <span className="font-mono">{inv.risk_score.toFixed(2)}</span>
                            {inv.risk_score >= 0.75 ? (
                              <span className="ml-1 h-2 w-2 rounded-full bg-rose-500 inline-block"></span>
                            ) : inv.risk_score >= 0.5 ? (
                              <span className="ml-1 h-2 w-2 rounded-full bg-amber-500 inline-block"></span>
                            ) : inv.risk_score >= 0.25 ? (
                              <span className="ml-1 h-2 w-2 rounded-full bg-yellow-400 inline-block"></span>
                            ) : (
                              <span className="ml-1 h-2 w-2 rounded-full bg-emerald-500 inline-block"></span>
                            )}
                          </>
                        ) : (
                          <span className="text-on-surface-variant">N/A</span>
                        )}
                      </td>
                      <td className="p-4 text-on-surface">
                        {inv.amount !== undefined && inv.currency !== undefined ? (
                          <>
                            <span className="font-mono">{inv.amount.toLocaleString()}</span>
                            <span className="ml-1 text-xs">{inv.currency}</span>
                          </>
                        ) : (
                          <span className="text-on-surface-variant">N/A</span>
                        )}
                      </td>
                      <td className="p-4 text-on-surface">{inv.customer_name || "N/A"}</td>
                      <td className="p-4 text-on-surface text-sm">
                        {inv.created_at ? (
                          <span className="text-on-surface-variant">{new Date(inv.created_at).toLocaleDateString()}</span>
                        ) : (
                          <span className="text-on-surface-variant">N/A</span>
                        )}
                      </td>
                      <td className="p-4 flex space-x-2">
                        <Link
                          to={`/investigations/${inv.investigation_id}`}
                          className="px-3 py-1 bg-on-surface text-background text-xs font-semibold rounded hover:bg-primary transition-colors"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination placeholder */}
        <div className="mt-6 flex justify-between items-center text-on-surface-variant text-sm">
          <span>Showing {investigations.length} investigations</span>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-surface-container-low border border-outline-variant rounded hover:bg-surface-container-high transition-colors">
              Previous
            </button>
            <button className="px-3 py-1 bg-surface-container-low border border-outline-variant rounded hover:bg-surface-container-high transition-colors">
              Next
            </button>
          </div>
        </div>
      </main>

      {/* Create Investigation Dialog */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-surface-container rounded-xl p-6 w-full max-w-md">
            <h2 className="font-headline-md text-headline-md text-on-surface mb-4">Start New Investigation</h2>
            <p className="text-on-surface-variant mb-6">
              Enter a transaction ID to begin an AI-powered fraud investigation.
            </p>
            <form onSubmit={handleCreateInvestigation} className="space-y-4">
              <div>
                <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Transaction ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. T-101, T-102"
                  value={newTransactionId}
                  onChange={(e) => setNewTransactionId(e.target.value)}
                  className="w-full pl-4 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
                />
              </div>
              {error && (
                <div className="pt-2 text-xs text-rose-500 bg-rose-500/10 border border-rose-500/30 rounded-lg p-3">
                  {error}
                </div>
              )}
              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    setNewTransactionId("");
                    setError(null);
                  }}
                  className="px-4 py-2 bg-surface-container-low text-on-surface-variant hover:bg-surface-container-high transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className={`px-4 py-2 bg-investment-gold text-surface font-semibold rounded hover:opacity-90 transition-all ${
                    submitting ? "opacity-50 cursor-not-allowed" : ""
                  }`}
                >
                  {submitting ? "Creating..." : "Start Investigation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}