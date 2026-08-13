# FFIRE - Screen-by-Screen Specifications

This document contains the complete UI/UX and Frontend Engineering specifications for the FFIRE platform, detailing every screen, layout, component, state, and interaction.

---

## Part 1: Authentication & Onboarding

### Screen 1: Login Screen
**Purpose**: Secure entry point into the FFIRE platform using JWT and MFA.
**Target Users**: All Users (Analysts, Compliance, Admins, Execs).

**Wireframe / Layout**:
- Split screen: Left side features a high-quality abstract dark-themed graphic or branding (e.g., glowing nodes or a subtle reasoning graph animation). Right side contains the login form centrally aligned.
- Top Right: Theme toggle (Dark/Light).

**Components**:
- **Logo**: FFIRE Enterprise Logo (Top left of the form).
- **Form Card**:
  - **Email Field**: Standard input with envelope icon.
  - **Password Field**: Obfuscated input with eye toggle to view.
  - **Login Button**: Full width, primary brand color (e.g., Blue gradient).
  - **Forgot Password Link**: Subtle text below the button.
  - **SSO Options**: "Login with Okta", "Login with Microsoft Entra ID".

**Interactions & States**:
- **Loading State**: Login button shows a subtle skeleton pulse or a small loading spinner, text changes to "Authenticating...".
- **Error State**: Inline red text above the form. Fields with errors get a red border.
- **Empty State**: Login button disabled if email/password are empty.

**API Mapping**:
- `POST /api/v1/auth/login`
  - Payload: `{ "email": "", "password": "" }`
  - Response: JWT Token or MFA challenge token.

**AI Prompts**:
> Create a professional enterprise login screen for a financial fraud platform. Split layout with a dark theme. The left side has a subtle glowing node animation representing AI. The right side has a minimal, glassmorphic login card. Primary button is a vibrant blue. Includes SSO options for Okta and Microsoft.

---

### Screen 2: Multi-Factor Authentication (MFA) & Password Reset
**Purpose**: Secondary authentication layer to meet banking security standards.

**Wireframe / Layout**:
- Same layout as Login (Split screen).

**Components**:
- **MFA Code Input**: 6-digit OTP input boxes. Auto-advances focus.
- **Verify Button**: Primary action.
- **Resend Code Link**: Counter (e.g., "Resend in 30s").

**Interactions & States**:
- **Validation**: Only accepts numeric input. Verify button enables after 6 digits.
- **Error State**: "Invalid Code" toast notification, input boxes shake horizontally.

**API Mapping**:
- `POST /api/v1/auth/mfa/verify`
  - Payload: `{ "challenge_token": "...", "code": "123456" }`

---

## Part 2: Core Dashboard

### Screen 3: Main Dashboard
**Purpose**: The central hub providing a high-level overview of investigations, metrics, and alerts.

**Wireframe / Layout**:
- **Top Navigation**: Logo, Global Search bar, Notifications Bell, User Profile avatar.
- **Left Sidebar**: Expandable/collapsible menu with icons (Dashboard, Investigations, Evidence, etc.).
- **Main Content**: Grid layout. 
  - Top row: 4 KPI Summary Cards.
  - Middle row: Fraud Distribution Chart (2/3 width) and Recent Alerts (1/3 width).
  - Bottom row: Recent Investigations Table (Full width).

**Components**:
- **Summary Cards**:
  - "Pending Cases", "Completed Cases", "High Risk Alerts", "Average Confidence Score".
  - Include micro-charts (sparklines) showing 7-day trends.
- **Activity Feed**: Timeline of system and team events on the right panel.
- **Fraud Distribution Chart**: Dark-themed bar chart showing fraud vs. genuine transactions over 30 days.
- **Recent Investigations Table**: Columns for ID, Merchant, Risk Score, Status.

**Buttons & Actions**:
- `Start Investigation` (Top Right): Opens the Start Investigation modal. Visibility: Analysts, Admins.

**API Mapping**:
- `GET /api/v1/dashboard/metrics` (KPIs)
- `GET /api/v1/dashboard/charts` (Chart data)
- `GET /api/v1/investigations/recent` (Table data)

