# FFIRE Screen Specifications
## Financial Fraud Investigation Reasoning Engine

### 1. Dashboard Screen (/)
**Purpose**: Executive overview of investigation operations, key metrics, and system health

#### Layout:
- **Header**: 
  - Title: "Dashboard"
  - Right: User avatar/profile dropdown
- **Main Content**: 
  - Responsive grid of metric cards
  - Recent activity feed
  - System alerts panel

#### Components:
1. **Metric Cards** (4-column grid on desktop, stacking on mobile):
   - Active Investigations: Count + trend indicator
   - High Priority Cases: Count requiring immediate attention
   - Avg Investigation Time: Trend over time period
   - Auto-Resolution Rate: Percentage of cases resolved without human intervention

2. **Recent Investigations Table**:
   - Columns: Investigation ID, Customer, Amount, Risk Level, Status, Last Updated, Actions
   - Actions: View Details, Add Note, Escalate

3. **System Alerts Panel**:
   - Real-time notifications
   - Severity-based coloring (info/warning/critical)
   - Dismissible with acknowledgment tracking

4. **Investigation Trends Chart**:
   - Daily/weekly/monthly toggles
   - Volume vs. completion rate
   - Risk distribution over time

#### Data Requirements:
- Real-time metrics from investigation service
- Recent investigations (last 24-48 hours)
- System health indicators
- Trend data for last 30 days

#### User Interactions:
- Click metric cards to drill down to filtered views
- Click investigation row to open Investigation Details
- Click alert to view details or acknowledge
- Date range selector for trends chart

#### Edge Cases:
- No recent investigations: Show inviting "Start First Investigation" CTA
- System offline: Display degraded mode indicators
- Large data sets: Implement virtual scrolling for tables

---

### 2. Investigations List Screen (/investigations)
**Purpose**: Browse, filter, and manage all investigations

#### Layout:
- **Header**:
  - Title: "Investigations"
  - Right: "New Investigation" button (primary CTA)
- **Filters Panel** (collapsible sidebar):
  - Status filter (multi-select)
  - Risk level filter (multi-select)
  - Date range picker
  - Amount range slider
  - Assigned analyst dropdown
  - Transaction ID/Customer search
- **Results Area**:
  - Investigations table with pagination
  - Bulk action toolbar
  - Export options

#### Components:
1. **Advanced Filters Panel**:
   - Collapsible/expandable with smooth animation
   - Clear all filters button
   - Apply filters button (with debounce)
   - Save current filter as named view

2. **Investigations Table**:
   - Columns (customizable via column picker):
     - Investigation ID (link to details)
     - Customer Name (truncated with tooltip)
     - Transaction Amount (formatted currency)
     - Currency Code
     - Risk Level (color-coded badge)
     - Status (color-coded badge with tooltip)
     - Assigned To (avatar/initials)
     - Created Date (relative time)
     - Last Updated (relative time)
     - Actions menu (kebab icon)
   - Features:
     - Sortable columns (click header)
     - Selectable rows (checkboxes for bulk actions)
     - Pagination controls (page size selector)
     - Responsive design (horizontal scroll on mobile)

3. **Bulk Actions Toolbar** (appears when items selected):
   - Assign to analyst
   - Change status
   - Add tag/label
   - Export selected
   - Delete (with confirmation)

4. **Investigation Row Actions** (per-row menu):
   - View Details
   - Add Note
   - Escalate
   - Assign to Me
   - Duplicate Investigation
   - Mark as False Positive

#### Data Requirements:
- Paginated list of investigations (50-100 per page)
- Filter options populated from reference data
- User assignments and team structure
- Bulk operation capabilities

#### User Interactions:
- Filter updates trigger API call with debounce
- Column resizing and reordering persistence
- Row selection via checkbox or click (configurable)
- Right-click context menu for row actions
- Keyboard navigation support
- Export to CSV/Excel/PDF

#### Edge Cases:
- No results: Show helpful empty state with search suggestions
- Loading states: Skeleton loaders for table and filters
- Error states: Retry mechanism for failed loads
- Very large datasets: Virtualized scrolling implementation

---

### 3. Investigation Detail Screen (/investigations/:id)
**Purpose**: Deep dive into a specific investigation with all evidence, analysis, and actions

#### Layout:
- **Header**:
  - Title: "Investigation: [ID]"
  - Right: Action buttons (Resume, Pause, Add Note, Export, Back)
