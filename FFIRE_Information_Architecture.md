# FFIRE Information Architecture
## Financial Fraud Investigation Reasoning Engine

### 1. Information Architecture Overview

The FFIRE Information Architecture defines the structural design of shared information environments, including the organization, labeling, search, and navigation systems within the Financial Fraud Investigation Reasoning Engine platform. This architecture supports usability and findability for financial investigators, compliance officers, and administrators.

#### Core Principles:
- **User-Centered Design**: Organized around investigator workflows and mental models
- **Progressive Disclosure**: Complex information revealed progressively based on user expertise and task context
- **Consistent Navigation**: Predictable navigation patterns reduce cognitive load
- **Role-Based Access**: Information architecture adapts to user roles (Fraud Analyst, Compliance Officer, Administrator)
- **Evidence-Based Design**: All information structures support evidence-based investigation workflows

### 2. Site Map & Primary Navigation

#### Top-Level Navigation Sections:
1. **Dashboard** - Executive overview and key metrics
2. **Investigations** - Case management and investigation workflow
3. **Evidence** - Evidence collection, management, and analysis
4. **Analytics** - Reporting, trends, and performance metrics
5. **Administration** - System configuration, user management, compliance
6. **Reports** - Investigation reports and audit trails

#### Role-Based Navigation Variants:
- **Fraud Analyst**: Full access to Investigations, Evidence, Dashboard, Reports
- **Compliance Officer**: Access to Audit Logs, Reports, Compliance Dashboard, Administration (limited)
- **Administrator**: Full system access including user management, system configuration, audit trails

### 3. Page Hierarchy & Routing Structure

#### Root Level Routes:
```
/ (Dashboard Home)
/login
/logout
/register
/forgot-password
/reset-password
```

#### Dashboard Module:
```
/dashboard
/dashboard/overview
/dashboard/metrics
/dashboard/etrics/realtime
/dashboard/alerts
/dashboard/notifications
```

#### Investigations Module:
```
/investigations
/investigations/list
/investigations/create
/investigations/{investigationId}
(investigations/{investigationId}/summary
/investigations/{investigationId}/evidence
/investigations/{investigationId}/timeline
/investigations/{investigationId}/reasoning
/investigations/{investigationId}/report
/investigations/{investigationId}/audit
```

#### Evidence Module:
```
/evidence
/evidence/library
/evidence/sources
/evidence/{evidenceId}
```

#### Analytics Module:
```
/analytics
/analytics/dashboard
/analytics/trends
/analytics/performance
/analytics/predictive
```

#### Administration Module:
```
/admin
/admin/users
/admin/roles
/admin/settings
/admin/security
/admin/audit-logs
/admin/system-health
```

#### Reports Module:
```
/reports
/reports/investigations
/reports/compliance
/reports/analytics
/reports/custom
```

### 4. User Flow Architecture

#### Primary Investigation Flow:
```
Login → Dashboard Overview → New Investigation → 
Transaction Input → Evidence Collection Phase → 
Analysis Phase → Reasoning Generation → 
Validation Review → Report Generation → 
Human Review (if required) → Final disposition → 
Audit Trail → Notification/Report Delivery
```

#### Secondary Flows:
- **Evidence Management Flow**: Evidence Collection → Tagging → Cross-referencing → Analysis → Archival
- **Investigation Review Flow**: Case Assignment → Review → Annotation → Approval/Rejection → Feedback Loop
- **Compliance Monitoring Flow**: Alert Generation → Investigation Triage → Resolution Tracking → Reporting
- **System Administration Flow**: User Provisioning → Role Assignment → Permission Configuration → Audit Review

#### Role-Specific Flows:
**Fraud Analyst**:
1. Login → Dashboard (Overview) → Investigations List
2. Select "New Investigation" → Enter Transaction ID
3. System initiates automated investigation workflow
4. Monitor progress via Investigation Dashboard
5. Review evidence as it becomes available
6. Analyze reasoning graph and risk factors
7. Generate preliminary assessment
8. Submit for human review if confidence < threshold
9. Finalize investigation with approval/rejection
10. Generate and export report

**Compliance Officer**:
1. Login → Compliance Dashboard
2. Review alert queue and investigation status
3. Audit selected investigations for procedural compliance
4. Generate compliance reports
5. Escalate issues to appropriate stakeholders

