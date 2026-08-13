import React from "react";

export function Pricing() {
  return (
    <>
      {/* TopNavBar */}
      <nav className="bg-surface dark:bg-surface flex justify-between items-center h-16 w-full px-margin border-b border-outline-variant fixed top-0 z-50">
        <div className="flex items-center gap-stack-md">
          <span className="font-headline-md text-headline-md font-bold text-investigation-gold tracking-tight">FFIRE</span>
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
            {/* Using div as placeholder for search icon */}
            <div className="flex items-center">
              <span>🔍</span>
            </div>
            <input className="bg-transparent border-none focus:ring-0 text-sm text-on-surface w-48" placeholder="Quick Search..." type="text"/>
          </div>
          <div className="flex items-center gap-stack-md">
            {/* Using div as placeholder for notifications icon */}
            <div className="flex items-center">
              <span>🔔</span>
            </div>
            {/* Using div as placeholder for settings icon */}
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
      </nav>
      {/* Main Content */}
      <main className="pt-24 pb-20 px-margin max-w-container-max mx-auto">
        {/* Hero Section */}
        <header className="text-center mb-16 relative">
          <h1 className="font-display-lg text-display-lg text-on-surface mb-stack-sm">FFIRE Pricing</h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto">
            Deterministic Intelligence for Fintech. Scale your fraud investigations with auditable reasoning and custom AI guardrails.
          </p>
        </header>
        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-gutter mb-24">
          {/* Starter */}
          <div className="bg-surface-container-low border border-outline-variant rounded-xl p-8 flex flex-col hover:border-on-surface-variant transition-all duration-300">
            <div className="mb-stack-lg">
              <span className="font-label-md text-label-md text-on-primary-container uppercase tracking-widest mb-2 block">For Emerging Fintechs</span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">Starter</h2>
              <div className="flex items-baseline gap-1 mt-4">
                <span className="font-headline-md text-headline-md text-on-surface">$</span>
                <span className="font-display-lg text-display-lg text-on-surface">499</span>
                <span className="text-on-surface-variant font-body-sm">/mo</span>
              </div>
            </div>
            <ul className="space-y-stack-md flex-grow mb-stack-lg">
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon */}
                <div className="flex items-center">
                  <span>✅</span>
                </div>
                <span className="text-on-surface-variant">Standard Fraud Monitoring</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon */}
                <div className="flex items-center">
                  <span>✅</span>
                </div>
                <span className="text-on-surface-variant">10,000 Monthly Transactions</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon */}
                <div className="flex items-center">
                  <span>✅</span>
                </div>
                <span className="text-on-surface-variant">Core Explainability Logs</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon */}
                <div className="flex items-center">
                  <span>✅</span>
                </div>
                <span className="text-on-surface-variant">Email Support</span>
              </li>
            </ul>
            <button className="w-full py-stack-md border border-outline text-on-surface hover:bg-surface-container-high transition-colors font-bold uppercase tracking-wider text-label-md">
              Start Free Trial
            </button>
          </div>
          {/* Professional */}
          <div className="bg-surface-container-high border border-investigation-gold rounded-xl p-8 flex flex-col relative pricing-card-shadow glow-soft transform lg:-translate-y-4">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-investigation-gold text-surface px-4 py-1 rounded-full text-label-sm font-bold uppercase">
              Most Popular
            </div>
            <div className="mb-stack-lg">
              <span className="font-label-md text-label-md text-investigation-gold uppercase tracking-widest mb-2 block">Advanced Reasoning</span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">Professional</h2>
              <div className="flex items-baseline gap-1 mt-4">
                <span className="font-headline-md text-headline-md text-on-surface">$</span>
                <span className="font-display-lg text-display-lg text-on-surface">2,499</span>
                <span className="text-on-surface-variant font-body-sm">/mo</span>
              </div>
            </div>
            <ul className="space-y-stack-md flex-grow mb-stack-lg">
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon (investigation-gold) */}
                <div className="flex items-center">
                  <span style={{ color: '#FCD34D' }}>✅</span>
                </div>
                <span className="text-on-surface">LangGraph Custom Logic</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon (investigation-gold) */}
                <div className="flex items-center">
                  <span style={{ color: '#FCD34D' }}>✅</span>
                </div>
                <span className="text-on-surface">Execution Trace Visualization</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon (investigation-gold) */}
                <div className="flex items-center">
                  <span style={{ color: '#FCD34D' }}>✅</span>
                </div>
                <span className="text-on-surface">100,000 Monthly Transactions</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon (investigation-gold) */}
                <div className="flex items-center">
                  <span style={{ color: '#FCD34D' }}>✅</span>
                </div>
                <span className="text-on-surface">Real-time Risk Alerts</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for check_circle icon (investigation-gold) */}
                <div className="flex items-center">
                  <span style={{ color: '#FCD34D' }}>✅</span>
                </div>
                <span className="text-on-surface">Priority Support</span>
              </li>
            </ul>
            <button className="w-full py-stack-md bg-investigation-gold text-surface hover:bg-opacity-90 transition-all font-bold uppercase tracking-wider text-label-md active:scale-95">
              Start Free Trial
            </button>
          </div>
          {/* Enterprise */}
          <div className="bg-surface-container-low border border-outline-variant rounded-xl p-8 flex flex-col hover:border-on-surface-variant transition-all duration-300">
            <div className="mb-stack-lg">
              <span className="font-label-md text-label-md text-on-primary-container uppercase tracking-widest mb-2 block">Full Compliance Control</span>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">Enterprise</h2>
              <div className="flex items-baseline gap-1 mt-4">
                <span className="font-headline-lg text-headline-lg text-on-surface">Custom Pricing</span>
              </div>
            </div>
            <ul className="space-y-stack-md flex-grow mb-stack-lg">
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for security icon */}
                <div className="flex items-center">
                  <span>🔒</span>
                </div>
                <span className="text-on-surface">Full RBAC Controls</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for lock icon */}
                <div className="flex items-center">
                  <span>🔐</span>
                </div>
                <span className="text-on-surface">Custom AI Guardrails</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for lan icon (using globe as placeholder) */}
                <div className="flex items-center">
                  <span>🌐</span>
                </div>
                <span className="text-on-surface">Unlimited Transactions</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for cloud_sync icon */}
                <div className="flex items-center">
                  <span>☁️</span>
                </div>
                <span className="text-on-surface">Self-hosted Deployments</span>
              </li>
              <li className="flex items-start gap-stack-sm">
                {/* Using div as placeholder for support_agent icon */}
                <div className="flex items-center">
                  <span>🎧</span>
                </div>
                <span className="text-on-surface">Dedicated Account Manager</span>
              </li>
            </ul>
            <button className="w-full py-stack-md bg-on-surface text-background hover:bg-primary transition-colors font-bold uppercase tracking-wider text-label-md">
              Contact Sales
            </button>
          </div>
        </div>
        {/* Detailed Comparison */}
        <section className="mt-stack-lg">
          <h2 className="font-headline-lg text-headline-lg text-on-surface text-center mb-stack-lg">Explainability Features</h2>
          <div className="bg-surface-container-low rounded-lg border border-outline-variant overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="font-label-md text-label-md text-on-surface">
                  <th className="p-6 font-label-md text-label-md text-on-surface">
                    Feature
                  </th>
                <th className="p-6 font-label-md text-label-md text-on-surface text-center">
                  Starter
                </th>
                <th className="p-6 font-label-md text-label-md text-on-surface text-center">
                  Professional
                </th>
                <th className="p-6 font-label-md text-label-md text-on-surface text-center">
                  Enterprise
                </th>
              </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                <tr>
                  <td className="p-6">
                    <p className="font-body-md font-bold text-on-surface">Reasoning Graph</p>
                    <p className="text-sm text-on-surface-variant">Visual trace of AI decision nodes</p>
                  </td>
                  <td className="p-6 text-center text-on-surface-variant">Basic logs</td>
                  <td className="p-6 text-center text-investigation-gold">
                    {/* Using div as placeholder for account_tree icon */}
                    <div className="flex items-center">
                      <span>🌳</span>
                    </div>
                  </td>
                  <td className="p-6 text-center text-investigation-gold">
                    {/* Using div as placeholder for account_tree icon */}
                    <div className="flex items-center">
                      <span>🌳</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td className="p-6">
                    <p className="font-body-md font-bold text-on-surface">Audit Evidence</p>
                    <p className="text-sm text-on-surface-variant">Direct source linking for every score</p>
                  </td>
                  <td className="p-6 text-center text-on-surface-variant">
                    {/* Using div as placeholder for check icon */}
                    <div className="flex items-center">
                      <span>✅</span>
                    </div>
                  </td>
                  <td className="p-6 text-center text-on-surface">
                    {/* Using div as placeholder for check icon */}
                    <div className="flex items-center">
                      <span>✅</span>
                    </div>
                  </td>
                  <td className="p-6 text-center text-on-surface">
                    {/* Using div as placeholder for check icon */}
                    <div className="flex items-center">
                      <span>✅</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td className="p-6">
                    <p className="font-body-md font-bold text-on-surface">Custom Guardrails</p>
                    <p className="text-sm text-on-surface-variant">Define strict logic bounds for AI</p>
                  </td>
                  <td className="p-6 text-center">—</td>
                  <td className="p-6 text-center text-on-surface-variant">
                    {/* Using div as placeholder for gpp_maybe icon (using question mark) */}
                    <div className="flex items-center">
                      <span>❓</span>
                    </div>
                  </td>
                  <td className="p-6 text-center text-risk-low">
                    {/* Using div as placeholder for gpp_maybe icon (using check mark) */}
                    <div className="flex items-center">
                      <span>✅</span>
                    </div>
                  </td>
                </tr>
                <tr>
                  <td className="p-6">
                    <p className="font-body-md font-bold text-on-surface">Historical Correlation</p>
                    <p className="text-sm text-on-surface-variant">Pattern matching across past 24 months</p>
                  </td>
                  <td className="p-6 text-center">3 months</td>
                  <td className="p-6 text-center text-on-surface">12 months</td>
                  <td className="p-6 text-center text-on-surface">Unlimited</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        {/* Bento Grid Proof Points */}
        <section className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-2 bg-surface-container-high border border-outline-variant p-stack-lg rounded-xl flex items-center gap-stack-lg">
            <div className="w-1/3">
              {/* Using div as placeholder for the icon */}
              <div className="flex items-center">
                <span>🧠</span>
              </div>
            </div>
            <div className="w-2/3">
              <h3 className="font-headline-md text-headline-md text-on-surface mb-2">Deterministic Reasoning</h3>
              <p className="text-on-surface-variant">Every risk score generated by FFIRE is backed by an auditable execution trace. Move beyond black-box AI with our unique reasoning graph architecture.</p>
            </div>
          </div>
          <div className="bg-surface-container-low border border-outline-variant p-stack-lg rounded-xl flex flex-col justify-center">
            <div className="text-display-lg font-display-lg text-investment-gold mb-2">99.8%</div>
            <p className="font-label-md text-label-md text-on-surface uppercase mb-1">Investigation Accuracy</p>
            <p className="text-sm text-on-surface-variant">Validated by Top 5 global neo-banks.</p>
          </div>
        </section>
        {/* Final CTA */}
        <section className="mt-24 text-center bg-primary-container p-16 rounded-2xl border border-primary/20 relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            {/* Placeholder for background pattern */}
          </div>
          <div className="relative z-10">
            <h2 className="font-headline-lg text-headline-lg text-on-surface mb-stack-md">Ready to secure your fintech?</h2>
            <p className="font-body-lg text-body-lg text-on-surface-variant mb-stack-lg max-w-xl mx-auto">
              Join hundreds of financial institutions using FFIRE to detect fraud with absolute transparency.
            </p>
            <div className="flex flex-col sm:flex-row gap-gutter justify-center">
              <button className="px-8 py-4 bg-investment-gold text-surface font-bold rounded hover:opacity-90 transition-all active:scale-95 shadow-lg">
                START FREE TRIAL
              </button>
              <button className="px-8 py-4 border border-on-surface text-on-surface font-bold rounded hover:bg-surface-container-high transition-all">
                TALK TO AN EXPERT
              </button>
            </div>
          </div>
        </section>
      </main>
      {/* Footer */}
      <footer className="border-t border-outline-variant bg-surface py-12 px-margin mt-12">
        <div className="max-w-container-max mx-auto flex flex-col md:flex-row justify-between items-start gap-stack-lg">
          <div className="max-w-sm">
            <span className="font-headline-md text-headline-md font-bold text-investigation-gold mb-4 block">FFIRE</span>
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