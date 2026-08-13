---
name: FFIRE Precision Ledger
colors:
  surface: '#081425'
  surface-dim: '#081425'
  surface-bright: '#2f3a4c'
  surface-container-lowest: '#040e1f'
  surface-container-low: '#111c2d'
  surface-container: '#152031'
  surface-container-high: '#1f2a3c'
  surface-container-highest: '#2a3548'
  on-surface: '#d8e3fb'
  on-surface-variant: '#c6c6cd'
  inverse-surface: '#d8e3fb'
  inverse-on-surface: '#263143'
  outline: '#909097'
  outline-variant: '#45464d'
  surface-tint: '#bec6e0'
  primary: '#bec6e0'
  on-primary: '#283044'
  primary-container: '#0f172a'
  on-primary-container: '#798098'
  inverse-primary: '#565e74'
  secondary: '#ffb77d'
  on-secondary: '#4d2600'
  secondary-container: '#d97707'
  on-secondary-container: '#432100'
  tertiary: '#b7c8e1'
  on-tertiary: '#213145'
  tertiary-container: '#06182b'
  on-tertiary-container: '#728299'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#ffdcc3'
  secondary-fixed-dim: '#ffb77d'
  on-secondary-fixed: '#2f1500'
  on-secondary-fixed-variant: '#6e3900'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#081425'
  on-background: '#d8e3fb'
  surface-variant: '#2a3548'
  risk-low: '#10B981'
  risk-medium: '#F59E0B'
  risk-high: '#EF4444'
  investigation-gold: '#FCD34D'
  graph-node-bg: '#334155'
  graph-edge: '#475569'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin: 32px
  container-max: 1440px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The brand personality is **Technical, Transparent, and Authoritative**. As an enterprise fintech tool, the design system must facilitate high-stakes decision-making where speed and correctness are balanced. The UI should evoke a sense of "Deterministic Design"—where every piece of information is grounded in evidence and every AI-generated conclusion is auditable.

The chosen design style is **Corporate / Modern** with a focus on **Tonal Layering**. It prioritizes information density and clarity over decorative elements. The aesthetic reflects a "Command Center" environment: professional, calm, and highly organized. We use crisp geometry and subtle depth to separate orchestration logic (the "Graph") from data evidence (the "Grids").

- **Trustworthiness:** Achieved through stable, balanced layouts and a conservative color palette.
- **Precision:** Communicated via hairline borders, monospaced data tokens, and strict alignment.
- **Auditability:** Reinforced by a clear "paper trail" visual hierarchy and explicit status indicators.

## Colors

The system uses a **Dark Mode** default to reduce eye strain for investigators performing long-form analysis. 

- **Primary & Neutral:** A foundation of deep navy (`#0F172A`) and slate grays (`#1E293B`) provides a high-contrast environment for data.
- **Investigation Gold:** Used exclusively for high-value highlights, active trace paths in the execution graph, and "pinned" evidence. 
- **Risk Tiers:** A strict semantic system for risk assessment:
    - **Green (Low):** Automated clearance, safe transactions.
    - **Amber (Medium):** Periodic review, flagged for observation.
    - **Red (High):** Immediate human intervention required.
- **Functional Grays:** Slate grays are used to differentiate between the "Canvas" (background) and "Surfaces" (cards, panels).

## Typography

Typography is categorized into three distinct roles to ensure readability in a data-dense application:

1.  **Headlines (Hanken Grotesk):** Clean, sharp, and modern. Used for section titles and dashboard headers to provide a professional, authoritative structure.
2.  **Body (Inter):** A systematic, utilitarian sans-serif chosen for its exceptional legibility at small sizes within data grids and evidence cards.
3.  **Labels & Data (JetBrains Mono):** Used for "Reasoning Tokens," transaction IDs, and the LangGraph execution trace. The monospaced nature emphasizes technical precision and helps analysts scan for patterns in alphanumeric strings.

**Hierarchy Note:** Use `label-sm` for all metadata caps (e.g., "TIMESTAMP", "ACTOR") to maintain a structured, engineering-led aesthetic.

## Layout & Spacing

The layout follows a **Fixed Grid** model for the primary dashboard to ensure a stable viewing experience for complex data, transitioning to a **Fluid Grid** within specialized panels like the Reasoning Graph.

- **Grid System:** A 12-column grid is used for desktop. 
    - **Evidence Sidebar:** Occupies 3 columns.
    - **Main Investigation Workspace:** Occupies 9 columns.
- **Rhythm:** A 4px baseline grid ensures tight, consistent alignment of data rows. 
- **Adaptability:**
    - **Desktop (1280px+):** Full multi-pane view with side-by-side graph and evidence logs.
    - **Tablet (768px - 1279px):** Collapsible sidebar; graph view switches to a vertical stack or drill-down pattern.
    - **Mobile (Below 768px):** Single-column focus on high-risk alerts and summary scores; complex visualizations are replaced with simplified summary cards.

## Elevation & Depth

Visual hierarchy is established through **Tonal Layers** rather than heavy shadows, maintaining a sleek, professional "SaaS" appearance.

- **Level 0 (Base):** Deepest navy (`#0F172A`). Used for the main application background.
- **Level 1 (Surface):** Neutral slate (`#1E293B`). Used for large cards, container backgrounds, and inactive panels.
- **Level 2 (Active/Raised):** Lighter slate (`#334155`). Used for hovered states, active nodes in the LangGraph, and modal overlays.
- **Outlines:** Instead of shadows, use 1px solid borders (`#475569`) to define boundaries. This creates a "blueprint" feel that matches the engineering-centric purpose of the tool.
- **Gradients:** Subtle linear gradients (10% opacity) may be used within Risk Gauges to suggest movement, but are otherwise avoided.

## Shapes

The system uses **Soft (Level 1)** roundedness (0.25rem / 4px) to balance professional rigidity with modern UI sensibilities.

- **Primary Components:** Buttons, Input Fields, and Evidence Cards use a 4px radius.
- **Graph Nodes:** Use a 4px radius for process steps, but maintain **Sharp (0px)** edges for database or "Hard Data" entities to differentiate between logic flows and static storage.
- **Status Pills:** Use **Pill-shaped (Level 3)** roundedness to clearly distinguish them from interactive buttons or data fields.

## Components

### Data Grids
Grids are the primary tool for analysts. Use `body-sm` for row content and `label-sm` for headers. Use alternating row stripes (subtle tonal shift) and "Investigation Gold" for the text of high-confidence matches.

### Evidence Cards
Structured containers that display "Reasoning Tokens" (e.g., `[device.first_seen]`). These should use a 1px border and a mono-font header to signal they are auditable snippets of data.

### Risk Score Gauges
Circular or semi-circular progress indicators. The stroke color must map strictly to the Risk Tier colors (Green, Amber, Red). The central text should use `headline-lg`.

### LangGraph Execution Trace
- **Nodes:** Rectangular cards with a mono-font label. Active nodes should have an "Investigation Gold" border.
- **Edges:** 1px lines (`graph-edge`). Use animated dashed lines to show "Processing" states.
- **Reasoning Tooltip:** On hovering over a node, a Level 2 elevation card appears showing the prompt/logic used for that specific step.

### Buttons & Inputs
- **Primary Button:** Solid `tertiary` or `primary` with a 1px border. High-action buttons (e.g., "APPROVE") use Risk Low green.
- **Ghost Buttons:** Used for secondary actions like "Add Note" or "View Audit Log" to reduce visual clutter in dense screens.
- **Inputs:** Dark backgrounds with a slightly lighter border. Active state uses a 1px "Investigation Gold" ring.