**AI Prompts**:
> Create an enterprise fintech dashboard in dark mode. Top navbar with search and profile. Left sidebar navigation. Main area contains 4 summary cards with sparklines. Below that, a beautiful dark-themed bar chart for fraud distribution, and a recent investigations table. Use Stripe/Linear design aesthetic with rounded corners and soft borders.

---

## Part 3: Investigation Module

### Screen 4: Transaction Search
**Purpose**: Quickly locate a specific transaction to begin or review an investigation.

**Wireframe / Layout**:
- Clean, focused center layout (similar to Google search or Spotlight search).

**Components**:
- **Hero Search Bar**: Large, centered input field. Placeholder: "Search by Transaction ID, Customer, or Merchant...".
- **Filters**: Dropdowns under the search bar (Date Range, Amount, Status).
- **Auto-Suggestions**: Dropdown listing matching transactions as the user types.
- **Recent Searches**: Displayed when the input is focused and empty.

**Interactions & States**:
- **Loading State**: Skeleton rows in the dropdown.
- **Empty State**: "No transactions found. Try adjusting your filters." with an illustration.

**API Mapping**:
- `GET /api/v1/transactions/search?q={query}&filters={}`

---

### Screen 5: Investigation Queue
**Purpose**: Manage and filter all assigned, pending, and completed investigations.

**Wireframe / Layout**:
- Standard data-grid page layout. Header with title and actions, full-page table.

**Components**:
- **Advanced Filters**: Slide-out panel or top row dropdowns for Risk Level, Confidence, Analyst, Status.
- **Data Table**:
  - Columns: Investigation ID, Customer, Merchant, Risk Score (color-coded badge), Confidence (progress bar), Status (badge), Analyst, Created.
  - Row Actions: Open, Reassign, Export, Delete (Admin only).
- **Pagination Controls**: Bottom of the table (Rows per page, Next/Prev).

**Interactions & States**:
- **Hover**: Table rows highlight slightly on hover.
- **Click**: Clicking a row routes to `Screen 7: Investigation Details`.

**API Mapping**:
- `GET /api/v1/investigations?page=1&limit=50&status=PENDING`

---

### Screen 6: Live Investigation Progress
**Purpose**: View the LangGraph AI reasoning engine working in real-time.

**Wireframe / Layout**:
- Focused view. A vertical timeline or terminal-like execution view in the center, with a pulsing status indicator at the top.

**Components**:
- **Status Header**: "Investigation Running..." with a glowing animation.
- **Live Event Feed**:
  - `[Customer Retrieval] Fetching history... DONE`
  - `[Location] Checking IP mismatch... DONE`
  - `[Reasoning] Analyzing risk factors... IN PROGRESS`
- **Progress Bar**: Determinate or indeterminate based on graph depth.
- **Cancel Button**: To abort the execution manually.

**API Mapping**:
- `WebSocket /ws/investigations/{id}/stream`

---

### Screen 7: Investigation Details - Summary
**Purpose**: Provide a comprehensive overview of a completed AI investigation so the analyst can make a decision.

**Wireframe / Layout**:
- Top Header: Investigation ID, Status Badge, High-level Actions (Approve, Reject, Export).
- Main Grid: 
  - Left Col (70%): Investigation Summary, Risk Factors list, AI Recommendation.
  - Right Col (30%): Entity Cards (Customer, Merchant, Device summary).

**Components**:
- **Risk & Confidence Scorecards**: Large numerical displays with gauge charts.
- **AI Recommendation Box**: Highlighted panel explaining *why* the transaction was flagged in natural language.
- **Action Buttons**: 
  - `Mark as Fraud` (Red button).
  - `Mark as Genuine` (Green button).
  - Both require a confirmation modal with a "Notes" field.

**API Mapping**:
- `GET /api/v1/investigations/{id}/summary`

---

### Screen 8: Investigation Details - Timeline
**Purpose**: Show the chronological sequence of events for the transaction and the customer's recent history.

**Wireframe / Layout**:
- Replaces the main grid of Screen 7 via a local tab navigation (Summary | Timeline | Graph | Report).