- **Main Content** (3-column layout on desktop, stacked on mobile):
  - **Left Column (8/12 cols)**: Investigation overview and reasoning graph
  - **Right Column (4/12 cols)**: Evidence explorer and execution monitor

#### Components:

##### Left Column:
1. **Transaction Summary Card**:
   - Customer information (name, account, KYC status)
   - Merchant details (name, category, risk score)
   - Transaction specifics (amount, currency, timestamp, status)
   - Risk indicators (badges, score meter)

2. **Reasoning Graph Visualization**:
   - Interactive node-link diagram showing AI reasoning steps
   - Node types: Evidence, Rule Check, Knowledge Lookup, Decision Point
   - Edge labels: Confidence, reasoning type
   - Interactive features: Node expansion, detail tooltips, path highlighting
   - Loading states and error handling

3. **Timeline View**:
   - Chronological view of investigation events
   - Color-coded by event type (evidence collected, analysis completed, etc.)
   - Expandable/collapsible sections
   - Ability to add manual notes/events

##### Right Column:
4. **Execution Monitor**:
   - Real-time progress of AI investigation pipeline
   - Current step highlighting
   - Step status: pending, running, completed, failed
   - Retry count indicators
   - Estimated time to completion

5. **Evidence Explorer**:
   - Evidence cards grouped by source type
   - Each evidence item shows:
     - Source system/badge
     - Relevance score (0-1.0) with visual indicator
     - Key facts/snippets
     - Actions: Expand, Tag as Relevant/Irrelevant, Add Note
   - Filter evidence by: source, relevance, type, date
   - Manual evidence entry capability

#### Data Requirements:
- Complete investigation record with all related entities
- Full evidence chain with metadata
- Step-by-step execution trace from LangGraph
- Related historical cases (if any)
- User permissions and action availability

#### User Interactions:
- Click evidence to view full details
- Drag/reorder evidence in timeline
- Add annotations to evidence/nodes
- Pause/resume investigation execution
- Manual override of AI decisions
- Export investigation package (PDF/JSON)
- Initiate human review/escalation

#### Edge Cases:
- Investigation not found: 404 page with suggested similar IDs
- Investigation in progress: Show live updating indicators
- Investigation failed: Show error details and retry options
- No evidence available: Guide user on evidence collection options
- Very large evidence sets: Virtualized lists with search/filter

---

### 4. Evidence Library Screen (/evidence/library)
**Purpose**: Central repository for managing and searching evidence

#### Layout:
- **Header**:
  - Title: "Evidence Library"
  - Right: "Add Evidence" button + Search bar
- **Filters/Sidebar**:
  - Evidence type filters (documents, images, transactions, etc.)
  - Source system filters
  - Date range
  - Relevance/min confidence sliders
  - Tags/categories multi-select
- **Main View**:
  - Grid/list toggle view
  - Evidence cards with preview
  - Selection checkboxes for bulk operations
  - Pagination/infinite scroll

#### Components:
1. **Evidence Card Views**:
   - **Grid View**: Visual preview with metadata overlay
   - **List View**: Detailed table with expandable rows
   - **Preview Modal**: Full-screen view with annotation tools

2. **Evidence Details Panel** (sidebar or modal):
   - Full metadata display
   - Provenance/tracking information
   - Related investigations (linked)
   - Annotation thread
   - Download/export options
   - Version history (if applicable)

3. **Bulk Operations Toolbar**:
   - Apply tags to selected
   - Move to archive/category
   - Generate report from evidence set
   - Delete selected (with confirmation)

#### Data Requirements:
- Evidence items with rich metadata
- Preview/thumbnails for media types
- Search index for full-text search
- Tagging and categorization system
- Usage statistics (which investigations used this evidence)

#### User Interactions:
- Drag-and-drop upload for new evidence
- Bulk tagging and categorization
- Evidence linking to investigations
- Annotation and commenting system
- Version control for documents
- Access control and permissions viewing

#### Edge Cases:
- Large file uploads: Progress indication, chunking
- Unsupported file types: Clear error messages with suggestions
- Duplicate detection: Warn user of potential duplicates
- Copyright/Licensing: Display restrictions and usage rights

---

### 5. Reports Screen (/reports)
**Purpose**: Generate, view, and manage investigation reports and analytics

#### Layout:
- **Header**:
  - Title: "Reports"
  - Right: "New Report" button + Date range selector
