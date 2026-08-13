# FFIRE Table Specifications
## Financial Fraud Investigation Reasoning Engine

### Table Design System Overview

Tables in FFIRE are designed to present complex investigative data clearly, efficiently, and accessibly. They support sorting, filtering, selection, and various data types while maintaining readability and usability for fraud investigators who often need to analyze large volumes of information quickly.

#### Core Principles:
1. **Scannability**: Quick visual parsing of key information
2. **Actionability**: Clear indication of what can be done with each row
3. **Flexibility**: Adaptable to different data types and use cases
4. **Performance**: Virtualization for large datasets
5. **Accessibility**: Full keyboard and screen reader support

#### Table Variants:
1. **Data Tables** - Interactive tables with sorting, selection, actions
2. **Simple Tables** - Read-only display tables (reference data, configurations)
3. **Compact Tables** - Dense layouts for dashboards and sidebars
4. **Borderless Tables** - Minimal visual design for specific contexts
5. **Expandable Tables** - Row expansion for detailed views

#### Features:
- Sorting (single & multi-column)
- Filtering (column-level & global)
- Selection (single, multiple, range)
- Pagination (client & server-side)
- Virtual scrolling (for large datasets)
- Column resizing & reordering
- Column visibility toggling
- Export capabilities (CSV, Excel, PDF)
- Bulk actions
- Inline editing (limited use cases)
- Expandable rows
- Row actions menu
- Loading states
- Empty states
- Error states

### Complete Table Catalog

#### 1. Investigations Tables

**Investigations List Table** (/investigations)
- Location: Main investigations view
- Purpose: Browse, filter, and manage investigations
- Data Source: Investigation service with filtering/pagination
- Row Height: Medium (comfortable for touch/mouse)
- Selection: Checkbox-based multiple selection
- Sorting: Multi-column sortable
- Virtualization: Enabled (>100 rows)
- Columns:
  - Investigation ID (link to details, sortable, default sort desc)
  - Customer Name (truncated with tooltip, sortable)
  - Transaction Amount (formatted currency, sortable)
  - Currency Code (ISO 4217, sortable)
  - Risk Level (color-coded badge, sortable by score)
  - Status (color-coded badge with tooltip, sortable)
  - Assigned To (avatar/initials, sortable by name)
  - Created Date (relative time, sortable by timestamp)
  - Last Updated (relative time, sortable by timestamp)
  - Actions (menu kebab icon, not sortable)
- Features:
  - Global search/filter bar above table
  - Column picker (show/hide columns)
  - Bulk actions toolbar (appears when selection > 0)
  - Row actions menu (per-row kebab)
  - Select all checkbox in header
  - Date range filtering in column headers
  - Amount range filtering via slider in column header
  - Export selected/selected all functionality
- Actions Menu (per row):
  - View Details
  - Add Note
  - Escalate
  - Assign to Me
  - Duplicate Investigation
  - Mark as False Positive
- Bulk Actions Toolbar:
  - Assign to analyst
  - Change status
  - Add tag/label
  - Export selected
  - Delete (with confirmation)
- Empty State:
  - Illustration + message: "No investigations match your filters"
  - Suggestions: "Try adjusting your filters" or "Start a new investigation"
  - Primary CTA: "New Investigation" button
- Loading State:
  - Skeleton rows (3-5 placeholder rows)
  - Column shimmer effect
- Error State:
  - Retry button + error message
  - Option to view cached data if available
  - Technical details toggle (for administrators)

**Investigations Archive Table** (/investigations?archived=true)
- Similar structure to Investigations List
- Additional Column: Archival Date
- Different Actions: Restore instead of Assign to Me
- Bulk Actions: Restore selected, Delete permanently selected

#### 2. Evidence Tables