**Components**:
- **Vertical Timeline**: 
  - Nodes represent events (e.g., Login, Password Change, Transaction Attempt).
  - Each node shows timestamp, IP address, and an icon.
  - Suspicious events are highlighted with a red dot or border.

**Interactions & States**:
- Click a timeline node to expand and see raw JSON payload or deeper details.

---

### Screen 9: Investigation Details - Reasoning Graph
**Purpose**: Visually map the AI's LangGraph execution path for total explainability.

**Wireframe / Layout**:
- Full canvas view within the tab.

**Components**:
- **Interactive Node Graph**: Uses a library like React Flow.
- **Nodes**: Represent AI agents/tools (e.g., "Location Validator", "Risk Analyzer").
- **Edges**: Show data flow with animated dashed lines.
- **Side Panel**: Clicking a node opens a right drawer showing the exact input/output of that specific AI step.

**API Mapping**:
- `GET /api/v1/investigations/{id}/graph`

---

### Screen 10: Investigation Details - Report Generation
**Purpose**: Generate, preview, and download compliance-ready audit reports.

**Wireframe / Layout**:
- Split view. Left side: Report configuration. Right side: PDF Preview.

**Components**:
- **Configuration Panel**: Checkboxes for what to include (Evidence, Graph, Analyst Notes, Raw Logs).
- **Export Buttons**: `Download PDF`, `Download JSON`, `Share Link`.
- **Document Viewer**: An embedded PDF or HTML preview of the final report.

**API Mapping**:
- `POST /api/v1/investigations/{id}/report`

---

## Part 4: Evidence Viewer

### Screen 11: Evidence - Customer Profile
**Purpose**: Deep dive into the customer's historical standing and account details.

**Wireframe / Layout**:
- Standard page with left sidebar navigation. Inside Evidence, a secondary navigation bar (Tabs or Sub-sidebar) for the specific evidence types.

**Components**:
- **Profile Header**: Avatar, Name, Account Number, KYC Status.
- **Historical KPI Cards**: Lifetime Value, Account Age, Total Disputes.
- **Historical Transactions Table**: List of past transactions by this customer.
- **Linked Accounts Panel**: Shows if this customer shares IP/Device with other accounts.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/customer`

---

### Screen 12: Evidence - Merchant Profile
**Purpose**: Analyze the merchant's risk profile to see if they are a common vector for fraud.

**Wireframe / Layout**:
- Similar layout to Customer Profile tab.

**Components**:
- **Merchant Details**: Name, Category Code (MCC), Country.
- **Merchant Risk Metrics**: Global Fraud Rate (gauge chart), Chargeback Ratio.
- **Velocity Chart**: Spike in recent transactions.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/merchant`

---

### Screen 13: Evidence - Device Intelligence
**Purpose**: Inspect the physical device used for the transaction.

**Wireframe / Layout**:
- Data-heavy grid with icon indicators for good/bad signals.

**Components**:
- **Device Fingerprint**: OS, Browser, Screen Resolution, Language.
- **Mismatch Alerts**: Highlights if the device OS doesn't match the historical norm (e.g., usually uses iOS, now using Windows).
- **VPN / Proxy Detection**: Badge indicating if the IP belongs to a known proxy.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/device`

---

### Screen 14: Evidence - Location & Velocity
**Purpose**: Visualize geographic data and detect impossible travel (velocity).

**Wireframe / Layout**:
- Top half: Interactive Map. Bottom half: Velocity analysis table.

**Components**:
- **Map View**: Plots the billing address, shipping address, and current IP location. Lines connect them if distance is suspicious.
- **Distance Calculation Box**: E.g., "500 miles from last login 10 minutes ago (Impossible Travel)".
- **IP Information**: ASN, ISP, coordinates.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/location`

---

### Screen 15: Evidence - Historical Fraud Cases
**Purpose**: Compare the current transaction to known fraud signatures.

**Wireframe / Layout**:
- Side-by-side comparison view or a table of similar cases.