**Administrator**:
1. Login → Administration Console
2. Manage user accounts and roles
3. Configure system settings and integrations
4. Monitor system health and performance
5. Review audit trails and security logs
6. Generate system utilization reports

### 5. Information categorization & Taxonomy

#### Investigation Classification:
- **By Transaction Type**: Wire Transfer, ACH, Credit Card, Debit Card, Check, Cryptocurrency
- **By Risk Level**: Low (0.0-0.3), Medium (0.3-0.7), High (0.7-0.9), Critical (0.9-1.0)
- **By Investigation Status**: Created, Running, Completed, Escalated, Failed, Closed-Approved, Closed-Rejected
- **By Fraud Type**: Identity Theft, Account Takeover, Transaction Fraud, Money Laundering, Fraudulent Merchant
- **By Jurisdiction**: Domestic, Cross-Border, High-Risk Countries, Sanctioned Entities
- **By Amount Tier**: Micro (<$1K), Small ($1K-$10K), Medium ($10K-$100K), Large ($100K-$1M), Mega (>$1M)

#### Evidence Classification:
- **By Source**: Customer Profile, Transaction Data, Merchant Info, Device Fingerprint, Geolocation, Historical Patterns
- **By Type**: Structured Data, Unstructured Text, Images, Timestamps, Network Data, Behavioral Patterns
- **By Relevance**: Primary Evidence, Corroborating Evidence, Contradictory Evidence, Contextual Evidence
- **By Verification Status**: Verified, Pending, Disputed, Refuted

#### User & Role Taxonomy:
- **Fraud Analyst**: Primary investigators conducting day-to-day investigations
- **Senior Analyst**: Experienced investigators handling complex/high-value cases
- **Team Lead**: Supervises analyst teams, handles escalations
- **Compliance Officer**: Ensures regulatory adherence, audits investigations
- **Investigations Manager**: Oversees investigation operations, resource allocation
- **System Administrator**: Manages technical infrastructure, user access, system configuration
- **Executive**: Views aggregated metrics, trends, and executive dashboards

### 6. Navigation Systems

#### Primary Navigation:
- **Persistent Left Sidebar**: Contains main navigation sections with icons and labels
- **Collapsible Navigation**: Sidebar can be collapsed to icon-only mode for more screen real estate
- **Role-Based Visibility**: Navigation items shown/hidden based on user permissions
- **Active State Indicators**: Clear visual indication of current location
- **Badge Notifications**: Unread alerts, pending reviews, etc. shown on navigation icons

#### Secondary Navigation:
- **Top App Bar**: Global actions, user profile, notifications, search, help
- **Contextual Tabs**: Within investigation views for switching between summary, evidence, timeline, etc.
- **Breadcrumbs**: Show hierarchical location within complex sections
- **Pagination Controls**: For list views with large datasets
- **Filter Bars**: Contextual filtering options for data views

#### Tertiary Navigation:
- **Action Menus**: Context-specific actions (kebab/meatball menus)
- **Modal Navigation**: Within wizards or complex modal workflows
- **Tooltip Guidance**: Helper text for complex controls or unfamiliar concepts
- **Progress Indicators**: Multi-step process visualization

### 7. Search & Information Discovery

#### Global Search:
- **Unified Search Bar**: Available in header for searching across investigations, evidence, users, etc.
- **Search Scope Selection**: Ability to limit search to specific domains (investigations only, evidence only, etc.)
- **Saved Searches**: Users can save frequently used search queries
- **Search Suggestions**: Real-time suggestions as user types
- **Search History**: Recent searches accessible via dropdown

#### Faceted Navigation:
- **Investigation Filters**: Status, date range, risk level, amount, fraud type, assigned analyst
- **Evidence Filters**: Source type, date collected, relevance score, verification status
- **User Filters**: Role, status, last login, department
- **Report Filters**: Date range, report type, generated by, status

#### Sorting Options:
- **Default Sort**: Most recent first (for investigations, evidence, alerts)
- **Numeric Sort**: Amount, risk score, confidence (ascending/descending)
- **Alphabetical**: Name, ID, transaction ID
- **Custom Sort**: Priority-based, SLA-based, complexity-based

### 8. Labeling & Taxonomy Systems

#### Navigation Labels:
Use clear, action-oriented labels that match investigator mental models:
- "Start Investigation" rather than "Create New Case"
- "Review Evidence" rather than "View Details"
- "Generate Report" rather than "Export Document"
- "Escalate for Review" rather than "Send to Supervisor"