**Evidence Library Table** (/evidence/library)
- Location: Evidence management center
- Purpose: Browse, search, and manage all evidence items
- Selection: Checkbox-based multiple selection
- Columns:
  - Thumbnail Preview (image/icon based on file type, not sortable)
  - Evidence ID (link to details, sortable)
  - Source System (badge with system name, sortable)
  - Evidence Type (document, image, transaction, etc., sortable)
  - Relevance Score (0-1.0 visual bar + numeric, sortable)
  - Date Collected (relative time, sortable)
  - Tags (multi-label display, sortable by first tag)
  - Related Investigations (count with tooltip, sortable)
  - Actions (menu kebab icon, not sortable)
- Features:
  - Advanced filtering sidebar (collapsible)
  - Grid/List toggle view
  - Drag & drop upload area above table
  - Bulk tagging toolbar
  - Column-specific filters (dropdowns in header)
  - Size indicators for file evidence
  - Preview tooltips on hover (for thumbnails)
- Row Actions Menu:
  - View Full Details
  - Expand/Collapse (if using expandable rows)
  - Tag as Relevant/Irrelevant
  - Add Note/Comment
  - Download Original
  - Apply Tags
  - Move to Category/Archive
  - Generate Report from Evidence Set
  - Delete Selected (with confirmation)
- Bulk Operations Toolbar:
  - Apply tags to selected
  - Move to archive/category
  - Generate report from evidence set
  - Delete selected (with confirmation)
- Special Features:
  - File type icons (PDF, DOC, XLS, JPG, PNG, etc.)
  - Virus scan status indicators
  - Duplication detection warnings
  - Copyright/licensing status indicators
  - Version history indicator (for documents)
  - Usage count (investigations using this evidence)

**Evidence Timeline Table** (within Investigation Detail)
- Location: Investigation detail right column/expanded view
- Purpose: Chronological view of investigation events
- Selection: None (read-only timeline)
- Columns:
  - Timestamp (relative/time-specific)
  - Event Type (icon + text: evidence collected, analysis completed, etc.)
  - Description (brief summary)
  - Actor (system/user who performed action)
  - Related Entity (evidence piece, transaction, etc. with link)
- Features:
  - Color-coded rows by event type
  - Expandable/collapsible sections by date
  - Ability to add manual notes/events
  - Drag & drop reordering (for manual events only)
  - Filter by event type
  - Export timeline (PDF/CSV)
- No bulk actions (timeline is primarily visual/scrollable)
- Loading state: Skeleton timeline entries
- Empty state: Guidance on how evidence gets added to timeline

#### 3. Reports Tables

**Reports Gallery Table** (/reports/investigations)
- Location: Reports section
- Purpose: Browse and manage generated reports
- Selection: Checkbox-based multiple selection
- Columns:
  - Report Title/Type (link to view/download)
  - Investigation ID/Date Range (display range or "N/A" for templates)
  - Format (PDF, JSON, CSV, etc. with icon)
  - Generation Date (relative time, sortable)
  - Generated By (user name, sortable)
  - Status (generating, ready, failed, expired)
  - Actions (menu kebab icon)
- Features:
  - Filter by report type, date range, status, investigator
  - Sort by generation date, title, format
  - Bulk operations: Delete selected, Regenerate selected
  - Size indicator for downloadable reports
  - Expiration indicators for time-limited reports
  - Share via email/secure link option in actions
- Actions Menu:
  - View Report
  - Share Report
  - Regenerate Report
  - Download
  - Delete (with confirmation)
- Empty State:
  - Message: "No reports generated yet"
  - CTA: "New Report" button + links to report templates
- Loading State: Skeleton report cards

**Report Builder Table** (within Custom Reports tab)
- Location: Report customization interface
- Purpose: Define columns and filters for custom reports
- Selection: Single selection (editing one field/filter at a time)
- Columns:
  - Field Name (from available schema)
  - Data Type (text, number, date, etc.)
  - Aggregation (none, sum, avg, count, min, max)
  - Sort Order (asc/desc/none)
  - Width/Priority (column position importance)
  - Actions (menu: move up/down, delete, edit)
