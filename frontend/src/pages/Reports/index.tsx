import React, { useState, useEffect } from "react";

export function Reports() {
  const [reports, setReports] = useState([
    {
      id: "rep-001",
      title: "Suspicious Activity Report - INV-78491",
      type: "Investigation Report",
      generatedBy: "System",
      status: "Completed",
      date: "2024-01-16",
      size: "2.4 MB",
      description: "Suspicious Activity Report for investigation INV-78491 detailing potential money laundering activities"
    },
    {
      id: "rep-002",
      title: "Daily Fraud Summary",
      type: "Trend Report",
      generatedBy: "System",
      status: "Completed",
      date: "2024-01-16",
      size: "1.2 MB",
      description: "Daily summary of fraud detection metrics and alerts"
    },
    {
      id: "rep-003",
      title: "Chargeback Analysis Report Q1 2024",
      type: "Compliance Report",
      generatedBy: "Maria Garcia (Analyst)",
      status: "Completed",
      date: "2024-04-01",
      size: "5.8 MB",
      description: "Quarterly analysis of chargeback trends, reasons, and recovery rates"
    },
    {
      id: "rep-004",
      title: "Investigation Timeline Export - INV-78490",
      type: "Investigation Report",
      generatedBy: "Alex Johnson",
      status: "Completed",
      date: "2024-01-16",
      size: "320 KB",
      description: "Complete investigation timeline with evidence and actions for INV-78490"
    },
    {
      id: "rep-005",
      title: "Compliance Report - Regulatory Filing",
      type: "Compliance Report",
      generatedBy: "Compliance Team",
      status: "Failed",
      date: "2024-02-05",
      size: "0 B",
      description: "Monthly regulatory filing for financial transactions"
    }
  ]);

  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");

  const filteredReports = reports.filter(report => {
    const matchesSearch = report.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "All" || report.status === statusFilter;
    const matchesType = typeFilter === "All" || report.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <>
      {/* Header (same as other pages) */}
      <header className="bg-surface dark:bg-surface flex justify-between items-center h-16 w-full px-margin border-b border-outline-variant fixed top-0 z-50">
        <div className="flex items-center gap-stack-md">
          <span className="font-headline-md text-headline-md font-bold text-investment-gold tracking-tight">FFIRE</span>
          <div className="hidden md:flex ml-stack-lg gap-gutter h-full items-center">
            <a href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Dashboard
            </a>
            <a href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Investigation Queue
            </a>
            <a href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Audit Logs
            </a>
            <a href="#" className="text-on-surface-variant hover:text-on-surface transition-colors font-body-md text-body-md h-full flex items-center">
              Reports
            </a>
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
        <div className="mb-8">
          <h1 className="font-display-lg text-display-lg text-on-surface mb-4">Reports</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-3xl mx-auto">
            Generate, manage, and export investigation reports. Track report history and schedule automated reporting.
          </p>
        </div>

        {/* Controls and Filters */}
        <div className="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1 md:w-48">
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Search Reports</label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
                <span>🔍</span>
              </div>
              <input
                className="w-full pl-10 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
                placeholder="Search by title, description, ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex-1 md:w-24">
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Filter by Status</label>
            <select
              className="w-full pl-4 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="All">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="Failed">Failed</option>
              <option value="Generating">Generating</option>
            </select>
          </div>
          <div className="flex-1 md:w-24">
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">Filter by Type</label>
            <select
              className="w-full pl-4 pr-4 py-2 bg-surface-container-low border border-outline-variant rounded-lg text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus:border-investment-gold"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="All">All Types</option>
              <option value="Investigation Report">Investigation Report</option>
              <option value="Compliance Report">Compliance Report</option>
              <option value="Trend Report">Trend Report</option>
              <option value="Custom Report">Custom Report</option>
            </select>
          </div>
          <div className="flex-1 md:w-24">
            <button
              onClick={() => {
                // New report logic would go here
                alert("Create new report functionality would be implemented here");
              }}
              className="w-full py-2 bg-investment-gold text-surface font-semibold rounded hover:opacity-90 transition-all"
            >
              New Report
            </button>
          </div>
        </div>

        {/* Reports Table */}
        <div className="bg-surface-container-low rounded-xl border border-outline-variant overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-surface-container-high">
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Title</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Type</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Generated By</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Date</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Size</th>
                  <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-on-surface-variant">
                      No reports found. Try adjusting your filters or creating a new report.
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((report) => (
                    <tr key={report.id} className="hover:bg-surface-container-high transition-colors">
                      <td className="p-4 text-on-surface">{report.title}</td>
                      <td className="p-4 text-on-surface-variant">{report.type}</td>
                      <td className="p-4 text-on-surface">{report.generatedBy}</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 text-xs font-mono rounded ${
                          report.status === "Completed"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : report.status === "Failed"
                              ? "bg-rose-500/20 text-rose-400"
                              : "bg-amber-500/20 text-amber-400"
                        }`}
                        >
                          {report.status}
                        </span>
                      </td>
                      <td className="p-4 text-on-surface">{report.date}</td>
                      <td className="p-4 text-on-surface">{report.size}</td>
                      <td className="p-4 flex space-x-2">
                        <button
                          onClick={() => {
                            // View report logic
                            alert(`Viewing report: ${report.title}`);
                          }}
                          className="px-3 py-1 bg-on-surface text-background text-xs font-semibold rounded hover:bg-primary transition-colors"
                        >
                          View
                        </button>
                        <button
                          onClick={() => {
                            // Export report logic
                            alert(`Exporting report: ${report.title}`);
                          }}
                          className="px-3 py-1 bg-on-surface text-background text-xs font-semibold rounded hover:bg-primary transition-colors"
                        >
                          Export
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Report Stats Summary */}
        <div className="mt-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex-1">
            <h2 className="font-headline-lg text-headline-lg text-on-surface mb-2">Report Statistics</h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              Track reporting trends and performance metrics.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-on-surface">{reports.length}</div>
              <div className="text-sm text-on-surface-variant">Total Reports</div>
            </div>
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-on-surface">{reports.filter(r => r.status === "Completed").length}</div>
              <div className="text-sm text-on-surface-variant">Successful Reports</div>
            </div>
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-on-surface">{reports.filter(r => r.status === "Failed").length}</div>
              <div className="text-sm text-on-surface-variant">Failed Reports</div>
            </div>
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-on-surface">{reports.filter(r => r.status === "Generated").length}</div>
              <div className="text-sm text-on-surface-variant">Pending Reports</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer (same as other pages) */}
      <footer className="border-t border-outline-variant bg-surface py-12 px-margin mt-12">
        <div className="max-w-container-max mx-auto flex flex-col md:flex-row justify-between items-start gap-stack-lg">
          <div className="max-w-sm">
            <span className="font-headline-md text-headline-md font-bold text-investment-gold mb-4 block">FFIRE</span>
            <p className="text-on-surface-variant text-sm">
              Deterministic Intelligence for the modern financial infrastructure. Precision auditing, human-centered explainability.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-stack-lg">
            <div>
              <h4 className="font-label-md text-label-md text-on-surface mb-4 uppercase">Product</h4>
              <ul className="space-y-2 text-sm text-on-surface-variant">
                <li><a href="#" className="hover:text-primary">Features</a></li>
                <li><a href="#" className="hover:text-primary">LangGraph Docs</a></li>
                <li><a href="#" className="hover:text-primary">Integrations</a></li>
                <li><a href="#" className="hover:text-primary">Pricing</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-label-md text-label-md text-on-surface mb-4 uppercase">Resources</h4>
              <ul className="space-y-2 text-sm text-on-surface-variant">
                <li><a href="#" className="hover:text-primary">Whitepapers</a></li>
                <li><a href="#" className="hover:text-primary">API Reference</a></li>
                <li><a href="#" className="hover:text-primary">Compliance Guide</a></li>
              </ul>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <h4 className="font-label-md text-label-md text-on-surface mb-4 uppercase">Status</h4>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-risk-low animate-pulse"></div>
                <span className="text-sm text-on-surface-variant font-label-sm">FFIRE Engine v2.4 Active</span>
              </div>
            </div>
          </div>
        </div>
        <div className="max-w-container-max mx-auto mt-12 pt-8 border-t border-outline-variant flex justify-between items-center text-xs text-on-surface-variant opacity-60">
          <p>© 2024 FFIRE Intelligence Systems. All rights reserved.</p>
          <div className="flex gap-stack-md">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Security</a>
          </div>
        </div>
      </footer>
    </>
  );
}