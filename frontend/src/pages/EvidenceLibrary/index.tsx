import React, { useState } from "react";

export function EvidenceLibrary() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Sample evidence data - in a real app, this would come from an API
  const identityDocuments = [
    {
      id: "1",
      tag: "KYC_LEVEL_3",
      tagColor: "bg-surface-container-high text-on-surface-variant text-[10px] font-label-md rounded",
      title: "Global Passport Index",
      source: "INTERPOL-API",
      lastUpdate: "2m ago",
      icon: "📋",
      isVerified: true,
      riskLevel: "low"
    },
    {
      id: "2",
      tag: "AML_SCAN",
      tagColor: "bg-surface-container-high text-on-surface-variant text-[10px] font-label-md rounded",
      title: "Sanction Lists",
      source: "OFAC_GOV",
      lastUpdate: "1h ago",
      icon: "⚠️",
      isVerified: false,
      riskLevel: "medium"
    },
    {
      id: "3",
      tag: "BIO_CHECK",
      tagColor: "bg-surface-container-high text-on-surface-variant text-[10px] font-label-md rounded",
      title: "Biometric Hash Vault",
      source: "LOCAL_ENCLAVE",
      lastUpdate: "Just now",
      icon: "👁️",
      isVerified: true,
      riskLevel: "low"
    },
    {
      id: "4",
      tag: "ADD_SOURCE",
      tagColor: "",
      title: "Add Data Source",
      source: "",
      lastUpdate: "",
      icon: "➕",
      isVerified: false,
      riskLevel: "",
      isAddButton: true
    }
  ];

  const deviceFingerprints = [
    // For the device fingerprints category, we'll show the live telemetry feed and integrity health
    // The actual data would come from an API in a real application
  ];

  const historicalPatterns = [
    {
      id: "1",
      title: "Synthetic Identity Chain",
      description: "Cross-matched patterns involving coordinated KYC document tampering across multiple neo-bank domains.",
      type: "HIGH RECURRENCE",
      typeColor: "bg-rose-500/10 text-rose-400 text-[10px] font-bold rounded",
      idNumber: "PAT-0082",
      verification: "100% (Manual Audit)",
      verificationColor: "text-emerald-400",
      actionText: "View Map",
      actionColor: "text-investigation-gold"
    },
    {
      id: "2",
      title: "Velocity Smurfing",
      description: "High-frequency, low-value transactions utilizing recycled mobile hardware fingerprints from APAC regions.",
      type: "EMERGING",
      typeColor: "bg-amber-500/10 text-amber-400 text-[10px] font-bold rounded",
      idNumber: "PAT-0094",
      verification: "82% (AI Logic)",
      verificationColor: "text-amber-400",
      actionText: "Analyze",
      actionColor: "text-investigation-gold"
    },
    {
      id: "3",
      title: "Residential Proxy Tunneling",
      description: "Persistent use of high-reputation residential IPs to mask systematic scraping of credit application endpoints.",
      type: "STABLE THREAT",
      typeColor: "bg-emerald-500/10 text-emerald-400 text-[10px] font-bold rounded",
      idNumber: "PAT-0041",
      verification: "99% (Telemetry)",
      verificationColor: "text-emerald-400",
      actionText: "Drill Down",
      actionColor: "text-investigation-gold"
    }
  ];

  return (
    <div className="bg-background text-on-surface font-body-md min-h-screen flex overflow-hidden dark">
      {/* Sidebar Navigation */}
      <aside className="hidden md:flex flex-col h-full w-64 bg-surface-container-lowest border-r border-outline-variant py-stack-md shrink-0">
        <div className="px-6 mb-8">
          <h1 className="font-headline-md text-headline-md text-on-surface tracking-tight">FFIRE Engine</h1>
          <p className="font-label-md text-label-md text-on-surface-variant opacity-70">V2.4 Active</p>
        </div>
        <nav className="flex-1 space-y-1">
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all cursor-pointer active:scale-95"
            href="#"
          >
            {/* Using div as placeholder for assignment icon */}
            <div className="mr-3 flex items-center">
              <span>📋</span>
            </div>
            <span className="font-label-md text-label-md">Cases</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all cursor-pointer active:scale-95"
            href="#"
          >
            {/* Using div as placeholder for account_tree icon */}
            <div className="mr-3 flex items-center">
              <span>🌳</span>
            </div>
            <span className="font-label-md text-label-md">Reasoning Graph</span>
          </a>
          {/* Active State: Evidence Vault */}
          <a
            className="flex items-center px-6 py-3 bg-primary-container text-primary border-r-4 border-primary transition-all cursor-pointer active:scale-95"
            href="#"
          >
            {/* Using div as placeholder for folder_shared icon with fill */}
            <div className="mr-3 flex items-center">
              <span>📁</span>
            </div>
            <span className="font-label-md text-label-md">Evidence Vault</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all cursor-pointer active:scale-95"
            href="#"
          >
            {/* Using div as placeholder for history icon */}
            <div className="mr-3 flex items-center">
              <span>📜</span>
            </div>
            <span className="font-label-md text-label-md">Historical Patterns</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all cursor-pointer active:scale-95"
            href="#"
          >
            {/* Using div as placeholder for analytics icon */}
            <div className="mr-3 flex items-center">
              <span>📊</span>
            </div>
            <span className="font-label-md text-label-md">System Health</span>
          </a>
        </nav>
        <div className="px-4 mt-auto space-y-4">
          <button
            className="w-full py-3 bg-secondary-container text-on-secondary-container font-label-md text-label-md rounded-lg flex items-center justify-center gap-2 hover:bg-secondary transition-colors"
          >
            {/* Using div as placeholder for plus icon */}
            <div className="flex items-center">
              <span>➕</span>
            </div>
            NEW INVESTIGATION
          </button>
          <div className="pt-4 border-t border-outline-variant">
            <a
              className="flex items-center px-4 py-2 text-on-surface-variant hover:bg-surface-container-low transition-all text-label-sm font-label-sm"
              href="#"
            >
              {/* Using div as placeholder for help icon */}
              <div className="mr-3 flex items-center">
                <span>❓</span>
              </div>
              Documentation
            </a>
            <a
              className="flex items-center px-4 py-2 text-on-surface-variant hover:bg-surface-container-low transition-all text-label-sm font-label-sm"
              href="#"
            >
              {/* Using div as placeholder for contact_support icon */}
              <div className="mr-3 flex items-center">
                <span>🎧</span>
              </div>
              Support
            </a>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="flex justify-between items-center h-16 w-full px-margin bg-surface border-b border-outline-variant shrink-0">
          <div className="flex items-center gap-8">
            <span className="font-headline-md text-headline-md font-bold text-investigation-gold">FFIRE</span>
            <div className="hidden lg:flex gap-6">
              <a
                href="#"
                className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors px-2 py-1"
              >
                Dashboard
              </a>
              <a
                href="#"
                className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors px-2 py-1"
              >
                Investigation Queue
              </a>
              <a
                href="#"
                className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors px-2 py-1"
              >
                Audit Logs
              </a>
              <a
                href="#"
                className="font-body-md text-body-md text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high transition-colors px-2 py-1"
              >
                Reports
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              {/* Using div as placeholder for search icon */}
              <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
                <span>🔍</span>
              </div>
              <input
                className="bg-surface-container-low border border-outline-variant rounded-full pl-10 pr-4 py-1.5 text-body-sm w-64 focus:outline-none focus:ring-1 focus:ring-investigation-gold"
                placeholder="Search Vault..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                type="text"
              />
            </div>
            {/* Using div as placeholder for notifications icon */}
            <div className="relative">
              <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center">
                <span>🔔</span>
              </div>
            </div>
            {/* Using div as placeholder for settings icon */}
            <div className="relative">
              <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center">
                <span>⚙️</span>
              </div>
            </div>
            {/* User profile image */}
            <div className="w-8 h-8 rounded-full bg-surface-container-highest overflow-hidden border border-outline-variant">
              <div className="w-full h-full flex items-center justify-center bg-surface-container-high text-on-surface-variant text-xs">
                AC
              </div>
            </div>
          </div>
        </header>

        {/* Canvas / Content Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-margin">
          {/* Page Header */}
          <div className="mb-8 flex justify-between items-end">
            <div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface mb-2">Evidence Vault</h2>
              <p className="font-body-md text-body-md text-on-surface-variant max-w-2xl">
                Secure centralized repository for deterministic evidence verification. All records are cryptographically signed and auditable.
              </p>
            </div>
            <div className="flex gap-3">
              <button
                className="flex items-center gap-2 px-4 py-2 border border-outline text-on-surface font-label-md text-label-md hover:bg-surface-container-high transition-colors rounded"
              >
                {/* Using div as placeholder for filter icon */}
                <div className="flex items-center">
                  <span>🔍</span>
                </div>
                Filter
              </button>
              <button
                className="flex items-center gap-2 px-4 py-2 bg-primary text-on-primary font-label-md text-label-md hover:opacity-90 transition-colors rounded"
              >
                {/* Using div as placeholder for upload icon */}
                <div className="flex items-center">
                  <span>📤</span>
                </div>
                Ingest Evidence
              </button>
            </div>
          </div>

          {/* Bento Grid of Categories */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter">
            {/* Category Section: Identity Documents */}
            <div className="md:col-span-12">
              <div className="flex items-center gap-3 mb-4">
                {/* Using div as placeholder for badge icon */}
                <div className="flex items-center">
                  <span>🏅</span>
                </div>
                <h3 className="font-headline-md text-headline-md">Identity Documents</h3>
                <div className="h-px flex-1 bg-outline-variant ml-4"></div>
                <span className="font-label-sm text-label-sm text-on-surface-variant">12,482 RECORDS</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {identityDocuments.map((item) => item.isAddButton ? (
                    <div
                      key={item.id}
                      className="evidence-card-gradient investigation-border p-4 flex flex-col items-center justify-center text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
                    >
                      <div className="w-1/3">
                        {/* Using div as placeholder for add_circle icon */}
                        <div className="text-3xl mb-2">
                          +
                        </div>
                      </div>
                      <div className="w-2/3">
                        <h3 className="font-headline-md text-headline-md text-on-surface mb-2">{item.title}</h3>
                        <p className="font-label-sm text-label-sm text-on-surface uppercase mb-1">Add Data Source</p>
                      </div>
                    </div>
                  ) : (
                    <div
                      key={item.id}
                      className={`evidence-card-gradient investigation-border p-4 flex flex-col gap-4 group transition-all ${item.isVerified ? 'border-investigation-gold hover:border-investigation-gold/50' : ''}`}
                    >
                      <div className="flex justify-between items-start">
                        <span className={item.tagColor}>{item.tag}</span>
                        <div className="flex items-center">
                          {/* Using div as placeholder for verified/error icons */}
                          <div className="flex items-center">
                            {item.isVerified ? (
                              <span className="mr-1 text-[10px]">✓</span>
                            ) : (
                              <span className="mr-1 text-[10px]">⚠️</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div>
                        <p className="font-label-md text-label-md text-primary mb-1">{item.title}</p>
                        <p className="text-[11px] font-label-sm text-on-surface-variant uppercase tracking-widest">Source: {item.source}</p>
                      </div>
                      <div className="mt-2 pt-4 border-t border-outline-variant flex justify-between items-end">
                        <div className="space-y-1">
                          <p className="text-[10px] text-on-surface-variant uppercase">Last Update</p>
                          <p className="font-label-sm text-label-sm">{item.lastUpdate}</p>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity text-investigation-gold">
                          {/* Using div as placeholder for chevron_right icon */}
                          <div className="flex items-center">
                            <span>→</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Category Section: Device Fingerprints */}
            <div className="md:col-span-12 mt-8">
              <div className="flex items-center gap-3 mb-4">
                {/* Using div as placeholder for devices icon */}
                <div className="flex items-center">
                  <span>📱💻</span>
                </div>
                <h3 className="font-headline-md text-headline-md">Device Fingerprints</h3>
                <div className="h-px flex-1 bg-outline-variant ml-4"></div>
                <span className="font-label-sm text-label-sm text-on-surface-variant">42,019 RECORDS</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Detailed Evidence Panel */}
                <div className="md:col-span-2 bg-surface-container-low investigation-border p-0 overflow-hidden flex flex-col">
                  <div className="bg-surface-container px-4 py-2 border-b border-outline-variant flex justify-between items-center">
                    <span className="font-label-sm text-label-sm text-investigation-gold uppercase tracking-tighter">Live Telemetry Feed</span>
                    <div className="flex gap-2">
                      <span className="w-2 h-2 rounded-full bg-risk-low animate-pulse"></span>
                      <span className="text-[10px] font-label-sm text-on-surface-variant">ACTIVE INGESTION</span>
                    </div>
                  </div>
                  <div className="flex-1 p-0 overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-outline-variant bg-surface-container-lowest">
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant uppercase">Device Token</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant uppercase">Verification</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant uppercase">IP/Geo</th>
                          <th className="px-4 py-3 font-label-sm text-label-sm text-on-surface-variant uppercase text-right">Updated</th>
                        </tr>
                      </thead>
                      <tbody className="font-label-sm text-label-sm divide-y divide-outline-variant">
                        {/* Sample data - in a real app, this would come from an API */}
                        <tr className="hover:bg-surface-container-high transition-colors">
                          <td className="px-4 py-3 text-primary">0x4f...8921</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-risk-low">
                              {/* Using div as placeholder for security icon with fill */}
                              <div className="flex items-center">
                                <span>🔒</span>
                              </div>
                              Hardware Bound
                            </div>
                          </td>
                          <td className="px-4 py-3 text-on-surface-variant">US-EAST-1 (VPC)</td>
                          <td className="px-4 py-3 text-right">14s</td>
                        </tr>
                        <tr className="hover:bg-surface-container-high transition-colors">
                          <td className="px-4 py-3 text-primary">0x9a...3310</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-on-tertiary-container">
                              {/* Using div as placeholder for browser_updated icon */}
                              <div className="flex items-center">
                                <span>🔄</span>
                              </div>
                              Browser Hook
                            </div>
                          </td>
                          <td className="px-4 py-3 text-on-surface-variant">London, UK</td>
                          <td className="px-4 py-3 text-right">1m</td>
                        </tr>
                        <tr className="hover:bg-surface-container-high transition-colors">
                          <td className="px-4 py-3 text-primary">0xbc...1104</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-risk-low">
                              {/* Using div as placeholder for security icon with fill */}
                              <div className="flex items-center">
                                <span>🔒</span>
                              </div>
                              Hardware Bound
                            </div>
                          </td>
                          <td className="px-4 py-3 text-on-surface-variant">Berlin, DE</td>
                          <td className="px-4 py-3 text-right">4m</td>
                        </tr>
                        <tr className="hover:bg-surface-container-high transition-colors">
                          <td className="px-4 py-3 text-primary">0xe2...5591</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1 text-risk-high">
                              {/* Using div as placeholder for warning icon */}
                              <div className="flex items-center">
                                <span>⚠️</span>
                              </div>
                              Emulator Probable
                            </div>
                          </td>
                          <td className="px-4 py-3 text-on-surface-variant">Unknown (Proxy)</td>
                          <td className="px-4 py-3 text-right">12m</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Sidebar Summary Chart / Stats */}
                <div className="bg-surface-container-high border border-outline-variant p-6 flex flex-col justify-between">
                  <div>
                    <p className="font-label-sm text-label-sm text-on-surface-variant uppercase mb-4">Integrity Health</p>
                    <div className="relative h-40 flex items-center justify-center">
                      {/* Using divs as placeholder for the circular progress visualization */}
                      <div className="w-32 h-32 relative">
                        <div className="absolute inset-0 rounded-full bg-surface-variant"></div>
                        <div className="absolute inset-0 rounded-full bg-risk-low" style={{ width: "85%", height: "85%" }}></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="font-headline-lg text-headline-lg">94%</span>
                          <span className="text-[10px] text-on-surface-variant uppercase">Confidence</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between text-label-sm font-label-sm">
                      <span className="text-on-surface-variant">Hardware ID</span>
                      <span className="text-risk-low">38.2k</span>
                    </div>
                    <div className="w-full bg-surface-variant h-1 rounded-full">
                      <div className="bg-risk-low h-1 rounded-full" style={{ width: "85%" }}></div>
                    </div>
                    <div className="flex justify-between text-label-sm font-label-sm">
                      <span className="text-on-surface-variant">Virtual/Proxy</span>
                      <span className="text-risk-medium">3.8k</span>
                    </div>
                    <div className="w-full bg-surface-variant h-1 rounded-full">
                      <div className="bg-risk-medium h-1 rounded-full" style={{ width: "15%" }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Category Section: Historical Case Patterns */}
            <div className="md:col-span-12 mt-8">
              <div className="flex items-center gap-3 mb-4">
                {/* Using div as placeholder for history_edu icon */}
                <div className="flex items-center">
                  <span>📚</span>
                </div>
                <h3 className="font-headline-md text-headline-md">Historical Case Patterns</h3>
                <div className="h-px flex-1 bg-outline-variant ml-4"></div>
                <span className="font-label-sm text-label-sm text-on-surface-variant">856 ANALYZED CLUSTERS</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {historicalPatterns.map((pattern) => (
                  <div
                    key={pattern.id}
                    className="bg-surface-container-low investigation-border p-5 relative overflow-hidden group"
                  >
                    {/* Using div as placeholder for the icon in the corner */}
                    <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                      <div className="text-6xl opacity-10">
                        {/* Using emoji as placeholder for the hub icon */}
                        🔗
                      </div>
                    </div>
                    <div className="flex items-center justify-between mb-4">
                      <span className={`px-2 py-1 ${pattern.typeColor} text-[10px] font-bold rounded`}>
                        {pattern.type}
                      </span>
                      <span className="text-on-surface-variant text-[10px] font-label-sm">ID: {pattern.idNumber}</span>
                    </div>
                    <h4 className="font-headline-md text-headline-md text-primary mb-2">{pattern.title}</h4>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mb-6">{pattern.description}</p>
                    <div className="flex justify-between items-center text-label-sm font-label-sm">
                      <span className={pattern.verificationColor}>Verification: {pattern.verification}</span>
                      <button className="text-investigation-gold hover:underline">
                        {pattern.actionText}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-surface-container border-t border-outline-variant flex justify-around items-center px-4 z-50">
        <a
          className="flex flex-col items-center gap-1 text-on-surface-variant"
          href="#"
        >
          {/* Using div as placeholder for assignment icon */}
          <div className="flex items-center">
            <span>📋</span>
          </div>
          <span className="text-[10px] font-label-sm">Cases</span>
        </a>
        <a
          className="flex flex-col items-center gap-1 text-on-surface-variant"
          href="#"
        >
          {/* Using div as placeholder for account_tree icon */}
          <div className="flex items-center">
            <span>🌳</span>
          </div>
          <span className="text-[10px] font-label-sm">Graph</span>
        </a>
        <a
          className="flex flex-col items-center gap-1 text-primary"
          href="#"
        >
          {/* Using div as placeholder for folder_shared icon with fill */}
          <div className="flex items-center">
            <span>📁</span>
          </div>
          <span className="text-[10px] font-label-sm font-bold">Vault</span>
        </a>
        <a
          className="flex flex-col items-center gap-1 text-on-surface-variant"
          href="#"
        >
          {/* Using div as placeholder for analytics icon */}
          <div className="flex items-center">
            <span>📊</span>
          </div>
          <span className="text-[10px] font-label-sm">System</span>
        </a>
      </nav>
    </div>
  );
}