- **Navigation Tabs**:
  - Investigation Reports
  - Compliance Reports
  - Trend Analytics
  - Custom Reports
- **Main Content**: Tab-specific views

#### Components per Tab:

##### Investigation Reports Tab:
- Report gallery with cards showing:
  - Report type/title
  - Investigation ID/date range
  - Format (PDF, JSON, CSV)
  - Generation date
  - Actions: View, Share, Regenerate, Delete
- Filters: Date range, report type, status, investigator

##### Compliance Reports Tab:
- Regulatory report templates (SAR, CTR, etc.)
- Schedule management for recurring reports
- Audit trail exports
- Policy compliance metrics

##### Trend Analytics Tab:
- Interactive charts and graphs
- Drill-down capabilities
- Comparative analysis tools
- Forecasting/prediction widgets

##### Custom Reports Tab:
- Report builder interface
- Drag-and-drop field selection
- Filter builder with conditional logic
- Format options (PDF, Excel, CSV, JSON)
- Save as template functionality

#### Data Requirements:
- Report templates and configurations
- Generated report metadata and storage links
- Aggregated data for analytics
- User preferences and saved configurations

#### User Interactions:
- Configure report parameters via form/wizard
- Schedule automated report generation
- Share reports via email or secure link
- Set retention policies for reports
- Compare reports across time periods

#### Edge Cases:
- Report generation failures: Queue retry mechanism
- Large report generation: Background processing with notifications
- Permission errors: Clear messaging on access restrictions
- Template versioning: Handle template updates gracefully

---

### 6. Analytics Screen (/analytics)
**Purpose**: Deep dive into investigation performance, trends, and operational metrics

#### Layout:
- **Header**:
  - Title: "Analytics"
  - Right: Date range selector + Export dashboard button
- **Layout**: Responsive grid of analytics widgets
- **Filters**: Global date range, investigation type, investigator/team

#### Widget Types:
1. **Key Metrics Cards** (top row):
   - Total Investigations (period vs previous)
   - Average Resolution Time
   - Escalation Rate
   - False Positive Rate
   - Manual Review Rate
   - Automation Efficiency (%)

2. **Trend Charts**:
   - Daily/weekly investigation volume
   - Risk score distribution over time
   - Geographic heatmap of incidents
   - Fraud type prevalence trends

3. **Performance Breakdowns**:
   - Investigator workload distribution
   - Average time by investigation stage
   - Success rate by fraud type
   - Resource utilization charts

4. **Predictive Analytics**:
   - Risk prediction accuracy over time
   - Model drift detection metrics
   - Feature importance rankings
   - False positive/negative analysis

#### Components:
- Interactive charts with drill-down capabilities
- Filter synchronization across widgets
- Export options (individual widget or full dashboard)
- Scheduled email delivery of snapshots
- Annotation/commenting on charts
- Custom dashboard layout saving

#### Data Requirements:
- Aggregated investigation metrics
- Time-series data for trend analysis
- Performance benchmarks and SLAs
- Predictive model performance data
- Resource utilization metrics

#### User Interactions:
- Click chart elements to drill down to underlying data
- Filter updates propagate to all connected widgets
- Date range changes trigger data refresh
- Save custom dashboard layouts
- Share insights via export or link
- Set up alerts for metric thresholds

#### Edge Cases:
- No data for selected period: Show guidance on adjusting filters
- Query timeouts: Progressive loading with partial results
- Data inconsistencies: Data quality warnings and reconciliation options
- Real-time streaming: Handle connection interruptions gracefully

---

### 7. Administration Screen (/admin)
**Purpose**: System configuration, user management, and settings

#### Layout:
- **Header**:
  - Title: "Administration"
  - Right: Notification center + User profile dropdown
- **Navigation Sidebar**:
  - Users & Roles
  - System Settings
  - Security & Compliance
  - Integrations
  - Audit Logs
  - System Health

#### Sub-Sections:

##### Users & Roles:
- User management table (create, edit, deactivate)
- Role-based access control (RBAC) editor
- Permission matrix viewer
- Team and department structure
- Invite/bulk import functionality

##### System Settings:
- General configuration (company info, time zones, etc.)
- Email/SMTP configuration
- Storage and retention policies
- API rate limits and throttling
- Feature flags and toggles