#### Status Labels:
Consistent status terminology throughout the system:
- **Investigation Status**: Created → Running → [Completed/Escalated/Failed] → [Closed Approved/Closed Rejected]
- **Evidence Status**: Collected → Processing → Available → Archived
- **User Status**: Active → Inactive → Suspended → Archived
- **System Status**: Operational → Degraded → Maintenance → Offline

#### Notification Types:
- **Investigation Updates**: New evidence available, analysis complete, requires review
- **System Alerts**: Performance issues, security events, maintenance windows
- **Reminders**: Pending reviews, SLA breaches, follow-up actions
- **Announcements**: System updates, policy changes, training opportunities

### 9. Data Modeling & Relationships

#### Core Entity Relationship Diagram (Based on Backend Models):
```
User 1 ——* Investigation
Customer 1 ——* Account 1 ——* Transaction 1 ——* Investigation
Transaction *——1 Merchant
Transaction *——1 Location
Transaction *——1 Device
Investigation 1 ——* Evidence
Investigation 1 ——* AuditLog
Investigation 1 ——* FraudCase (optional)
Investigation 1 ——* RiskScore (optional)
```

#### Data Flow Patterns:
1. **Investigation Initiation**: User provides transaction ID → System creates investigation record
2. **Evidence Gathering**: Parallel retrieval of customer, transaction, merchant, device, location data
3. **Analysis Processing**: Rules engine evaluates transactions against known fraud patterns
4. **Knowledge Base Lookup**: Historical case matching for similar patterns
5. **AI Reasoning**: LLM analyzes evidence, rules, and historical data to generate explanation
6. **Validation**: Automated checks for hallucinations and unsupported claims
7. **Report Generation**: Structured report with evidence citations and risk assessment
8. **Human Review**: Optional escalation for low-confidence or complex cases
9. **Archival**: Completed investigations moved to searchable archive

#### Data Lifecycle:
- **Active Investigations**: Real-time updates, frequent access, high performance requirements
- **Completed Investigations**: Read-heavy access, archival storage, compliance retention
- **Expired Investigations**: Purged according to data retention policies (typically 7 years for financial records)
- **Audit Trail**: Immutable logs retained for regulatory compliance (minimum 7 years)

### 10. Content Prioritization & Information Hierarchy

#### Investigation Detail Page Hierarchy:
1. **Primary Information** (Always Visible):
   - Investigation ID & Status Badge
   - Transaction Summary (Amount, Currency, Timestamp)
   - Current Risk Score & Confidence Meter
   - Primary Action Buttons (based on state)

2. **Secondary Information** (Expanded by Default):
   - Evidence Summary Cards (Count by type)
   - Timeline Overview (Key events)
   - Risk Factors Summary

3. **Tertiary Information** (Collapsible/On-Demand):
   - Detailed Evidence Tables
   - Complete Reasoning Graph
   - Full Audit Trail
   - Related Historical Cases

4. **Contextual Actions** (Context-dependent):
   - Add Evidence (manual)
   - Request Additional Analysis
   - Escalate to Specialist
   - Add Notes/Annotations
   - Schedule Follow-up

#### Dashboard Information Hierarchy:
1. **Executive Summary** (At-a-glance):
   - Active Investigations Count
   - High-Risk Cases Requiring Attention
   - Average Investigation Time
   - Success/Escalation Rates

2. **Real-Time Monitoring**:
   - Live Investigation Feed
   - Alert Notifications
   - System Performance Metrics

3. **Trend Analysis**:
   - Fraud Attempt Patterns (Daily/Weekly/Monthly)
   - Geographic Hotspots
   - Attack Vector Distribution
   - ROI Metrics

4. **Operational Details**:
   - Team Workload Distribution
   - Pending Reviews Queue
   - SLA Compliance Metrics
   - Resource Utilization

### 11. Mobile & Responsive Information Architecture

#### Breakpoint-Based Adaptations:
- **Desktop (≥1024px)**: Full sidebar navigation, multi-panel layouts, detailed sidebars
- **Tablet (768-1023px)**: Collapsible sidebar (icon-only by default), adaptive grid layouts
- **Mobile (<768px)**: Bottom navigation drawer, full-screen modals, stacked vertical layouts

