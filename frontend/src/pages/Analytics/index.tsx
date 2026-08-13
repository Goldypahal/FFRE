import React, { useState, useEffect } from "react";

export function Analytics() {
  const [metrics, setMetrics] = useState([
    { label: "Total Investigations", value: "12,450", change: "+12%", changeType: "increase", icon: "👥" },
    { label: "Avg Resolution Time", value: "4.2 days", change: "-8%", changeType: "decrease", icon: "⏱️" },
    { label: "Escalation Rate", value: "15.3%", change: "+3%", changeType: "increase", icon: "⚡" },
    { label: "False Positive Rate", value: "8.7%", change: "-2.1%", changeType: "decrease", icon: "🛡️" },
    { label: "Automation Efficiency", value: "72%", change: "+5%", changeType: "increase", icon: "🤖" }
  ]);

  const [chartData, setChartData] = useState({
    investigationVolume: [
      { month: "Jan", value: 120 },
      { month: "Feb", value: 135 },
      { month: "Mar", value: 98 },
      { month: "Apr", value: 150 },
      { month: "May", value: 200 },
      { month: "Jun", value: 175 }
    ],
    riskDistribution: [
      { range: "Low", count: 45 },
      { range: "Medium", count: 30 },
      { range: "High", count: 15 },
      { range: "Critical", count: 10 }
    ],
    geoHeatmap: [
      { region: "North America", value: 35 },
      { region: "Europe", value: 25 },
      { region: "Asia", value: 20 },
      { region: "Latin America", value: 15 },
      { region: "Middle East", value: 5 }
    ]
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
          <div className="mb-12 text-center">
            <h1 className="font-display-lg text-display-lg text-on-surface mb-4">Analytics Dashboard</h1>
            <p className="font-body-lg text-body-lg text-on-surface-variant max-w-3xl mx-auto">
              Monitor key performance indicators, investigation trends, and operational metrics to optimize your fraud prevention strategy.
            </p>
          </div>

          {/* Key Metrics */}
          <div className="mb-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {metrics.map((metric, index) => (
              <div
                key={index}
                className="bg-surface-container-low border border-outline-variant rounded-xl p-6 flex flex-col items-center text-center hover:border-on-surface-variant transition-colors"
              >
                <div className="text-2xl font-bold mb-2">{metric.icon}</div>
                <div className="text-on-surface font-medium mb-1">{metric.value}</div>
                <p className="font-label-sm text-label-sm text-on-surface-variant">{metric.label}</p>
                <span className={`px-2 py-0.5 text-xs font-mono rounded ${
                  metric.changeType === "increase" ? "bg-risk-low/20 text-risk-low" : "bg-risk-high/20 text-risk-high"
                }`}>
                  {metric.change}
                </span>
              </div>
            ))}
          </div>

          {/* Charts Section */}
          <section className="mb-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Investigation Volume Chart */}
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6">
              <h3 className="font-headline-md text-headline-md text-on-surface mb-4">Investigation Volume Trend</h3>
              <div className="h-40 bg-surface-container-highest rounded-lg flex items-center justify-center">
                <div className="text-on-surface-variant">Line chart showing monthly investigation volume</div>
              </div>
              <p className="mt-2 text-center text-on-surface-variant text-sm">
                Shows the number of investigations opened each month over the past 6 months.
              </p>
            </div>

            {/* Risk Distribution Chart */}
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6">
              <h3 className="font-headline-md text-headline-md text-on-surface mb-4">Risk Distribution</h3>
              <div className="h-40 bg-surface-container-highest rounded-lg flex items-center justify-center">
                <div className="text-on-surface-variant">Pie chart showing risk level distribution</div>
              </div>
              <p className="mt-2 text-center text-on-surface-variant text-sm">
                Breakdown of investigations by risk severity: Low, Medium, High, Critical.
              </p>
            </div>

            {/* Geographic Heatmap */}
            <div className="bg-surface-container-low border border-outline-variant rounded-xl p-6">
              <h3 className="font-headline-md text-headline-md text-on-surface mb-4">Geographic Heatmap</h3>
              <div className="h-40 bg-surface-container-highest rounded-lg flex items-center justify-center">
                <div className="text-on-surface-variant">World map showing investigation density by region</div>
              </div>
              <p className="mt-2 text-center text-on-surface-variant text-sm">
                Visual representation of investigation origins across global regions.
              </p>
            </div>
          </section>

          {/* Recent Activity */}
          <section className="mb-12">
            <h3 className="font-headline-md text-headline-md text-on-surface mb-4">Recent Investigation Activity</h3>
            <div className="bg-surface-container-low border border-outline-variant rounded-xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-min	border-collapse">
                  <thead>
                    <tr className="bg-surface-container-high">
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Investigation ID</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Type</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Risk Level</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Status</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Opened</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Duration</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left">Alerts</th>
                      <th className="p-4 font-label-sm text-label-sm text-on-surface-variant uppercase text-left text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                      <tr key={i} className="hover:bg-surface-container-high transition-colors">
                        <td className="p-4 text-on-surface-variant font-mono">INV-{1000 + i}</td>
                        <td className="p-4 text-on-surface">
                          {["Transaction Fraud", "Identity Theft", "Money Laundering", "Cyber Fraud"][i % 4]}
                        </td>
                        <td className="p-4">
                          <span className={`px-2 py-0.5 text-xs font-mono rounded ${
                            ["Low", "Medium", "High", "Critical"][i % 4] === "Low" ? "bg-risk-low/20 text-risk-low" :
                            ["Low", "Medium", "High", "Critical"][i % 4] === "Medium" ? "bg-risk-medium/20 text-risk-medium" :
                            ["Low", "Medium", "High", "Critical"][i % 4] === "High" ? "bg-risk-high/20 text-risk-high" : "bg-risk-high/20 text-risk-high"
                          }`}>
                            {["Low", "Medium", "High", "Critical"][i % 4]}
                          </span>
                        </td>
                        <td className="p-4 text-on-surface">
                          {["Pending", "Investigating", "Escalated", "Completed"][i % 4]}
                        </td>
                        <td className="p-4 text-on-surface">2024-06-{10 + i}</td>
                        <td className="p-4 text-on-surface">{i}d {i * 2}h</td>
                        <td className="p-4 text-on-surface">{i * 3}</td>
                        <td className="p-4 text-right">
                          <button className="px-3 py-1 bg-on-surface text-background hover:bg-primary transition-colors font-sm">
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
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