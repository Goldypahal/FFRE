import React from "react";
import { Link } from "react-router-dom";

// Since we can't easily import lucide icons in this environment,
// we'll use SVG emojis or simple divs as placeholders for icons
const Landing = () => {
  return (
    <>
      {/* Header Bar */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-8">
            {/* Logo */}
            <div className="flex items-center gap-2 group cursor-pointer">
              <div className="w-8 h-8 bg-accent-primary flex items-center justify-center rounded">
                <span className="text-white font-bold italic">F</span>
              </div>
              <span className="text-xl font-bold tracking-tight text-white">FFIRE</span>
            </div>
            {/* Desktop Nav Links */}
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
              <a href="#" className="hover:text-white transition-colors">
                Platform
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Solutions
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Compliance
              </a>
              <a href="#" className="hover:text-white transition-colors">
                API Docs
              </a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              className="px-4 py-2 text-sm font-medium hover:text-white transition-colors"
            >
              Sign in
            </button>
            <Link
              to="/auth"
              className="bg-white text-surface px-5 py-2 rounded font-semibold text-sm hover:bg-slate-200 transition-all"
            >
              Request a Demo
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="relative pt-20 pb-32 overflow-hidden">
          <div className="absolute inset-0 hero-glow pointer-events-none"></div>
          <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent-primary/10 border border-accent-primary/20 text-accent-primary text-xs font-bold uppercase tracking-widest mb-8">
              <span className="relative flex h-2 w-2">
                <span
                  className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-primary opacity-75"
                ></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-primary"></span>
              </span>
              Next-Gen Fraud Intelligence
            </div>
            <h1
              className="text-5xl md:text-7xl font-bold leading-tight tracking-tight mb-6 text-gradient"
            >
              Explainable Multi-Step Reasoning<br />
              for Enterprise Fraud
            </h1>
            <p className="max-w-2xl mx-auto text-lg md:text-xl text-slate-400 mb-10">
              Move beyond opaque risk scores with a deterministic LangGraph-powered investigation engine. Trace every decision to verifiable evidence.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/auth"
                className="w-full sm:w-auto px-8 py-4 bg-accent-primary hover:bg-blue-600 text-white rounded font-bold text-base transition-all shadow-lg shadow-accent-primary/20"
              >
                Request a Demo
              </Link>
              <a
                href="#"
                className="w-full sm:w-auto px-8 py-4 border border-white/10 hover:bg-white/5 text-white font-bold text-base transition-all"
              >
                View Sample Report
              </a>
            </div>
            {/* Product Preview Mockup */}
            <div className="mt-20 relative mx-auto max-w-5xl group" data-purpose="product-preview">
              <div
                className="absolute -inset-1 bg-gradient-to-r from-accent-primary/20 to-accent-gold/20 rounded-lg blur opacity-30 group-hover:opacity-50 transition duration-1000"
              ></div>
              <div
                className="relative bg-surface-container-low border border-white/10 rounded-lg shadow-2xl overflow-hidden aspect-video"
              >
                {/* Using a placeholder image - in a real app this would be a proper dashboard mockup */}
                <div className="w-full h-full bg-gradient-to-br from-surface-container-high to-surface-container-highest flex items-center justify-center">
                  <div className="text-center text-on-surface-variant">
                    <div className="text-2xl font-bold mb-2">Investigation Dashboard</div>
                    <div className="text-sm">Preview of FFIRE's Reasoning Interface</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Social Proof */}
        <section className="py-12 border-y border-white/5 bg-surface-container-lowest/50">
          <div className="max-w-7xl mx-auto px-6">
            <p className="text-center text-xs font-bold uppercase tracking-[0.2em] text-slate-500 mb-8">
              Trusted by Global Financial Institutions
            </p>
            <div className="flex flex-wrap justify-center items-center gap-12 md:gap-20 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
              {/* Placeholder Fintech Brands */}
              <div className="text-2xl font-bold tracking-tighter text-white">VORTEX BANK</div>
              <div className="text-2xl font-bold tracking-tighter text-white">SECURELEDGER</div>
              <div className="text-2xl font-bold tracking-tighter text-white">APEX CAPITAL</div>
              <div className="text-2xl font-bold tracking-tighter text-white">NOVA PAY</div>
              <div className="text-2xl font-bold tracking-tighter text-white">QUANTUM TRUST</div>
            </div>
          </div>
        </section>

        {/* Features Grid */}
        <section className="py-32 relative" data-purpose="features">
          <div className="max-w-7xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end mb-16 gap-6">
              <div className="max-w-2xl">
                <h2 className="text-accent-gold text-sm font-bold uppercase tracking-widest mb-4">
                  The FFIRE Advantage
                </h2>
                <h3 className="text-3xl md:text-4xl font-bold text-white">
                  Audit-ready investigations for high-stakes compliance.
                </h3>
              </div>
              <div className="text-slate-400 max-w-sm text-sm">
                Our multi-agent orchestration ensures that no stone is left unturned and no decision remains unexplained.
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Feature 1: Deterministic Execution */}
              <div className="p-8 bg-surface-container-low border border-white/5 rounded-lg hover:border-accent-primary/50 transition-all group">
                <div className="w-12 h-12 bg-accent-primary/10 rounded flex items-center justify-center mb-6 group-hover:bg-accent-primary/20 transition-colors">
                  {/* Deterministic execution icon - placeholder */}
                  <div className="w-6 h-6 text-accent-primary flex items-center justify-center bg-accent-primary/20 rounded-full">
                    <span className="text-xs font-mono">⚡</span>
                  </div>
                </div>
                <h4 className="text-xl font-bold text-white mb-3">
                  Deterministic Execution
                </h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  LangGraph-based pipelines ensure repeatable execution and a 100% auditable history for every case.
                </p>
              </div>
              {/* Feature 2: Grounded Reasoning */}
              <div className="p-8 bg-surface-container-low border-border-white/5 rounded-lg hover:border-accent-gold/50 transition-all group">
                <div className="w-12 h-12 bg-accent-gold/10 rounded flex items-center justify-center mb-6 group-hover:bg-accent-gold/20 transition-colors">
                  {/* Grounded reasoning icon - placeholder */}
                  <div className="w-6 h-6 text-accent-gold flex items-center justify-center bg-accent-gold/20 rounded-full">
                    <span className="text-xs">✓</span>
                  </div>
                </div>
                <h4 className="text-xl font-bold text-white mb-3">
                  Grounded Reasoning
                </h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Every LLM claim is verified against source data. No hallucinations, only evidence-backed conclusions.
                </p>
              </div>
              {/* Feature 3: Human-in-the-Loop */}
              <div className="p-8 bg-surface-container-low border-border-white/5 rounded-lg hover:border-accent-primary/50 transition-all group">
                <div className="w-12 h-12 bg-accent-primary/10 rounded flex items-center justify-center mb-6 group-hover:bg-accent-primary/20 transition-colors">
                  {/* Human-in-the-loop icon - placeholder */}
                  <div className="w-6 h-6 text-accent-primary flex items-center justify-center bg-accent-primary/20 rounded-full">
                    <span className="text-xs">👁️</span>
                  </div>
                </div>
                <h4 className="text-xl font-bold text-white mb-3">
                  Human-in-the-Loop
                </h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Intelligent escalation triggers for high-risk or low-confidence cases, ensuring expert oversight.
                </p>
              </div>
              {/* Feature 4: Composite Scoring */}
              <div className="p-8 bg-surface-container-low border-border-white/5 rounded-lg hover:border-accent-gold/50 transition-all group">
                <div className="w-12 h-12 bg-accent-gold/10 rounded flex items-center justify-center mb-6 group-hover:bg-accent-gold/20 transition-colors">
                  {/* Composite scoring icon - placeholder */}
                  <div className="w-6 h-6 text-accent-gold flex items-center justify-center bg-accent-gold/20 rounded-full">
                    <span className="text-xs">📊</span>
                  </div>
                </div>
                <h4 className="text-xl font-bold text-white mb-3">
                  Composite Scoring
                </h4>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Combines heuristic rules, vector similarity, and LLM reasoning into one transparent risk signal.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Showcase Section */}
        <section className="py-32 bg-surface-container-lowest grid-bg" data-purpose="product-deep-dive">
          <div className="max-w-7xl mx-auto px-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
              <div>
                <h2 className="text-accent-primary text-sm font-bold uppercase tracking-widest mb-4">
                  Precision Reasoning
                </h2>
                <h3 className="text-4xl font-bold text-white mb-6 leading-tight">
                  From Opaque Scores to Verified Insights
                </h3>
                <p className="text-slate-400 mb-8 leading-relaxed">
                  Traditional fraud systems give you a number. FFIRE gives you a report. Our engine decomposes investigations into parallel tasks: customer history, geolocation analysis, and merchant reputation checks—then weaves them into a grounded narrative.
                </p>
                <ul className="space-y-4 mb-10">
                  <li className="flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 w-5 h-5 rounded-full bg-accent-success/20 flex items-center justify-center">
                      <span className="w-3 h-3 text-accent-success">✓</span>
                    </div>
                    <span className="text-slate-300">P95 investigation latency &lt; 8 seconds</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 w-5 h-5 rounded-full bg-accent-success/20 flex items-center justify-center">
                      <span className="w-3 h-3 text-accent-success">✓</span>
                    </div>
                    <span className="text-slate-300">80% reduction in manual investigation time</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <div className="mt-1 flex-shrink-0 w-5 h-5 rounded-full bg-accent-success/20 flex items-center justify-center">
                      <span className="w-3 h-3 text-accent-success">✓</span>
                    </div>
                    <span className="text-slate-300">Full RBAC and encryption compliance</span>
                  </li>
                </ul>
                <button
                  className="px-6 py-3 border border-accent-primary text-accent-primary hover:bg-accent-primary/10 rounded font-bold transition-all"
                >
                  Explore Architecture
                </button>
              </div>
              <div className="relative">
                {/* Graphical Representation of LangGraph Trace */}
                <div
                  className="bg-surface border border-white/10 rounded-xl p-8 shadow-2xl overflow-hidden relative"
                  data-purpose="graph-visualization"
                >
                  <div className="flex items-center justify-between mb-8">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                      Active Execution Trace
                    </span>
                    <span className="flex items-center gap-2 text-[10px] bg-accent-primary/10 text-accent-primary px-2 py-0.5 rounded-full border border-accent-primary/20">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-primary animate-pulse"></span>
                      Processing
                    </span>
                  </div>
                  {/* Visualization Nodes (Abstracted CSS representation) */}
                  <div className="space-y-6">
                    {/* Start Node */}
                    <div className="flex items-center gap-4">
                      <div className="w-3 h-3 rounded-full bg-accent-success"></div>
                      <div className="h-10 px-4 flex items-center bg-surface-container-bright rounded border border-white/10 text-xs font-mono">Planner::Task_Decomposition</div>
                    </div>
                    {/* Retrieval & Risk Nodes */}
                    <div className="ml-8 border-l-2 border-white/5 pl-8 space-y-4">
                      <div className="flex items-center gap-4">
                        <div className="w-3 h-3 rounded-full bg-accent-success"></div>
                        <div className="h-10 px-4 flex items-center bg-surface-container-bright rounded border border-white/10 text-xs font-mono">Retriever::Transaction_History</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="w-3 h-3 rounded-full bg-accent-success"></div>
                        <div className="h-10 px-4 flex items-center bg-surface-container-bright rounded border border-white/10 text-xs font-mono">Retriever::Device_Fingerprint</div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="w-3 h-3 rounded-full bg-accent-primary animate-pulse"></div>
                        <div className="h-10 px-4 flex items-center bg-accent-primary/10 rounded border border-accent-primary/30 text-xs font-mono text-accent-primary">Reasoner::Explainable_Report</div>
                      </div>
                    </div>
                    {/* Validator Node (Ghosted) */}
                    <div className="flex items-center gap-4 opacity-30">
                      <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                      <div className="h-10 px-4 flex inset-center bg-surface-container-bright rounded border border-white/5 text-xs font-mono">Validator::Grounding_Check</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Footer Section */}
        <section className="py-24" data-purpose="cta-banner">
          <div className="max-w-7xl mx-auto px-6">
            <div className="bg-gradient-to-b from-surface-container-low to-surface rounded-2xl p-12 text-center border border-white/5 relative overflow-hidden">
              <div className="absolute inset-0 grid-bg opacity-10"></div>
              <div className="relative z-10">
                <h2 className="text-4xl font-bold text-white mb-6">
                  Ready to upgrade your fraud defense?
                </h2>
                <p className="text-slate-400 max-w-xl mx-auto mb-10">
                  Join leading fintechs reducing false positives and manual overhead with FFIRE's reasoning engine.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <button
                    className="w-full sm:w-auto px-10 py-4 bg-white text-surface hover:bg-slate-200 font-bold rounded transition-all"
                  >
                    Book a Technical Demo
                  </button>
                  <button
                    className="w-full sm:w-auto px-10 py-4 border border-white/10 hover:bg-white/5 text-white font-bold rounded transition-all"
                  >
                    Download SRS PDF
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Main Footer */}
      <footer className="bg-surface-container-lowest pt-20 pb-10 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-20">
            <div className="col-span-2">
              <div className="flex items-center gap-2 mb-6">
                <div className="w-8 h-8 bg-accent-primary flex items-center justify-center rounded">
                  <span className="text-white font-bold italic">F</span>
                </div>
                <span className="text-xl font-bold tracking-tight text-white">FFIRE</span>
              </div>
              <p className="text-slate-500 text-sm max-w-xs leading-relaxed">
                Financial Fraud Investigation Reasoning Engine. Enterprise-grade AI for transparent, auditable fraud detection.
              </p>
            </div>
            <div>
              <h5 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Platform</h5>
              <ul className="space-y-4 text-sm text-slate-500">
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    How it works
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    LangGraph Engine
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Security
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Roadmap
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h5 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Resources</h5>
              <ul className="space-y-4 text-sm text-slate-500">
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    API Reference
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Compliance Guide
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Case Studies
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h5 className="text-white font-bold mb-6 text-sm uppercase tracking-widest">Company</h5>
              <ul className="space-y-4 text-sm text-slate-500">
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    About Us
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Careers
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Contact
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-accent-primary transition-colors">
                    Legal
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="pt-10 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="text-slate-600 text-xs">
              © 2026 FFIRE Engine V2.4. All rights reserved. Confidential - Internal Engineering.
            </div>
            <div className="flex gap-6 text-xs text-slate-600">
              <a href="#" className="hover:text-white transition-colors">
                Privacy Policy
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Terms of Service
              </a>
              <a href="#" className="hover:text-white transition-colors">
                Cookie Policy
              </a>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
};

export { Landing };
export default Landing;