#### Mobile-Specific Patterns:
- **Bottom Navigation**: Primary destinations (Dashboard, Investigations, Evidence, Profile)
- **Gesture Navigation**: Swipe between timeline cards, pull-to-refresh lists
- **Contextual Menus**: Long-press for actions, floating action buttons for primary actions
- **Optimized Forms**: Large touch targets, minimal data entry, intelligent defaults
- **Offline Capabilities**: Limited functionality for connectivity-challenged environments

#### Information Density Adaptation:
- **High-Density Views** (Desktop): Detailed tables, side-by-side comparisons, comprehensive dashboards
- **Medium-Density Views** (Tab): Essential information collapsible sections, moderate detail
- **Low-Density Views** (Mobile): Critical information only, progressive disclosure, focus on actions

### 12. Accessibility Information Architecture

#### Screen Reader Navigation Order:
1. Skip to Main Content Link
2. Site Identity (Logo/Brand)
3. Primary Navigation (Landmark: navigation)
4. Page Title (Heading 1)
5. Main Content Region (Landmark: main)
6. Secondary Content/Sidebars (Landmark: complementary)
7. Footer Information (Landmark: contentinfo)

#### Landmark Roles:
- `banner`: Site header with logo and primary actions
- `navigation`: Main navigation menu
- `main`: Primary page content
- `complementary`: Secondary information (sidebar, related content)
- `contentinfo`: Footer with copyright, links, etc.

#### Heading Hierarchy:
Each page follows proper heading structure:
- h1: Page title (unique per page)
- h2: Major sections
- h3: Subsections
- h4: Detailed subsections (rarely needed)
- Proper nesting maintained for screen reader navigation

#### Focus Management:
- Logical tab order following visual flow
- Modal traps keyboard focus within dialog until dismissed
- Skip links bypass repetitive navigation
- Focus returns to triggering element after modal dismissal
- Dynamic content announces changes appropriately for screen readers

### 13. Content Management & Governance

#### Content Ownership:
- **Investigation Content**: Owned by assigned investigator, reviewable by supervisors
- **Evidence Content**: Owned by collection system, immutable after verification
- **System Configuration**: Owned by administrators, change-controlled
- **Templates & Reports**: Owned by compliance/governance team
- **Training Materials**: Owned by enablement/training team

#### Version Control & History:
- **Investigation Edits**: Full audit trail of all changes
- **Evidence Annotations**: Tracked with user and timestamp
- **Configuration Changes**: Git-style version control with approval workflow
- **Report Generations**: Immutable snapshots with generation metadata
- **Audit Logs**: Tamper-evident chronological record of all system interactions

#### Retention & Archival Policies:
- **Active Investigations**: Available indefinitely until resolution
- **Completed Investigations**: Searchable for 7 years (financial regulation standard)
- **Archived Investigations**: Metadata available indefinitely, full retrieval possible
- **Audit Logs**: Immutable storage for minimum 7 years (extendable by regulation)
- **Backup & Disaster Recovery**: Regular backups with tested restore procedures

### 14. Implementation Guidelines

#### Information Architecture Maintenance:
- **Quarterly Reviews**: IA reviewed and updated based on user feedback and analytics
- **Change Control**: Significant IA changes require stakeholder review and testing
- **User Testing**: Regular tree testing and card sorting to validate classification schemes
- **Analytics Integration**: Monitor search success rates, navigation paths, time-to-find metrics
- **Feedback Mechanisms**: In-app feedback for findability issues, confusing labels, missing information

#### Success Metrics:
- **Findability Metrics**: Time to locate specific information, search success rate
- **Efficiency Metrics**: Steps to complete common tasks, navigation errors
- **Satisfaction Metrics**: User satisfaction with information organization
- **Adoption Metrics**: Usage of advanced search features, saved searches, filters
- **Error Metrics**: Wrong turns, backtracking, help requests related to navigation

#### Evolution Guidelines:
- **Backward Compatibility**: New IA elements should not break existing workflows
- **Progressive Enhancement**: Basic functionality available to all, enhancements for capable browsers/devices
- **Scalability**: Structure designed to accommodate 10x growth in users, investigations, data volume
- **Extensibility**: Clear points for adding new sections, features, or user roles
- **Localization Foundation**: Structure supports future internationalization and localization efforts

---

*This Information Architecture serves as the foundational blueprint for the FFIRE frontend implementation, ensuring that the user interface is organized, intuitive, and aligned with investigator workflows and mental models.*