- Features:
  - Drag & drop reordering
  - Inline editing for most properties
  - Preview of how column will appear in report
  - Validation of incompatible combinations (e.g. text + sum)
  - Search/filter available fields
  - Save as template functionality
- Special Columns for Filters Tab:
  - Filter Field
  - Operator (equals, contains, between, etc.)
  - Value Input (custom control based on data type)
  - Logic (AND/OR between filters)
  - Actions (delete, edit)

#### 4. Analytics Tables

**Performance Metrics Table** (/analytics/performance)
- Location: Analytics performance tab
- Purpose: Display performance breakdowns and benchmarks
- Selection: None (read-only reference)
- Columns:
  - Metric Category (investigation stage, fraud type, etc.)
  - Metric Name (specific measurement)
  - Current Value (formatted appropriately)
  - Target/Benchmark (if applicable)
  - Trend (arrow icon: ↑→↓ with percentage change)
  - Status (color indicator: meets target/needs improvement)
  - Details (link to drill-down view)
- Features:
  - Expandable categories
  - Sort by metric name, value, trend
  - Conditional formatting based on target achievement
  - Tooltips with calculation methodology and data sources
  - Export to CSV/Excel for further analysis
  - Time period selector affecting all values
- Specialized Tables:
  - Investigator Workload: Name, assigned investigations, avg time, completion rate
  - Fraud Type Analysis: Type, count, avg amount, success rate, trend
  - Resource Utilization: Component, CPU%, memory%, storage%, network%

#### 5. Administration Tables

**Users Management Table** (/admin/users)
- Location: User administration section
- Purpose: Create, edit, deactivate user accounts
- Selection: Checkbox-based multiple selection
- Columns:
  - Avatar/Initials (visual identification)
  - Full Name (sortable)
  - Email Address (sortable)
  - Role(s) (multi-badge display, sortable by primary role)
  - Department/Team (sortable)
  - Status (Active/Inactive/Suspended with color indicator)
  - Last Login (relative time, sortable)
  - MFA Status (icon + text: Enabled/Disabled/Not Required)
  - Actions (menu kebab)
- Features:
  - Inline editing for status, department
  - Bulk actions: Activate selected, Deactivate selected, Reset password
  - Role assignment dropdown in Actions menu
  - Export users (CSV/Excel)
  - Search/filter by name, email, role, status
  - Column visibility controls
- Actions Menu:
  - Edit User
  - Deactivate/Activate
  - Reset Password
  - Assign Roles
  - View Audit Log
  - Export User Data (GDPR)
  - Delete User (with confirmation, requires re-type username)
- Empty State:
  - Message: "No users found"
  - CTA: "Invite Users" or "Create New User" button
- Loading State: Skeleton user rows

**Roles & Permissions Table** (/admin/roles)
- Location: Role-based access control management
- Purpose: Define and manage roles and their permissions
- Selection: Single selection (editing one role at a time)
- Columns:
  - Role Name (link to edit, sortable)
  - Description (brief purpose)
  - Permission Count (total permissions assigned)
  - User Count (number of users with this role)
  - Level (inheritance level if hierarchical)
  - Actions (menu: duplicate, delete)
- Features:
  - Inline editing for description
  - Permission matrix viewer (separate full-screen view)
  - Role hierarchy visualization (if applicable)
  - Bulk operations limited (roles typically managed individually)
  - Export role definitions (JSON/YAML)
- Special Features:
  - Permission inheritance indicators
  - Conflict highlighting (when permissions contradict)
  - Template roles based on common job functions
  - Default role assignments for self-registration
- Actions Menu:
  - Edit Role
  - View Permissions (opens matrix)
  - Duplicate Role
  - Delete Role (with confirmation if users assigned)
  - Export Role Definition