##### Security & Compliance:
- Authentication providers (SSO, LDAP, SAML)
- Password policy configuration
- Session management settings
- Audit log retention and access
- Encryption key management
- Compliance reporting configuration

##### Integrations:
- Third-party service connections (data providers, CRMs)
- Webhook management
- API key administration
- Custom connector marketplace
- Integration health monitoring

##### Audit Logs:
- Immutable log viewer with filtering
- Export capabilities for compliance
- Search by user, action, date range, resource
- Suspicious activity flagging
- Integration with SIEM systems

##### System Health:
- Real-time performance metrics
- Service dependency status
- Resource utilization (CPU, memory, disk, network)
- Error rates and latency distributions
- Alert configuration and notification channels

#### Components:
- Form wizards for complex configurations
- Validation with real-time feedback
- Preview modes for setting changes
- Rollback capabilities for risky changes
- Bulk operations with confirmation dialogs
- Import/export functionality for configurations

#### Data Requirements:
- User and role information with hashed credentials
- System configuration key-value store
- Audit trail entries with full context
- Integration credentials and connection strings
- Health check metrics from all services

#### User Interactions:
- Role assignment via drag-and-drop to groups
- Bulk user operations (activate/deactivate, password reset)
- Configuration change preview and diff view
- Testing connections for integrations before saving
- Emergency access procedures (break-glass accounts)
- Disaster recovery initiation procedures

#### Edge Cases:
- Configuration conflicts: Clear validation and resolution guidance
- Lockout prevention: Multiple admin requirement for critical changes
- Audit log tampering: Cryptographic verification and alerts
- Integration failures: Circuit breaker patterns and fallback options
- System overload: Graceful degradation and load shedding

---

### 8. User Profile Screen (/profile)
**Purpose**: Personal settings, preferences, and activity history

#### Layout:
- **Header**:
  - Title: "My Profile"
  - Back button to previous location
- **Sections**:
  - Profile Information
  - Preferences & Settings
  - Notification Preferences
  - Activity History
  - Connected Applications
  - Security Settings

#### Components:
1. **Profile Information**:
   - editable fields (name, email, phone, bio)
   - avatar upload/gravatar integration
   - supervisory hierarchy display
   - skills and certifications

2. **Preferences**:
   - UI theme selection (light/dark/auto)
   - date/time format preferences
   - default dashboard widgets
   - email notification frequency
   - language and localization

3. **Notification Center**:
   - Channel preferences (email, in-app, SMS)
   - Event type subscriptions
   - Quiet hours scheduling
   - Duplicate suppression settings

4. **Activity Feed**:
   - Personal investigation activity
   - Recent logins and sessions
   - Permission changes
   - Export/download history

5. **Security**:
   - Password change flow
   - Multi-factor authentication setup
   - Session management (active locations/devices)
   - API key management
   - Account recovery options

#### Data Requirements:
- User profile attributes
- Preference settings per category
- Notification delivery history and preferences
- Activity/audit trail for user-specific actions
- Connected applications and permissions

#### User Interactions:
- Real-time validation on form inputs
- Preview of theme changes before saving
- Test notification delivery
- Export personal data (GDPR/compliance)
- Session termination from specific devices
- Recovery code generation and validation

#### Edge Cases:
- Profile picture upload failures: size/type validation with helpful messages
- Preference conflicts: Clear precedence rules and notifications
- Activity history limits: Archiving and pagination strategies
- Security lockouts: Administrator-assisted recovery procedures
- Concurrent session management: Conflict resolution strategies

---

### 9. Help & Documentation Screen (/help)
**Purpose**: Contextual help, documentation, and support resources

#### Layout:
- **Header**:
  - Title: "Help & Support"
  - Left: Breadcrumb navigation
- **Sidebar Navigation**:
  - Getting Started
  - User Guides
  - API Documentation
  - FAQs
  - Video Tutorials
  - Contact Support
  - Release Notes
- **Main Content**:
  - Searchable documentation viewer
  - Context-sensitive help panels
  - Interactive tutorials/walkthroughs
  - Community forums embed
  - Ticket submission form

#### Components:
1. **Search Bar**:
   - Federated search across docs, videos, tickets
   - Auto-complete with topic suggestions
   - Recent searches and popular articles

2. **Documentation Reader**:
   - Responsive text formatting
   - Code syntax highlighting
   - Interactive examples and sandbox
   - Version selection for documentation
   - Print/PDF export options