**Components**:
- **Similarity Score Badge**: E.g., "85% match with Case #9932".
- **Matching Factors List**: Explains *why* it's similar (e.g., Same IP subnet, same device type, same merchant).
- **Link to Past Cases**: Clickable IDs to open historical reports in a new tab.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/historical`

---

### Screen 16: Evidence - Document Attachments
**Purpose**: Store and view uploaded PDFs, receipts, or external compliance documents.

**Wireframe / Layout**:
- File manager layout (Grid of thumbnails or list view).

**Components**:
- **Drag-and-Drop Zone**: Upload new evidence.
- **Document List**: File name, uploaded by, date, size.
- **Preview Modal**: Opens PDFs/Images directly in the browser without downloading.

**API Mapping**:
- `GET /api/v1/investigations/{id}/evidence/documents`
- `POST /api/v1/investigations/{id}/evidence/documents`

---

## Part 5: Knowledge Base & Analytics

### Screen 17: Knowledge Base
**Purpose**: Searchable SOPs, guidelines, and compliance rules for analysts.

**Wireframe / Layout**:
- Left Sidebar: Document tree (Categories > Articles). Right side: Markdown/Rich text article viewer.

**Components**:
- **Search Bar**: Instant full-text search across all SOPs.
- **Article Viewer**: Displays formatted text, tables, and images.
- **Edit Button (Admin)**: To update SOPs directly in the UI.

**API Mapping**:
- `GET /api/v1/kb/articles`

---

### Screen 18: Analytics & Trends
**Purpose**: High-level reporting for Executives and Managers.

**Wireframe / Layout**:
- Full width dashboard focused purely on charts and aggregate data.

**Components**:
- **Global Fraud Map**: Heatmap of where fraudulent transactions originate.
- **Analyst Productivity Table**: Cases resolved per analyst, average resolution time.
- **System Accuracy Chart**: Line chart comparing AI confidence vs. final human decision (measuring false positives).
- **Export CSV/PDF Button**.

**API Mapping**:
- `GET /api/v1/analytics/trends`

---

## Part 6: Audit & Notifications

### Screen 19: Audit Logs Viewer
**Purpose**: Immutable log of every action taken in the system for compliance.

**Target Users**: Compliance Officers, Admins.

**Wireframe / Layout**:
- Dense, tabular data view optimized for reading logs.

**Components**:
- **Log Table**: Timestamp, User, Action (e.g., "APPROVED_FRAUD", "VIEWED_EVIDENCE"), Target ID, IP Address.
- **Advanced Query Builder**: Filter by User, Date Range, Action Type.
- **JSON Payload Viewer**: Expand a row to see the exact API payload of the action.

**API Mapping**:
- `GET /api/v1/audit/logs`

---

### Screen 20: Compliance Report Exporter
**Purpose**: Generate bulk reports across multiple investigations for regulators.

**Wireframe / Layout**:
- Single form page centered on the screen.

**Components**:
- **Date Range Picker**: Standard calendar input.
- **Format Selector**: PDF, CSV, JSON.
- **Generate Button**: Triggers a long-running background task.
- **Download History Table**: List of previously generated reports available for download.

**API Mapping**:
- `POST /api/v1/audit/export`

---

### Screen 21: Notification Center
**Purpose**: View and manage system alerts, assignments, and escalations.

**Wireframe / Layout**:
- Slide-out drawer (accessed from Top Nav bell icon) or a full page inbox.

**Components**:
- **Notification List**: E.g., "You have been assigned Case #1029", "System Update at 2 AM".
- **Unread Badges**: Blue dot for unread.
- **Mark All as Read Button**.

**API Mapping**:
- `GET /api/v1/notifications`
---

## Part 7: Settings & Administration

### Screen 22: User Profile & Preferences
**Purpose**: Manage personal settings and active sessions.

**Wireframe / Layout**:
- Left nav (Profile, Preferences, Security), Right content area.

**Components**:
- **Theme Toggle**: Dark, Light, System.
- **Language/Timezone Selectors**.
- **Active Sessions Table**: List of devices logged into this account, with a "Revoke" button.

**API Mapping**:
- `GET /api/v1/users/me`

---

### Screen 23: Admin - User Management
**Purpose**: Invite, suspend, and manage staff accounts.

**Wireframe / Layout**:
- Table view with an "Invite User" modal.

**Components**:
- **User Table**: Name, Email, Role, Status (Active/Suspended), Last Login.
- **Action Menu (Three dots)**: Edit Role, Suspend, Reset MFA.
- **Invite Modal**: Email input and Role dropdown.

**API Mapping**:
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users/invite`