**Audit Logs Table** (/admin/audit-logs)
- Location: Security and compliance section
- Purpose: Review system activity for auditing and troubleshooting
- Selection: Checkbox-based multiple selection (for export)
- Columns:
  - Timestamp (relative/time-specific, sortable desc)
  - User (avatar/initials + name, sortable)
  - Action (CRUD operation + resource type, sortable)
  - Resource (name/type with link if applicable)
  - IP Address (geolocation icon on hover, sortable)
  - User Agent (browser/device info, tooltip on hover)
  - Outcome (Success/Failure with color indicator)
  - Actions (menu: view details, export)
- Features:
  - Advanced filtering: date range, user, action, outcome, resource type
  - Column freezing for timestamp and user columns
  - Export capabilities (CSV, JSON, SEC format)
  - Search within log messages
  - Saved searches for common audit queries
  - Alert creation from search results
  - Immutable log indicator (tamper-evident)
- Virtualization: Essential (often 10K+ rows)
- Loading State: Skeleton log rows with shimmer
- Error State: Connection issues vs. empty results distinguished
- Retention Policy Indicator: Shows how long logs are retained
- Actions Menu:
  - View Full Details
  - Export Entry
  - Copy Resource ID
  - Copy User ID
  - Flag for Investigation (if suspicious activity)

#### 6. Configuration & Settings Tables

**System Settings Table** (/admin/settings)
- Location: System configuration area
- Purpose: Manage key-value configuration settings
- Selection: Single selection (editing one setting at a time)
- Columns:
  - Setting Key (machine-readable identifier, sortable)
  - Setting Name (human-readable description)
  - Data Type (string, number, boolean, enum, JSON)
  - Current Value (formatted appropriately for type)
  - Default Value (for comparison)
  - Description (detailed explanation with examples)
  - Actions (menu: edit, reset to default)
- Features:
  - Inline editing for simple types (text, number, boolean)
  - Special editors for complex types (color picker, date/time, JSON)
  - Validation based on data type and constraints
  - Reset to default value option
  - Visibility of whether setting requires restart
  - Grouping/category filtering
  - Search/filter by key, name, description
- Special Types:
  - Enum: Dropdown selector
  - JSON: Syntax-highlighted editor with validation
  - File Path: Browser + validation
  - Email/SMTP: Individual field validators
  - API Key: Masked input with test button
- Actions Menu:
  - Edit Setting
  - Reset to Default
  - View Change History (if audited)
  - View Dependencies (other settings affected)
  - Documentation Link

**Integrations Table** (/admin/integrations)
- Location: Third-party service connections
- Purpose: Manage external service integrations
- Selection: Checkbox-based multiple selection
- Columns:
  - Integration Name (link to details, sortable)
  - Service Type (data provider, CRM, etc., sortable)
  - Status (Connected/Disconnected/Error with color icon)
  - Last Sync (relative time, sortable)
  - Sync Frequency (disabled/manual/interval display)
  - Actions (menu kebab)
- Features:
  - Inline editing for frequency, basic settings
  - Test Connection button in Actions menu
  - Bulk operations: Enable selected, Disable selected
  - Health indicators (latency, success rate, error count)
  - Credential status (configured/needs update/expired)
  - Environment separation (dev/stage/prod labels)
- Actions Menu:
  - Edit Configuration
  - Test Connection
  - Enable/Disable
  - View Sync Logs
  - View Credentials (masked)
  - Force Sync Now
  - Delete Integration (with confirmation)
- Empty State:
  - Message: "No integrations configured"
  - CTA: "Add Integration" button + marketplace/explorer link

#### 7. Specialized Tables

**Fraud Patterns Table** (within Knowledge Base or Rules Engine)
- Location: Fraud detection configuration
- Purpose: Manage known fraud patterns and rules
- Selection: Checkbox-based multiple selection
- Columns:
  - Pattern ID/Rule ID (sortable)
  - Description (human readable explanation)
  - Fraud Type(s) Associated (multi-label display)
  - Severity/Impact (score or level with color indicator)
  - Enabled Status (toggle switch)
  - Hit Count (24h/7d/30d, sortable)
  - False Positive Rate (percentage with trend)
  - Last Updated (relative time, sortable)
  - Actions (menu kebab)
