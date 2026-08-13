# FFIRE - Fully Detailed Component Library Specification

This document provides an exhaustive, production-ready specification for every button, section, table, and popup within the FFIRE platform, including the developer and AI Prompts necessary for automated code generation.

---

## 1. Every Button

### 1.1 Start Investigation Button
- **Name**: Start Investigation
- **Visibility**: Fraud Analyst, Senior Analyst, Admin
- **Role Permissions**: `investigation:create`
- **Visuals**: Blue gradient background, Rocket icon on the left, white text.
- **Hover Animation**: Scale up 1.02x, gradient brightness +10%.
- **Click Animation**: Scale down 0.98x.
- **When Clicked**:
  ↓
  Open Investigation Wizard Modal
  ↓
  Ask for Transaction ID & Priority
  ↓
  Validate input length (must be > 5 chars)
  ↓
  Call API `POST /api/v1/investigations`
  ↓
  Loading animation: Button text changes to "Initializing..." with spinner
  ↓
  Success Behavior: Show "Investigation Started" toast message
  ↓
  Redirect Page: `/investigations/{new_id}/live`
- **Failure Behavior**: Show error toast, highlight input in red.
**AI / Developer Prompt**:
> Create a Start Investigation Button. Use a blue gradient background with a rocket icon on the left and white text. Add a 1.02x hover scale animation and a 0.98x click scale animation. When clicked, it must open a modal asking for Transaction ID and Priority. Show a loading spinner during API calls, and handle both success toast redirects and error highlighting.

### 1.2 Mark as Fraud Button
- **Name**: Mark as Fraud
- **Visibility**: Fraud Analyst, Senior Analyst
- **Role Permissions**: `investigation:resolve`
- **Visuals**: Solid Red (`#D32F2F`), Shield-alert icon.
- **When Clicked**:
  ↓
  Open "Confirm Fraud Decision" Popup
  ↓
  Ask for Mandatory Justification Note
  ↓
  Validate note length > 10 chars
  ↓
  Call API `PATCH /api/v1/investigations/{id}/status` with `{"status": "FRAUD", "note": "..."}`
  ↓
  Success Behavior: Toast "Investigation closed as Fraud"
  ↓
  Redirect Page: `/investigations/queue`