---

### Screen 24: Admin - Roles & Permissions (RBAC)
**Purpose**: Define what each role can access.

**Wireframe / Layout**:
- Matrix/Grid layout.

**Components**:
- **Roles Column**: Fraud Analyst, Senior Analyst, Compliance, Admin.
- **Permissions Rows**: Create Investigation, Delete Logs, Export Data, etc.
- **Checkboxes**: Intersecting grid to toggle permissions.

**API Mapping**:
- `GET /api/v1/admin/roles`
- `PATCH /api/v1/admin/roles/{id}`

---

### Screen 25: Admin - API Keys & Integrations
**Purpose**: Manage authentication keys for external services (e.g., Data providers, LLMs).

**Wireframe / Layout**:
- Card-based layout for each integration.

**Components**:
- **Integration Cards**: Stripe, OpenAI, GeoIP Service, Datadog.
- **Status Indicator**: Green (Connected), Red (Failed).
- **Edit Keys Modal**: Obfuscated input for secret keys.

**API Mapping**:
- `GET /api/v1/admin/integrations`

---

### Screen 26: Admin - Threshold Configuration
**Purpose**: Tune the AI without changing code.

**Wireframe / Layout**:
- Form page with sliders and numeric inputs.

**Components**:
- **Auto-Approve Threshold**: Slider (e.g., >95% confidence).
- **Human Review Threshold**: Slider (e.g., <80% confidence).
- **Save Configuration Button**: Applies immediately to the rule engine.

**API Mapping**:
- `GET /api/v1/admin/config/thresholds`

---

### Screen 27: Admin - AI Models & Settings
**Purpose**: Select which LLMs and Vector DBs power the reasoning engine.

**Wireframe / Layout**:
- Form page.

**Components**:
- **Model Selector Dropdown**: e.g., GPT-4o, Claude-3.5-Sonnet, Llama-3.
- **Vector DB Status**: Connection ping to Pinecone or Milvus.
- **System Prompt Editor**: Read-only (or admin editable) view of the master system prompt used in the LangGraph.

**API Mapping**:
- `GET /api/v1/admin/config/ai`

---

### Screen 28: Admin - System Monitoring & Health
**Purpose**: Ensure the platform is running smoothly.

**Wireframe / Layout**:
- Grid of real-time charts.

**Components**:
- **Service Status Indicators**: Database, Redis, LLM API, Web UI.
- **Latency Charts**: API response times.
- **Error Rate Gauge**: Spikes turn red if errors > 1%.

**API Mapping**:
- `GET /api/v1/admin/monitoring/health`

---

### Screen 29: Admin - Security & Policies
**Purpose**: Manage global security constraints.

**Wireframe / Layout**:
- Form page.

**Components**:
- **MFA Policy Toggle**: "Require MFA for all users".
- **Session Timeout**: Numeric input (e.g., "Logout after X minutes of inactivity").
- **IP Whitelist/Blacklist**: Text area to enter CIDR blocks.

**API Mapping**:
- `GET /api/v1/admin/security/policies`

---

### Screen 30: Admin - Event & Webhook Logs
**Purpose**: Debug integrations and external webhooks.

**Wireframe / Layout**:
- Tabular log viewer, similar to Audit Logs but for system events.

**Components**:
- **Event List**: Timestamp, Event Name (e.g., `transaction.created`), Status Code (e.g., 200, 500).
- **Payload Inspector**: Split view to see exactly what JSON was sent/received.
- **Retry Button**: Manually replay a failed webhook.

**API Mapping**:
- `GET /api/v1/admin/webhooks/logs`

---
**End of Document**
