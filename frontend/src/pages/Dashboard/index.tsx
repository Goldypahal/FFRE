import React, { useState } from "react";

export function Dashboard() {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  return (
    <>
      {/* Side Navigation Shell */}
      <aside className="hidden md:flex flex-col h-full w-64 bg-surface-container-lowest border-r border-outline-variant py-stack-md shrink-0">
        <div className="px-6 mb-8">
          <h1 className="font-headline-md text-headline-md text-on-surface">FFIRE Engine</h1>
          <p className="font-label-sm text-label-sm text-on-tertiary-container mt-1">V2.4 Active</p>
        </div>
        <nav className="flex-1 space-y-1">
          <a
            href="#"
            className="flex items-center px-6 py-3 bg-primary-container text-primary border-r-4 border-primary group"
          >
            {/* Using div as placeholder for assignment icon */}
            <div className="mr-3 flex items-center">
              <span>📋</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Cases</span>
          </a>
          <a
            href="#"
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
          >
            {/* Using div as placeholder for account_tree icon */}
            <div className="mr-3 flex items-center">
              <span>🌳</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Reasoning Graph</span>
          </a>
          <a
            href="#"
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
          >
            {/* Using div as placeholder for folder_shared icon */}
            <div className="mr-3 flex items-center">
              <span>📁</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Evidence Vault</span>
          </a>
          <a
            href="#"
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
          >
            {/* Using div as placeholder for history icon */}
            <div className="mr-3 flex items-center">
              <span>📜</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Historical Patterns</span>
          </a>
          <a
            href="#"
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
          >
            {/* Using div as placeholder for analytics icon */}
            <div className="mr-3 flex items-center">
              <span>📊</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">System Health</span>
          </a>
        </nav>
        <div className="px-4 mb-4">
          <button
            className="w-full py-3 bg-tertiary text-on-tertiary font-label-md text-label-md tracking-widest active:scale-95 transition-all"
          >
            NEW INVESTIGATION
          </button>
        </div>
        <div className="mt-auto border-t border-outline-variant/30 pt-4">
          <a
            href="#"
            className="flex items-center px-6 py-2 text-on-surface-variant hover:text-on-surface transition-colors"
          >
            {/* Using div as placeholder for help icon */}
            <div className="flex items-center">
              <span>❓</span>
            </div>
            <span className="font-label-md text-label-md">Documentation</span>
          </a>
          <a
            href="#"
            className="flex items-center px-6 py-2 text-on-surface-variant hover:text-on-surface transition-colors"
          >
            {/* Using div as placeholder for contact_support icon */}
            <div className="flex items-center">
              <span>🎧</span>
            </div>
            <span className="font-label-md text-label-md">Support</span>
          </a>
        </div>
      </aside>

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col min-w-0 bg-background relative">
        {/* Top Bar Shell */}
        <header className="h-16 flex items-center justify-between px-margin bg-surface border-b border-outline-variant shrink-0">
          <div className="flex items-center space-x-gutter">
            <span className="font-headline-md text-headline-md font-bold text-investment-gold">FFIRE</span>
            <div className="hidden lg:flex items-center bg-surface-container-low border border-outline-variant px-3 py-1.5 w-80">
              {/* Using div as placeholder for search icon */}
              <div className="flex items-center">
                <span>🔍</span>
              </div>
              <input
                className="bg-transparent border-none focus:ring-0 text-sm text-on-surface w-full placeholder:text-outline"
                placeholder="Search signals, cases, or tools..."
                type="text"
              />
            </div>
          </div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-4 border-r border-outline-variant pr-6">
              {/* Using div as placeholder for notifications icon */}
              <div className="flex items-center">
                <span>🔔</span>
              </div>
              {/* Using div as placeholder for settings icon */}
              <div className="flex items-center">
                <span>⚙️</span>
              </div>
            </div>
            <div className="flex items-center space-x-3 cursor-pointer group">
              <div className="text-right">
                <p className="font-label-md text-label-md text-on-surface">Alex Chen</p>
                <p className="font-label-sm text-[10px] text-on-tertiary-container uppercase tracking-tighter">
                  Sr. Investigator
                </p>
              </div>
              <div className="w-10 h-10 rounded-full border border-outline-variant overflow-hidden">
                <div className="w-full h-full flex items-center justify-center bg-surface-container-high text-on-surface-variant text-xs">
                  AC
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-gutter space-y-gutter pb-24">
          {/* Case Header */}
          <div className="bg-surface-container p-6 border border-outline-variant flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <div className="flex items-center space-x-3 mb-1">
                <span className="font-label-sm text-label-sm text-investigation-gold bg-investment-gold/10 px-2 py-0.5">
                  CASE INV-20260630-0091
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-outline-variant"></span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">Transaction T-78491</span>
              </div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">
                $12,450.00 <span className="font-body-md text-body-md text-on-surface-variant font-normal ml-2">USD</span>
              </h2>
            </div>
            <div className="flex space-x-8 items-center">
              <div className="text-center">
                <p className="font-label-sm text-label-sm text-on-tertiary-container uppercase mb-1">
                  Risk Score
                </p>
                <div className="flex items-baseline space-x-1">
                  <span className="font-headline-lg text-headline-lg text-risk-high">82</span>
                  <span className="font-label-md text-label-md text-on-surface-variant">/100</span>
                </div>
              </div>
              <div className="w-px h-10 bg-outline-variant"></div>
              <div className="text-center">
                <p className="font-label-sm text-label-sm text-on-tertiary-container uppercase mb-1">
                  AI Confidence
                </p>
                <div className="flex items-baseline space-x-1">
                  <span className="font-headline-lg text-headline-lg text-investment-gold">91</span>
                  <span className="font-label-md text-label-md text-on-surface-variant">%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Bento Grid Main */}
          <div className="grid grid-cols-12 gap-gutter">
            {/* Reasoning Column */}
            <section className="col-span-12 lg:col-span-4 flex flex-col space-y-gutter">
              <div className="bg-surface-container border border-outline-variant p-6 flex-1">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-label-md text-label-md text-on-surface uppercase tracking-widest flex items-center">
                    {/* Using div as placeholder for description icon */}
                    <div className="flex items-center">
                      <span>📄</span>
                    </div>
                    Explainable Report
                  </h3>
                  {/* Using div as placeholder for open_in_new icon */}
                  <div className="flex items-center">
                    <span>↗️</span>
                  </div>
                </div>
                <div className="space-y-4 font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                  <p>
                    The transaction has been flagged as <span className="text-risk-high font-medium">Critical Risk</span> due to a sequence of anomalous signals. The session originated from an{" "}
                    <span className="text-on-surface font-medium underline decoration-investment-gold/50 cursor-help">
                      unrecognized iPhone 15
                    </span>{" "}
                    [device.first_seen] which has no historical binding to the customer account.
                  </p>
                  <p>
                    Furthermore, a <span className="text-on-surface font-medium underline decoration-investment-gold/50 cursor-help">
                      location mismatch
                    </span> was detected; the request IP originates from London, UK, while the user's primary residence and recent activity are centralized in New York, NY [loc.dist_3400mi].
                  </p>
                  <p>
                    High velocity patterns were also observed, with three failed authentication attempts [auth.fail_3] followed by a successful login via a legacy recovery bypass protocol.
                  </p>
                  <div className="mt-8 p-4 bg-surface-container-low border-l-2 border-investment-gold">
                    <p className="text-[11px] font-label-sm text-investment-gold uppercase mb-2">
                      Automated Conclusion
                    </p>
                    <p className="italic">
                      "The alignment of device spoofing markers and geolocation hopping suggests a high-probability account takeover (ATO) scenario."
                    </p>
                  </div>
                </div>
              </div>
            </section>
            {/* Execution Graph Column */}
            <section className="col-span-12 lg:col-span-5">
              <div className="bg-surface-container border border-outline-variant h-full flex flex-col">
                <div className="p-6 border-b border-outline-variant flex items-center justify-between">
                  <h3 className="font-label-md text-label-md text-on-surface uppercase tracking-widest flex items-center">
                    {/* Using div as placeholder for account_tree icon */}
                    <div className="flex items-center">
                      <span>🌳</span>
                    </div>
                    LangGraph Trace
                  </h3>
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-risk-low animate-pulse"></div>
                    <span className="font-label-sm text-[10px] text-on-tertiary-container uppercase">
                      Processing Step 5/6
                    </span>
                  </div>
                </div>
                <div className="flex-1 relative flex items-center justify-center p-8 bg-surface-container-lowest">
                  {/* We'll keep the SVG from the original for simplicity, but note that it uses custom classes */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
                    <path className="graph-line" d="M 100 100 L 200 100 M 200 100 L 300 50 M 300 100 L 300 150 M 300 50 L 450 100 M 300 150 L 450 100 M 450 100 L 550 100"></path>
                  </svg>
                  <div className="grid grid-cols-3 gap-x-12 gap-y-16 items-center relative z-10">
                    {/* Start */}
                    <div className="col-start-1 bg-graph-node-bg border border-outline-variant p-3 flex flex-col items-center justify-center w-28 h-16">
                      <span className="font-label-sm text-[10px] text-on-tertiary-container">START</span>
                      <span className="font-label-md text-xs text-on-surface">Trigger</span>
                    </div>
                    {/* Planner */}
                    <div className="col-start-2 bg-graph-node-bg border border-outline-variant p-3 flex flex-col items-center justify-center w-28 h-16">
                      <span className="font-label-sm text-[10px] text-on-tertiary-container">PLANNER</span>
                      <span className="font-label-md text-xs text-on-surface">Strategy</span>
                    </div>
                    {/* Retrieval & Risk */}
                    <div className="col-start-3 flex flex-col space-y-8">
                      <div className="bg-graph-node-bg border border-outline-variant p-3 flex flex-col items-center justify-center w-28 h-16">
                        <span className="font-label-sm text-[10px] text-on-tertiary-container">RETRIEVAL</span>
                        <span className="font-label-md text-xs text-on-surface">Evidence</span>
                      </div>
                      <div className="bg-graph-node-bg border border-outline-variant p-3 flex flex-col items-center justify-center w-28 h-16">
                        <span className="font-label-sm text-[10px] text-on-tertiary-container">ANALYSIS</span>
                        <span className="font-label-md text-xs text-on-surface">Scoring</span>
                      </div>
                    </div>
                    {/* Validator (ACTIVE) */}
                    <div className="col-start-2 row-start-2 bg-graph-node-bg node-active border border-investment-gold p-4 flex flex-col items-center justify-center w-36 h-20 -mt-10">
                      <span className="font-label-sm text-[10px] text-investment-gold">ACTIVE</span>
                      <span className="font-label-md text-sm text-on-surface font-bold">VALIDATOR</span>
                      <div className="mt-2 w-full bg-surface-container-lowest h-1">
                        <div className="bg-investment-gold h-full w-[70%]"></div>
                      </div>
                    </div>
                    {/* Report */}
                    <div className="col-start-3 row-start-2 opacity-30 bg-graph-node-bg border border-outline-variant p-3 flex flex-col items-center justify-center w-28 h-16 -mt-10">
                      <span className="font-label-sm text-[10px] text-on-tertiary-container">FINAL</span>
                      <span className="font-label-md text-xs text-on-surface">Report</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
            {/* Evidence Column */}
            <section className="col-span-12 lg:col-span-3 space-y-4">
              <div className="bg-surface-container border border-outline-variant p-5">
                <div className="flex items-center space-x-3 mb-4">
                  {/* Using div as placeholder for stars icon */}
                  <div className="flex items-center">
                    <span>⭐</span>
                  </div>
                  <h4 className="font-label-sm text-label-sm text-on-surface uppercase">Customer Context</h4>
                </div>
                <div className="p-3 bg-surface-container-low border border-outline-variant/30">
                  <div className="flex justify-between items-center">
                    <span className="font-body-sm text-body-sm text-on-surface-variant">Tier</span>
                    <span className="font-label-md text-label-md text-investment-gold">GOLD</span>
                  </div>
                </div>
              </div>
              <div className="bg-surface-container border border-outline-variant p-5">
                <div className="flex items-center space-x-3 mb-4">
                  {/* Using div as placeholder for smartphone icon */}
                  <div className="flex items-center">
                    <span>📱</span>
                  </div>
                  <h4 className="font-label-sm text-label-sm text-on-surface uppercase">Device Audit</h4>
                </div>
                <div className="p-3 bg-surface-container-low border border-outline-variant/30 space-y-2">
                  <p className="font-label-md text-label-md text-on-surface">iPhone 15 Pro</p>
                  <div className="flex items-center text-risk-high">
                    {/* Using div as placeholder for warning icon */}
                    <div className="flex items-center">
                      <span>⚠️</span>
                    </div>
                    <span className="font-label-sm text-[11px] uppercase">Unrecognized hardware</span>
                  </div>
                </div>
              </div>
              <div className="bg-surface-container border border-outline-variant p-5">
                <div className="flex items-center space-x-3 mb-4">
                  {/* Using div as placeholder for distance icon */}
                  <div className="flex items-center">
                    <span>📏</span>
                  </div>
                  <h4 className="font-label-sm text-label-sm text-on-surface uppercase">Geo-Velocity</h4>
                </div>
                <div className="p-3 bg-surface-container-low border border-outline-variant/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] text-on-tertiary-container uppercase">Origin</div>
                    <div className="text-[10px] text-on-tertiary-container uppercase">Home</div>
                  </div>
                  <div className="flex items-center justify-between font-label-md text-label-md">
                    <span>London, UK</span>
                    <span className="material-symbols-outlined text-on-tertiary-container">arrow_forward</span>
                    <span>New York, NY</span>
                  </div>
                  <p className="text-[11px] text-risk-high text-center">
                    3,470 mi in 24 mins (IMPOSSIBLE)
                  </p>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Bottom Action Bar */}
        <footer className="absolute bottom-0 left-0 right-0 h-20 bg-surface-container-highest border-t border-outline-variant px-margin flex items-center justify-between z-20">
          <div className="flex items-center space-x-4">
            {/* Using div as placeholder for bookmark icon */}
            <div className="flex items-center">
              <span>🔖</span>
            </div>
            {/* Using div as placeholder for share icon */}
            <div className="flex items-center">
              <span>📤</span>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button
              className="px-6 py-2.5 bg-surface-variant border border-outline-variant text-on-surface font-label-md text-label-md hover:bg-surface-container-high transition-colors active:scale-95"
            >
              REQUEST HUMAN REVIEW
            </button>
            <button
              className="px-6 py-2.5 bg-transparent border border-error text-error font-label-md text-label-md hover:bg-error/10 transition-colors active:scale-95"
            >
              REJECT TRANSACTION
            </button>
            <button
              className="px-8 py-2.5 bg-risk-low text-on-primary font-label-md text-label-md font-bold hover:brightness-110 transition-colors active:scale-95 flex items-center"
            >
              {/* Using div as placeholder for check_circle icon */}
              <div className="flex items-center">
                <span>✅</span>
              </div>
              APPROVE
            </button>
          </div>
        </footer>
      </main>

      {/* Micro-interaction Script (simplified) */}
      {/* We'll omit the complex tooltip logic for now, but we can add a simple version if needed */}
    </>
  );
}