**AI / Developer Prompt**:
> Create a Mark as Fraud Button. Solid Red (#D32F2F) with a shield-alert icon. When clicked, open a confirmation popup asking for a mandatory justification note (>10 chars). Call the PATCH API, show a success toast, and redirect to the queue on success.

### 1.3 Mark as Genuine Button
- **Name**: Mark as Genuine
- **Visibility**: Fraud Analyst, Senior Analyst
- **Role Permissions**: `investigation:resolve`
- **Visuals**: Solid Green (`#2E7D32`), Shield-check icon.
- **When Clicked**:
  ↓
  Open "Confirm Genuine Decision" Popup
  ↓
  Ask for Justification Note (Optional unless overriden AI)
  ↓
  Call API `PATCH /api/v1/investigations/{id}/status` with `{"status": "GENUINE"}`
  ↓
  Success Behavior: Toast "Investigation closed as Genuine"
  ↓
  Redirect Page: `/investigations/queue`
**AI / Developer Prompt**:
> Create a Mark as Genuine Button. Solid Green (#2E7D32) with a shield-check icon. When clicked, open a popup for an optional justification note. Patch the API on confirm, show a toast, and redirect to the queue.

### 1.4 Export Report Button
- **Name**: Export PDF
- **Visibility**: All Roles
- **Visuals**: Outlined secondary button, Download icon.
- **When Clicked**:
  ↓
  Open "Export Options" Modal
  ↓
  Select format (PDF/JSON) & Sections (Evidence, Graph, Audit)
  ↓
  Call API `POST /api/v1/investigations/{id}/export`
  ↓
  Loading animation: Spinner on button "Generating PDF..."
  ↓
  Success Behavior: Trigger browser file download
  ↓
  Close Modal
**AI / Developer Prompt**:
> Create an Export PDF Button. Outline styling with a download icon. On click, open an Export Options modal with checkboxes for Evidence, Graph, and Audit. Call the export POST API and show a spinner on the button until the file downloads.

### 1.5 Reassign Case Button
- **Name**: Assign / Reassign
- **Visibility**: Senior Analyst, Admin
- **When Clicked**:
  ↓
  Open "Reassign Case" Modal
  ↓
  Fetch Analyst List (`GET /api/v1/users?role=analyst`)
  ↓
  Select User from Dropdown
  ↓
  Call API `PATCH /api/v1/investigations/{id}/assignee`
  ↓
  Success Behavior: Toast "Case assigned to {User}"
**AI / Developer Prompt**:
> Create a Reassign Case Button. On click, open a modal that fetches a list of analysts via API and displays them in a dropdown. Patch the investigation with the new assignee ID and show a success toast.

---

## 2. Every Section

### 2.1 Evidence Panel - Customer History
- **Contains**: 
  - Customer Name & Avatar
  - Account Age
  - KYC Status
  - Total Disputes (Lifetime)
  - Linked Accounts (Shared IPs)
- **Behavior**: Collapsible accordion. Default expanded.
- **Interactions**:
  - `Copy`: Clicking the Account ID copies it to clipboard.
  - `Download`: Export this specific pane to CSV.
  - `Highlight`: Suspicious metrics (e.g., High dispute rate) are highlighted with a red background pill.
**AI / Developer Prompt**:
> Create a Customer History Evidence Panel. Make it a collapsible accordion that is expanded by default. Display avatar, name, age, KYC status, disputes, and linked accounts. Add a click-to-copy feature for the Account ID and a red highlight for suspicious metrics.

### 2.2 Evidence Panel - Device Intelligence
- **Contains**:
  - Operating System
  - Browser & Version
  - Screen Resolution
  - VPN/Proxy Detection Status
- **Behavior**: Collapsible accordion.
- **Interactions**:
  - `Warning State`: If OS mismatches historical profile, the entire section header glows orange.
**AI / Developer Prompt**:
> Create a Device Intelligence Evidence Panel. Must be collapsible. Display OS, Browser, Resolution, and VPN Status. Add a warning state that makes the header glow orange if the OS prop mismatches the historical norm.

### 2.3 Reasoning Graph Viewer (Main Content)
- **Contains**:
  - Interactive React Flow Canvas
  - AI Nodes (Retrieval, Validator, Risk Analysis)
  - Zoom Controls, Fit to View
- **Interactions**:
  - `Click Node`: Opens a right-side drawer.
  - `Right Drawer`: Displays exact JSON Input, JSON Output, Latency, and Tokens used by that specific AI step.
**AI / Developer Prompt**:
> Create a Reasoning Graph Viewer using React Flow. Render nodes for Retrieval, Validator, and Risk Analysis with zoom controls. Clicking a node must open a right-side drawer displaying JSON input, output, latency, and tokens.

---

## 3. Every Table

### 3.1 Investigations Queue Table
- **Columns**:
  - `Investigation ID` (Clickable link to case)
  - `Customer` (Name + ID)
  - `Merchant`
  - `Risk Score` (Red > 80, Orange 50-80, Green < 50)
  - `Confidence` (Progress bar style)
  - `Status` (Badge: Pending, Review, Closed)
  - `Analyst` (Avatar + Name)
  - `Created At` (Relative time, e.g., "2 hours ago")
  - `Actions` (Three-dots dropdown)
- **Actions Menu**:
  - `Open` -> Routes to case details
  - `Continue` -> Routes to live execution viewer
  - `Export` -> Triggers export modal
  - `Assign` -> Triggers assign modal
  - `Delete` -> (Admin only) Triggers delete modal
- **Behaviors**:
  - `Sorting`: Click on Risk Score or Created At to sort.
  - `Pagination`: 50 items per page limit.
**AI / Developer Prompt**:
> Create an Investigations Queue Table. Include columns for ID, Customer, Merchant, Risk Score (colored badges), Confidence (progress bar), Status, Analyst, and Created At. Add a three-dots action menu for Open, Continue, Export, Assign, and Delete. Implement sorting for Risk Score and Created At, and pagination for 50 items per page.

### 3.2 Audit Logs Table
- **Columns**:
  - `Timestamp` (Exact UTC time)
  - `Actor` (User Email or "System")
  - `Action` (e.g., `INVESTIGATION_CREATED`, `LOGIN_FAILED`)
  - `Target Resource` (e.g., `INV-90231`)
  - `IP Address`
- **Actions Menu**:
  - `View Payload` -> Opens a modal showing the raw JSON event data.
- **Behaviors**:
  - `Filtering`: Date range picker, Actor search, Action multi-select.
**AI / Developer Prompt**:
> Create an Audit Logs Table. Display Timestamp (UTC), Actor, Action, Target Resource, and IP Address. Add a 'View Payload' action that opens a modal with raw JSON. Include a date range picker and actor search filter above the table.

---

## 4. Every Popup / Modal

### 4.1 Delete Investigation (Admin Only)
- **Title**: Delete Investigation
- **Warning Text**: "Are you sure you want to delete INV-8832? This action is irreversible and will permanently remove all associated evidence and logs."
- **Buttons**:
  - `Cancel` (Secondary outline, closes modal)
  - `Delete` (Primary Destructive Red, initiates deletion)
- **Loading State**: `Delete` button turns into a spinner. Modal backdrop prevents clicking outside.
- **Success Behavior**: Modal closes, Toast "Investigation Deleted", Table row fades out.
**AI / Developer Prompt**:
> Create a Delete Investigation Modal for Admins. Title: "Delete Investigation". Display warning text. Show a secondary Cancel button and a primary destructive red Delete button. When Delete is clicked, show a spinner, disable outside clicks, and show a success toast while fading out the associated row on close.

### 4.2 Start Investigation Wizard
- **Title**: New Investigation
- **Inputs**:
  - `Transaction ID` (Required, string)
  - `Priority` (Dropdown: Low, Medium, High)
  - `Initial Notes` (Textarea, Optional)
- **Buttons**: `Cancel`, `Start Investigation`.
- **Validation**: `Transaction ID` must match regex pattern `^TXN-[0-9]{5,10}$`.
**AI / Developer Prompt**:
> Create a Start Investigation Wizard Modal. Title: "New Investigation". Include inputs for Transaction ID, Priority dropdown, and a textarea for Initial Notes. Validate that the Transaction ID matches the regex ^TXN-[0-9]{5,10}$. Show Cancel and Start Investigation buttons.

---
**End of Detailed Component Library**
