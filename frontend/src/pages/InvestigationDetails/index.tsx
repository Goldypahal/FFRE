import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

export function InvestigationDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [investigation, setInvestigation] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  // Helper function to format currency
  const formatCurrency = (amount: number | undefined, currency: string | undefined) => {
    if (amount === undefined || amount === null) return "N/A";
    return `${currency || "$"}${amount.toFixed(2)}`;
  };

  // Helper function to get merchant name from evidence
  const getMerchantName = () => {
    const merchEvidence = investigation?.evidence?.find((e: any) => e.source === "merchant_evidence");
    if (merchEvidence) {
      try {
        const cleanJson = merchEvidence.snippet.replace(/'/g, '"');
        const parsed = JSON.parse(cleanJson);
        return parsed.name || "Unknown Merchant";
      } catch {
        return merchEvidence.snippet;
      }
    }
    return "Merchant Analysis Pending";
  };

  // Helper function to get node status
  const getNodeStatus = (nodeName: string) => {
    if (!investigation) return "pending";
    const logs = investigation.audit_logs || [];

    const hasError = logs.some((l: any) =>
      l.action.toLowerCase().includes(nodeName.toLowerCase()) &&
      (l.action.toUpperCase().includes("ERROR") || l.action.toUpperCase().includes("FAILED"))
    );
    if (hasError) return "failed";

    const hasCompleted = logs.some((l: any) =>
      l.action.toLowerCase().includes(nodeName.toLowerCase()) &&
      l.action.toUpperCase().includes("NODE_EXECUTION")
    );
    if (hasCompleted) return "completed";

    if (investigation.status === "RUNNING") {
      if (nodeName === "planner") return "completed";

      const isRetriever = nodeName.startsWith("retrieve");
      const hasAnyRetrieverFinished = logs.some((l: any) => l.action.toLowerCase().includes("retrieve_"));

      if (isRetriever) return "running";
      if (nodeName === "rule_engine" && hasAnyRetrieverFinished) return "running";
    }

    return "pending";
  };

  // Fetch investigation details
  async function loadDetails() {
    try {
      setLoading(true);
      setError(null);
      const data = await api.get<any>(`/investigations/${id}`);
      setInvestigation(data);
    } catch (err: any) {
      console.error("Failed to load investigation details", err);
      setError(err.message || "Failed to load investigation details.");
    } finally {
      setLoading(false);
    }
  }

  // Load data when component mounts or ID changes
  useEffect(() => {
    if (id) {
      loadDetails();
    }
  }, [id]);

  // Handle review actions
  async function handleReviewAction(action: "APPROVE" | "REJECT") {
    if (!id) return;

    try {
      await api.post(`/investigations/${id}/review`, {
        action,
        notes: `Manual analyst review decision: ${action}`
      });
      loadDetails(); // Refresh data after action
    } catch (err: any) {
      console.error("Review action failed", err);
      // In a real app, we'd show a proper error notification
      alert(err.message || "Failed to submit review action.");
    }
  }

  // Handle tooltip mouse events
  const handleTooltipEnter = (tooltipId: string) => {
    setActiveTooltip(tooltipId);
  };

  const handleTooltipLeave = () => {
    setActiveTooltip(null);
  };

  if (loading && !investigation) {
    return (
      <div className="flex h-full w-full items-center justify-center text-text-secondary">
        Loading investigation details...
      </div>
    );
  }

  if (error || !investigation) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-4 text-text-secondary">
        {/* Using div as placeholder for alert icon */}
        <div className="w-8 h-8 flex items-center justify-center bg-system-red/20 rounded-lg text-system-red">
          !
        </div>
        <p>{error || "Investigation not found."}</p>
        <button
          onClick={() => navigate("/investigations")}
          className="px-4 py-2 bg-transparent border border-outline-variant text-on-surface hover:bg-surface-container-high transition-colors rounded"
        >
          Back to Queue
        </button>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden font-body-md text-body-md dark">
      {/* Side Navigation Shell */}
      <aside className="hidden md:flex flex-col h-full w-64 bg-surface-container-lowest border-r border-outline-variant py-stack-md shrink-0">
        <div className="px-6 mb-8">
          <h1 className="font-headline-md text-headline-md text-on-surface">FFIRE Engine</h1>
          <p className="font-label-sm text-label-sm text-on-tertiary-container mt-1">V2.4 Active</p>
        </div>
        <nav className="flex-1 space-y-1">
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
            href="#"
          >
            {/* Using div as placeholder for assignment icon */}
            <div className="mr-3 flex items-center">
              <span>📋</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Cases</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
            href="#"
          >
            {/* Using div as placeholder for account_tree icon */}
            <div className="mr-3 flex items-center">
              <span>🌳</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Reasoning Graph</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
            href="#"
          >
            {/* Using div as placeholder for folder_shared icon */}
            <div className="mr-3 flex items-center">
              <span>📁</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Evidence Vault</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
            href="#"
          >
            {/* Using div as placeholder for history icon */}
            <div className="mr-3 flex items-center">
              <span>📜</span>
            </div>
            <span className="font-label-md text-label-md uppercase tracking-wider">Historical Patterns</span>
          </a>
          <a
            className="flex items-center px-6 py-3 text-on-surface-variant hover:bg-surface-container-low transition-all group"
            href="#"
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
            className="flex items-center px-6 py-2 text-on-surface-variant hover:text-on-surface transition-colors"
            href="#"
          >
            {/* Using div as placeholder for help icon */}
            <div className="mr-3 flex items-center">
              <span>❓</span>
            </div>
            <span className="font-label-md text-label-md">Documentation</span>
          </a>
          <a
            className="flex items-center px-6 py-2 text-on-surface-variant hover:text-on-surface transition-colors"
            href="#"
          >
            {/* Using div as placeholder for contact_support icon */}
            <div className="mr-3 flex items-center">
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
            <span className="font-headline-md text-headline-md font-bold text-investigation-gold">FFIRE</span>
            <div className="hidden lg:flex items-center bg-surface-container-low border border-outline-variant px-3 py-1.5 w-80">
              {/* Using div as placeholder for search icon */}
              <div className="relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center">
                  <span>🔍</span>
                </div>
                <input
                  className="bg-transparent border-none focus:ring-0 text-sm text-on-surface w-full placeholder:text-outline"
                  placeholder="Search signals, cases, or tools..."
                  type="text"
                />
              </div>
            </div>
          </div>
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-4 border-r border-outline-variant pr-6">
              {/* Using divs as placeholder for notification and settings icons */}
              <div className="relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center">
                  <span>🔔</span>
                </div>
              </div>
              <div className="relative">
                <div className="absolute left-0 top-1/2 -translate-y-1/2 flex items-center">
                  <span>⚙️</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3 cursor-pointer group">
              <div className="text-right">
                <p className="font-label-md text-label-md text-on-surface">Alex Chen</p>
                <p className="font-label-sm text-[10px] text-on-tertiary-container uppercase tracking-tighter">Sr. Investigator</p>
              </div>
              {/* Using div as placeholder for user image */}
              <div className="w-10 h-10 rounded-full border border-outline-variant flex items-center justify-center bg-surface-container-high">
                <span className="text-on-surface-variant">AC</span>
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
                <span className="font-label-sm text-label-sm text-investigation-gold bg-investigation-gold/10 px-2 py-0.5">CASE {investigation.investigation_id.slice(0, 12)}...</span>
                <span className="w-1.5 h-1.5 rounded-full bg-outline-variant"></span>
                <span className="font-label-sm text-label-sm text-on-surface-variant">Transaction {investigation.transaction_id}</span>
              </div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">${formatCurrency(investigation.amount, investigation.currency)} <span className="font-body-md text-body-md text-on-surface-variant font-normal ml-2">{investigation.currency}</span></h2>
            </div>
            <div className="flex space-x-8 items-center">
              <div className="text-center">
                <p className="font-label-sm text-label-sm text-on-tertiary-container uppercase mb-1">Risk Score</p>
                <div className="flex items-baseline space-x-1">
                  <span className={`font-headline-lg text-headline-lg text-${investigation.risk_score >= 80 ? 'risk-high' : investigation.risk_score >= 60 ? 'risk-medium' : 'risk-low'}`}>
                    {investigation.risk_score}
                  </span>
                  <span className="font-label-md text-label-md text-on-surface-variant">/100</span>
                </div>
              </div>
              <div className="w-px h-10 bg-outline-variant"></div>
              <div className="text-center">
                <p className="font-label-sm text-label-sm text-on-tertiary-container uppercase mb-1">AI Confidence</p>
                <div className="flex items-baseline space-x-1">
                  <span className="font-headline-lg text-headline-lg text-investigation-gold">{investigation.ai_confidence}</span>
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
                    <div className="mr-2 flex items-center">
                      <span>📝</span>
                    </div>
                    Explainable Report
                  </h3>
                  <span className="material-symbols-outlined text-on-surface-variant cursor-pointer hover:text-on-surface">open_in_new</span>
                </div>
                <div className="space-y-4 font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                  <p>
                    The transaction has been flagged as <span className={`text-${investigation.risk_score >= 80 ? 'risk-high' : investigation.risk_score >= 60 ? 'risk-medium' : 'risk-low'} font-medium`}>
                      {investigation.risk_score >= 80 ? 'Critical Risk' : investigation.risk_score >= 60 ? 'High Risk' : 'Medium Risk'}
                    </span> due to a sequence of anomalous signals. The session originated from an <span className="text-on-surface font-medium underline decoration-investigation-gold/50 cursor-help" onMouseEnter={() => handleTooltipEnter('device')} onMouseLeave={handleTooltipLeave}>
                      unrecognized iPhone 15
                    </span> <span className="font-mono text-xs text-investigation-gold">[device.first_seen]</span> which has no historical binding to the customer account.
                  </p>
                  <p>
                    Furthermore, a <span className="text-on-surface font-medium underline decoration-investigation-gold/50 cursor-help" onMouseEnter={() => handleTooltipEnter('location')} onMouseLeave={handleTooltipLeave}>
                      location mismatch
                    </span> was detected; the request IP originates from London, UK, while the user's primary residence and recent activity are centralized in New York, NY <span className="font-mono text-xs text-investigation-gold">[loc.dist_3400mi]</span>.
                  </p>
                  <p>
                    High velocity patterns were also observed, with three failed authentication attempts <span className="font-mono text-xs text-investigation-gold">[auth.fail_3]</span> followed by a successful login via a legacy recovery bypass protocol.
                  </p>
                  <div className="mt-8 p-4 bg-surface-container-low border-l-2 border-investigation-gold">
                    <p className="text-[11px] font-label-sm text-investigation-gold uppercase mb-2">Automated Conclusion</p>
                    <p className="italic">"{investigation.report || 'The alignment of device spoofing markers and geolocation hopping suggests a high-probability account takeover (ATO) scenario.'}"</p>
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
                    <div className="mr-2 flex items-center">
                      <span>🌳</span>
                    </div>
                    LangGraph Trace
                  </h3>
                  <div className="flex items-center space-x-2">
                    <span className={`w-2 h-2 rounded-full bg-${investigation.status === 'RUNNING' ? 'risk-low' : 'surface-container-lowest'} animate-pulse`}></span>
                    <span className="font-label-sm text-[10px] text-on-tertiary-container uppercase">Processing Step {Math.floor(Math.random() * 6) + 1}/6</span>
                  </div>
                </div>
                <div className="flex-1 relative flex items-center justify-center p-8 bg-surface-container-lowest">
                  {/* Visualizing Graph Nodes */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
                    <path className="graph-line" d="M 100 100 L 200 100 M 200 100 L 300 50 M 200 100 L 300 150 M 300 50 L 450 100 M 300 150 L 450 100 M 450 100 L 550 100"></path>
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
                    <div className="col-start-2 row-start-2 bg-graph-node-bg node-active border border-investigation-gold p-4 flex flex-col items-center justify-center w-36 h-20 -mt-10">
                      <span className="font-label-sm text-[10px] text-investigation-gold">ACTIVE</span>
                      <span className="font-label-md text-sm text-on-surface font-bold">VALIDATOR</span>
                      <div className="mt-2 w-full bg-surface-container-lowest h-1">
                        <div className="bg-investigation-gold h-full w-[70%]"></div>
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
              {/* Customer Context */}
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
                    <span className="font-label-md text-label-md text-investigation-gold">GOLD</span>
                  </div>
                </div>
              </div>

              {/* Device Audit */}
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

              {/* Geo-Velocity */}
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
                    {/* Using div as placeholder for arrow_forward icon */}
                    <div className="flex items-center">
                      <span>→</span>
                    </div>
                    <span>New York, NY</span>
                  </div>
                  <p className="text-[11px] text-risk-high text-center">3,470 mi in 24 mins (IMPOSSIBLE)</p>
                </div>
              </div>
            </section>
          </div>
        </div>

        {/* Bottom Action Bar */}
        <footer className="absolute bottom-0 left-0 right-0 h-20 bg-surface-container-highest border-t border-outline-variant px-margin flex items-center justify-between z-20">
          <div className="flex items-center space-x-4">
            {/* Using divs as placeholder for bookmark and share icons */}
            <div className="flex items-center">
              <span>🔖</span>
            </div>
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
              onClick={() => handleReviewAction("REJECT")}
            >
              REJECT TRANSACTION
            </button>
            <button
              className="px-8 py-2.5 bg-risk-low text-on-primary font-label-md text-label-md font-bold hover:brightness-110 transition-colors active:scale-95 flex items-center"
              onClick={() => handleReviewAction("APPROVE")}
            >
              {/* Using div as placeholder for check_circle icon */}
              <div className="mr-2 flex items-center">
                <span>✅</span>
              </div>
              APPROVE
            </button>
          </div>
        </footer>

        {/* Micro-interaction Script */}
        {/* Note: In a real implementation, we would use useEffect for these event listeners */}
        <div
          onMouseMove={(e) => {
            const card = document.querySelector('.login-card');
            if (card) {
              const x = (window.innerWidth / 2 - e.pageX) / 100;
              const y = (window.innerHeight / 2 - e.pageY) / 100;
              // Note: In the actual Stitch design, this affects the login card,
              // but in our investigation dashboard, we might want to apply it to a different element
              // For now, we'll comment this out as it doesn't apply to this page
              // card.style.transform = `translate(${x}px, ${y}px)`;
            }
          }}
        >
          {/* Tooltip implementations */}
          {activeTooltip === 'device' && (
            <div className="absolute bg-surface-container-high border border-outline-variant p-2 text-[10px] z-50 rounded shadow-xl max-w-xs">
              Confidence: 0.98. Source: Auth-Session-Manager. Trace ID: a8f7-92bc.
            </div>
          )}
          {activeTooltip === 'location' && (
            <div className="absolute bg-surface-container-high border border-outline-variant p-2 text-[10px] z-50 rounded shadow-xl max-w-xs">
              Confidence: 0.95. Source: GeoIP-Service. Trace ID: f3a1-77de.
            </div>
          )}
        </div>
      </main>
    </div>
  );
}