- Features:
  - Inline toggling for enabled status
  - Bulk enable/disable selected
  - Export rulesets (JSON/YAML)
  - Test rule against sample data
  - Performance impact indicator
  - Rule complexity score
  - Tags/Labels for categorization
  - Version history indicator
- Actions Menu:
  - Edit Rule/Pattern
  - Test Rule
  - Enable/Disable
  - View Performance Metrics
  - View Version History
  - Duplicate Rule
  - Export Rule Set
  - Delete Rule (with confirmation)

**Watchlists Table** (within External Data Sources)
- Location: External risk data management
- Purpose: Manage external watchlists and blacklists
- Selection: Checkbox-based multiple selection
- Columns:
  - List Name (link to details, sortable)
  - List Type (sanctions, PEP, adverse media, etc.)
  - Source Provider (vendor/internal)
  - Entry Count (formatted number, sortable)
  - Last Updated (relative time, sortable)
  - Update Frequency (disabled/daily/weekly/etc.)
  - Status (Active/Stale/Error with color indicator)
  - Coverage (geographic/jurisdictional info)
  - Actions (menu kebab)
- Features:
  - Inline editing for frequency, source credentials
  - Bulk operations: Activate selected, Deactivate selected
  - Download latest version button
  - View sample entries
  - Update now button
  - Sync status indicators
  - Overlap/warning alerts with other lists
- Actions Menu:
  - Edit Source Configuration
  - View Sample Entries
  - Download Current Version
  - Update Now
  - Enable/Disable
  - View Update History
  - Delete List (with confirmation)
  - Export List (sample or full based on license)

#### Table Implementation Guidelines

**Column Types & Rendering:**
1. **Text** - Left-aligned, wrapping, tooltip on overflow
2. **Numbers** - Right-aligned, thousands separators, appropriate precision
3. **Currency** - Right-aligned, symbol prefix, 2 decimal places
4. **Dates/Times** - Left/center-aligned, relative time with tooltip absolute
5. **Badges/Tags** - Center-aligned, color-coded by meaning/type
6. **Avatars** - Center-aligned, fixed size with tooltip on hover
7. **Actions** - Center-aligned, consistent icon sizing
8. **Checkboxes** - Center-aligned in header for select-all, left in rows
9. **Toggles/Switches** - Center-aligned, consistent size
10. **Links** - Blue underline on hover, cursor pointer
11. **Icons** - Center-aligned, consistent size, tooltip for meaning
12. **Progress Bars** - Left-aligned, fixed height, percentage label
13. **Avatars with Status** - Combined avatar + status indicator overlay
14. **Thumbnails** - Fixed aspect ratio, hover enlargement, click to view full

**Interaction Patterns:**
1. **Sorting** - Click header to sort, shift-click for multi-column, clear indicator
2. **Column Resizing** - Drag header boundary, persistence in local storage/user prefs
3. **Column Reordering** - Drag header to new position, persistence
4. **Column Visibility** - Menu in header or toolbar, persistence
5. **Selection** - Click row (configurable), shift-click for range, cmd/ctrl-click for toggle
6. **Bulk Selection** - Header checkbox, indeterminate state for partial selection
7. **Expanding Rows** - Click expand icon or anywhere in row (if configured)
8. **Inline Editing** - Double-click or pencil icon, enter to save, esc to cancel
9. **Context Menus** - Right-click or kebab icon, consistent grouping
10. **Keyboard Navigation** - Arrow keys, space/enter to activate, escape to cancel
12. **Scrolling** - Virtual scroll for >100 rows, sticky header during scroll
13. **Export** - Toolbar button with format options, progress indicator for large exports
14. **Refresh** - Toolbar button or auto-refresh toggle
15. **Column Filters** - Text/number/date filters in header row, apply on enter or debounce