3. **Interactive Tutorials**:
   - Step-by-step guided tours
   - Sandbox environment for practice
   - Progress tracking and completion badges
   - Skip/navigate controls

4. **Support Ticket System**:
   - Categorization and priority selection
   - Attachment upload capabilities
   - Status tracking and notifications
   - Knowledge base article suggestions

#### Data Requirements:
- Documentation content and metadata
- Video transcripts and timestamps
- FAQ entries with categorization
- Support ticket history and status
- User progress and completion tracking
- Community guidelines and moderation rules

#### User Interactions:
- Contextual help triggers (question mark icons)
- "Was this helpful?" feedback voting
- Comment/discussion threads on documentation
- Share specific section linking documentation to UI elements
- Offline downloading for disconnected use
- Accessibility features (screen reader optimization, keyboard nav)

#### Edge Cases:
- Documentation version mismatches: Clear indicators and update prompts
- Search result relevance: Continuous improvement based on click-through
- Offline access: Synchronization mechanisms and conflict resolution
- Community moderation: Spam prevention and quality maintenance
- Accessibility compliance: Regular audits and remediation tracking

---

### 10. Login & Authentication Screens
**Purpose**: Secure access to the FFIRE system

#### Variants:
1. **Login Page** (/login):
   - Email/username and password fields
   - Remember me checkbox
   - Forgot password link
   - Single Sign-On buttons (SAML, OIDC)
   - "Sign Up" link for new users

2. **Registration Page** (/register):
   - Account creation form with validation
   - Role selection (based on invitation or default)
   - Terms of service and privacy policy acceptance
   - Email verification flow

3. **Password Reset** (/reset-password):
   - Secure token-based reset flow
   - Password strength requirements
   - Confirmation and login redirect

4. **Multi-Factor Authentication** (/mfa):
   - TOTP application setup (QR code + manual entry)
   - Backup code generation and download
   - Remember this device option

#### Common Elements:
- Consistent branding and styling
- Accessibility compliance (WCAG 2.1 AA)
- Error messaging with recovery guidance
- Loading states for async operations
- "Remember device" functionality for trusted environments

#### Security Considerations:
- Rate limiting on authentication attempts
- Account lockout after failed attempts
- Password strength enforcement
- Secure password reset mechanisms
- Session management and timeout handling
- CSRF protection on all forms
- HTTPS enforcement everywhere

---

### 11. Error & Empty States
**Purpose**: Consistent, helpful user experience when things don't go as expected

#### Types:
1. **404 Not Found**:
   - Friendly message with suggested navigation
   - Search bar for finding related content
   - Links to popular sections
   - Optional: "Report broken link" functionality

2. **500 Server Error**:
   - Apologetic tone with incident reference
   - Option to report the problem
   - Suggested retry after delay
   - Contact support information

3. **Empty States**:
   - Context-specific illustrations or icons
   - Clear explanation of what should be there
   - Primary call-to-action to populate the space
   - Secondary actions for learning more

4. **Loading States**:
   - Skeleton screens for perceived performance
   - Progressive loading indicators
   - Option to cancel long-running operations
   - Background activity indicators

5. **Permission Denied**:
   - Clear explanation of what access is needed
   - Path to request permissions (if applicable)
   - Contact information for administrators
   - Alternative actions available at current level

#### Implementation Guidelines:
- Consistent visual language and tone
- Actionable guidance wherever possible
- Avoid dead ends - always provide next steps
- Maintain brand voice even in error situations
- Log sufficient detail for troubleshooting while protecting sensitive data

---

### Implementation Priority & Phasing

**Phase 1: Core Investigation Flow**
1. Login/Authentication
2. Dashboard
3. Investigations List
4. Investigation Detail
5. Evidence Explorer (within investigation)

**Phase 2: Operational Features**
6. Reports
7. Analytics
8. Evidence Library (standalone)
9. User Profile & Settings

**Phase 3: Administration & Advanced Features**
10. Administration Console
11. Help & Documentation
12. Advanced Filtering & Saved Views
13. Bulk Operations & Automation
14. Integration & Extension Points

**Phase 4: Optimization & Refinement**
15. Performance tuning
16. Mobile responsiveness optimization
17. Accessibility enhancements
18. Internationalization/i18n foundation
19. Advanced analytics and ML insights
20. Collaboration and workflow features

Each screen should follow the established design system and accessibility guidelines while providing the depth of functionality needed for professional fraud investigation workflows.