**States & Feedback:**
1. **Loading** - Skeleton rows with shimmer animation
2. **Empty** - Illustrative graphic + helpful message + primary CTA
3. **Error** - Retry button + message + optional details toggle
4. **Saving** - Inline spinner in cell or row-level indicator
5. **Validation Error** - Red border/icon + tooltip message, prevent bulk actions if any invalid
6. **Hover State** - Subtle background change, show row actions if hidden by default
7. **Selected State** - Background highlight + checkbox checked
8. **Expanded State** - Background shift + expand/collapse icon rotation
9. **Click Feedback** - Visual press state + potential sound (if enabled)
10. **Accessibility Focus** - Visible outline, announced by screen readers

**Performance Optimizations:**
1. **Virtualization** - Windowing for >100 rows (only render visible + buffer)
2. **Debouncing** - Input delays for search/filter/column resize
3. **Memoization** - Cache row rendering functions
4. **Lazy Loading** - Expandable content, thumbnails, tooltips
5. **CSS Containment** - Isolate table styling for performance
6. **Request Batching** - Combine multiple filter/sort operations
7. **Pagination Awareness** - Distinguish client vs server-side pagination needs
8. **Memory Management** - Clean up event listeners on row unmount
9. **Animation Performance** - Use transform/opacity, respect prefers-reduced-motion
10. **Scroll Position Persistence** - Maintain scroll position on data refresh when possible

**Accessibility Requirements:**
1. **Semantic Structure** - Proper `<table>`, `<thead>`, `<tbody>`, `<tfoot>`, `<th>` with scope
2. **Keyboard Navigation** - Full navigation via arrow keys, home/end, page up/down
3. **Screen Reader Labels** - Announce row/column headers, selection state, expanded state
4. **Focus Management** - Trap focus in edit modes, return to triggering element
5. **Color Contrast** - WCAG AA minimum for all text and icons
6. **Resize Observers** - Handle column width changes gracefully
7. **Alternative Text** - Meaningful alt text for all icons and images
8. **Aria Labels** - Descriptive labels for custom controls (date pickers, etc.)
9. **Row Identification** - Unique identifiers for screen reader row announcement
10. **Nested Tables** - Avoid when possible, provide clear headers when necessary

**Responsive Design Breakpoints:**
1. **Desktop (≥1024px)** - Full column set, horizontal scrolling if needed
2. **Tablet (768-1023px)** - Hidden less critical columns, horizontal scrolling
3. **Mobile (<768px)** - Card view toggle OR horizontal scroll with prioritized columns
4. **Ultra Narrow (<320px)** - Single column mode with expandable rows for details

**Internationalization Considerations:**
1. **Text Expansion** - Accommodate up to 30% longer text in some languages
2. **Number/Formatting** - Localize decimal/thousand separators, currency placement
3. **Date Formats** - Respect locale-specific date/time presentations
4. **RTL Support** - Mirror column order, alignment, and icons for Arabic/Hebrew
5. **Sorting Logic** - Use locale-aware sorting for text columns
6. **Placeholder Text** - Translate all hints, empty states, tooltips

**Testing Checklist:**
1. **Functional** - All CRUD operations, sorting, filtering, selection, actions
2. **Performance** - Virtualization with 10K+ rows, column operations responsiveness
3. **Accessibility** - Screen reader, keyboard-only, color blindness, zoom testing
4. **Responsiveness** - All breakpoints, orientation changes, touch targets
5. **Error Handling** - Network failures, malformed data, invalid states
6. **Data Integrity** - Correct values, formatting, sorting, filtering accuracy
7. **State Persistence** - Column preferences, sort order, pagination, scroll position
8. **Bulk Operations** - Selection limits, confirmation dialogs, undo possibilities
9. **Keyboard Shortcuts** - Standard navigation, selection, action triggers
10. **Localization** - Multiple languages, RTL, various locales for formatting

This comprehensive table specification ensures that every data presentation in the FFIRE system is optimized for investigative work, providing clear, actionable, and accessible views of complex fraud detection data while maintaining performance and usability standards.