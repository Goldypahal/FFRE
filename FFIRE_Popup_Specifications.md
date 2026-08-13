# FFIRE Popup Specifications
## Financial Fraud Investigation Reasoning Engine

### Popup/Modal Design System Overview

Popups, modals, dialogs, and overlays in FFIRE are designed to capture user attention for critical actions, information display, or data entry while maintaining context and usability. They follow principles of minimal disruption, clear dismissal paths, and accessibility.

#### Popup Types:
1. **Modal Dialogs** - Blocking overlays requiring action before returning to main interface
2. **Non-blocking Overlays** - Informational displays that don't block interaction
3. **Drawers/Slide-ins** - Contextual panels that slide in from side
4. **Tooltips** - Small contextual hints on hover/focus
5. **Notifications** - Temporary informational messages
6. **Context Menus** - Right-click or long-press action menus
7. **Combo Box Selectors** - Dropdowns for choosing from lists
8. **Date/Time Pickers** - Specialized input controls
9. **File Uploaders** - Specialized dialogs for file selection
10. **Wizard/Steppers** - Multi-step process dialogs

#### Core Principles:
1. **Minimal Disruption** - Only use blocking modals when absolutely necessary
2. **Clear Dismissal** - Always provide obvious ways to close (X, ESC, backdrop click, Cancel)
3. **Context Preservation** - Maintain visual connection to underlying content when possible
4. **Accessibility** - Full keyboard navigation, screen reader support, focus management
5. **Consistent Anatomy** - Header, body, footer structure with predictable patterns
6. **Escapability** - Never trap users without a clear escape path
7. **Responsive Design** - Adapt to different screen sizes and orientations

#### Size Categories:
- **Extra Small** (xs): Simple confirmations, tooltips
- **Small** (s): Quick forms, status updates
- **Medium** (m): Standard forms, detail views
- **Large** (l): Complex forms, data previews
- **Extra Large** (xl): Full-screen immersion (rarely used)
- **Full Screen**: Dedicated views for complex workflows

#### Anatomy:
1. **Header** (optional but recommended):
   - Title (clear, action-oriented)
   - Close button (X icon in top-right)
   - Drag handle (if draggable)
2. **Body**:
   - Primary content (form, information, visualization)
   - Scrolling capability if content exceeds viewport
3. **Footer** (optional):
   - Action buttons (primary, secondary, cancel)
   - Left-aligned secondary actions, right-aligned primary actions
   - Loading indicators, progress bars

#### Behavioral Guidelines:
1. **Modal vs Non-modal**:
   - Modal: Critical actions, data entry with validation, irreversible actions
   - Non-modal: Informational displays, contextual help, non-critical selections
2. **Backdrop**:
   - Modal: Semi-transparent backdrop that closes on click (configurable)
   - Non-modal: May have no backdrop or translucent backdrop
3. **Keyboard**:
   - ESC: Always closes (unless preventing data loss)
   - Enter: Primary action (if focused and valid)
   - Tab: Navigation within popup, trap focus when modal
4. **Animation**:
   - Fade-in/scale-up for entrance
   - Fade-out/scale-down for exit
   - Respect prefers-reduced-motion setting
5. **Focus Management**:
   - On open: Focus first focusable element or close button
   - On close: Return focus to triggering element
   - During: Trap focus within popup (for modals)
6. **Scrolling**:
   - Body scrolls if content exceeds height
   - Header/footer remain fixed
   - Prevent background scroll when popup open

### Complete Popup Catalog

#### 1. Confirmation & Alert Dialogs

**Delete Confirmation Dialog**
- Title: "Delete [Item Type]"
- Icon: Trash can (🗑️) in header
- Size: Medium
- Modal: True (blocking)
- Body:
  - Warning icon (⚠️)
  - Primary message: "Are you sure you want to delete this [item]?"
  - Secondary message: "This action cannot be undone." (if applicable)
  - For bulk: "Delete [count] selected items?"
  - Safety confirm: "Type DELETE to confirm" input (for critical deletes)
- Footer:
  - Cancel button (secondary/ghost)
  - Delete button (danger)
- ESC Behavior: Closes dialog ( cancels action )
- Enter Behavior: Triggers delete if validation passes
- Accessibility:
  - aria-labelledby and aria-describedb
  - Role="alertdialog"
  - Focus trap
  - Screen reader announces as alert dialog

**Critical Action Confirmation**
- Similar structure but with more severe warnings
- Examples: "Permanently delete investigation", "Disable authentication method"
- May include additional safety steps (typing confirmation, 2-step escalation)

**Information Alert**
- Title: Context-specific ("Success", "Error", "Warning", "Info")
- Icon: Corresponding symbol (✅, ❌, ⚠️, ℹ️)
- Size: Small/Medium
- Modal: False (non-blocking) or true for critical errors
- Body: Message with optional details toggle
- Footer:
  - Primary action button (if applicable)
  - Close button (X or "Got it")
- Auto-dismiss: Optional for non-critical info (timeout: 5-10 seconds)
- Position: Top-center, top-right, or bottom-right (non-interruptive)
- Accessibility:
  - Role="alert" for auto-dismiss
  - Role="dialog" for blocking
  - Live region updates for status changes

#### 2. Form & Data Entry Dialogs

**New Investigation Wizard**
- Title: "Start New Investigation"
- Size: Large
- Modal: True
- Body:
  - Stepper/header showing progress (1 of 3 steps)
  - Form fields varies by step:
    * Step 1: Transaction ID input + lookup button
    * Step 2: Customer/merchant verification
    * Step 3: Investigation configuration (priority, tags, notes)
  - Validation inline and on step transition
- Footer:
  - Previous button (secondary, disabled on first step)
  - Next/Submit button (primary, disabled until valid)
  - Cancel button (secondary)
- Features:
  - Linear progression with optional non-linear navigation
  - Save & resume later capability
  - Contextual help tooltips in each step
  - Preview/summary before final submission
- Accessibility:
  - Aria-label for each step
  - Proper form field labeling
  - Error announcement and focus management

**Edit Investigation Details**
- Title: "Edit Investigation: [ID]"
- Size: Medium/Large
- Modal: True
- Body:
  - Tabbed interface or accordion for sections:
    * Basic Info (read-only transaction data)
    - Investigation Settings (priority, tags, assigned analyst)
    - Custom Fields (if applicable)
    - Notes & Annotations
  - Inline editing with save/cancel per section OR global save
- Footer:
  - Save Changes (primary)
  - Cancel (secondary)
  - Reset to Original (secondary, shows if modified)
- Features:
  - Dirty tracking (unsaved changes warning on close)
  - Field-level validation
  - Preview of how changes affect risk scores
- Accessibility:
  - Proper tab/accordion semantics
  - Live validation announcements
  - Focus return to edited field on validation error

**Add Evidence Dialog**
- Title: "Add Evidence"
- Size: Medium
- Modal: True
- Body:
  - Tabbed interface:
    * Upload Files (drag & drop area + file picker)
    * External Systems (search connected data sources)
    * Manual Entry (form for creating evidence record)
    * Link Existing (search current investigation evidence)
  - File validation: type, size, virus scan
  - External search: filters, sorting, preview
  - Manual entry: fields vary by evidence type
- Footer:
  - Add Evidence (primary)
  - Cancel (secondary)
- Features:
  - Multiple file upload
  - Progress indicators for uploads/virus scanning
  - Duplicate detection warnings
  - Metadata extraction preview
  - Tag suggestions during manual entry
- Accessibility:
  - Proper tab semantics
  - Form field associations
  - Screen reader friendly drag & drop instructions

**Filter Editor Dialog**
- Title: "Edit Filter" or "Manage [Item Type] Filters"
- Size: Medium/Large
- Modal: True
- Body:
  - Filter condition builder:
    * Dropdown for field selection
    - Dropdown for operator (equals, contains, between, etc.)
    - Input for value (type-aware: text, number, date, enum)
    - AND/OR logic toggles between conditions
    - Remove condition button (X)
    - Add condition button (+)
  - Preview of how filter affects current data set
  - Saved filter management (if editing saved filter)
- Footer:
  - Apply Filter (primary)
  - Cancel (secondary)
  - Save As... (secondary, if creating new)
  - Reset to Default (secondary)
- Features:
  - Nested condition groups (advanced mode)
  - Field-specific operators (date ranges, text matches)
  - Value helpers (calendar for date, lookup for enums)
  - Validation of incompatible combinations
  - Performance impact estimation
- Accessibility:
  - Proper labeling of dynamic form elements
  - Keyboard accessible condition builder
  - ARIA live region for preview updates

**Bulk Action Dialog**
- Title: "Perform Bulk Action on [count] Items"
- Size: Medium
- Modal: True
- Body:
  - Summary of selected items (types, counts)
  - Action selection dropdown (context-specific)
  - Action-specific parameters form:
    * For "Assign to Analyst": User picker + notification toggle
    * For "Change Status": Status dropdown + reason required
    * For "Add Tags": Tag selector + replace/append toggle
    * For "Export": Format selector + options (include metadata, etc.)
  - Warning about irreversible actions (if applicable)
- Footer:
  - Perform Action (primary)
  - Cancel (secondary)
- Features:
  - Preview of first few items that will be affected
  - Select all/none buttons for parameter application
  - Dry run option (show what would happen without executing)
  - Progress tracking for long-running bulk actions
- Accessibility:
  - Clear labeling of action-specific controls
  - Error summarization and prevention
  - Focus management on open and validation errors

#### 3. Information & Detail Display

**Evidence Viewer Modal**
- Title: "Evidence: [ID or Description]"
- Size: Large (responsive to content)
- Modal: True (typically)
- Body:
  - Header: Evidence metadata (source, type, date collected, tags)
  - Main Content: Type-optimized display:
    * Image: Zoomable viewer with pan/rotate
    * Document: Text viewer with search, highlight, page navigation
    * Video/Audio: Player with controls, transcript/captions
    * Spreadsheet: Grid viewer with sorting, filtering
    * JSON/XML: Syntax-highlighted viewer with collapse/expand
    * Text: Reader with search, font size adjustment
  - Sidebar: Actions and metadata
    * Relevance score adjustment (slider + numeric)
    * Tag management
    * Notes/comments thread
    * Related investigations
    * Download original
    - Expand/collapse sidebar
- Footer:
  - Actions row: Tag as Relevant/Irrelevant, Add Note, Download
  - Close button (X in header typically sufficient)
- Features:
  - Touch-friendly gestures (pinch to zoom, swipe to navigate)
  - Fullscreen toggle button
  - Print/Save as PDF option
  - Annotation tools (highlight, comment, draw)
  - Version history (for documents)
  - Usage statistics
- Accessibility:
  - Semantic structure appropriate to content type
  - Keyboard navigation for all interactive elements
  - Screen reader announcements for zoom/pan state
  - Alternative text for non-decorative images
  - Captions/transcripts for media

**Investigation Reasoning Graph Modal**
- Title: "Reasoning Graph: Investigation [ID]"
- Size: Extra Large/Large
- Modal: True
- Body:
  - Toolbar: Layout controls (fit-to-screen, zoom controls, reset)
  - Node/Edge filters: Show/hide by type, confidence threshold
  - Search: Find nodes by label/content
  - Main Canvas: Interactive node-link diagram
    * Node types: Evidence (circle), Rule Check (square), Knowledge Lookup (diamond), Decision Point (hexagon)
    * Edge labels: Confidence percentage, reasoning type
    * Interactive features: Node expansion, detail tooltips, path highlighting
    * Navigation: Pan, zoom, miniature overview window
    * Selection: Multi-select for bulk operations
    * Context menus: Right-click on nodes/edges for actions
  - Details Panel: Collapsible sidebar showing selected item details
- Footer:
  - Export options: PNG, SVG, JSON (graph data)
  - Close button
- Features:
  - Lane/swimlane layout options
  - Auto-layout algorithms (hierarchical, force-directed, circular)
  - Custom styling based on node/edge properties
  - Animation during layout transitions
  - Performance optimization for large graphs
  - Offline capability for previously loaded graphs
- Accessibility:
  - ARIA labels for nodes and edges
  - Keyboard navigation to navigate graph
  - Screen reader announcements for selection changes
  - Text alternative description availability
  - High contrast mode support

**Report Preview Modal**
- Title: "Preview Report: [Title]"
- Size: Large
- Modal: True
- Body:
  - Report header: Title, date range, generation info
  - Main content: Report preview matching final output format
  - Sidebar: Metadata and actions
    - Generation details (time, user, parameters)
    - Evidence citations list
    - Sharing options (email, secure link)
    - Regenerate with different parameters
    - Download options (PDF, Excel, CSV)
- Footer:
  - Close button (primary action often)
  - Regenerate Report (secondary)
- Features:
  - Page navigation for multi-page reports
  - Text selection and copying
  - Search within report
  - Zoom controls
  - Print-friendly view
  - Access to underlying data/JSON
- Accessibility:
  - Proper heading structure
  - Alternative text for charts/graphics
  - Keyboard navigable controls
  - Screen reader friendly layout
  - Contrast compliance

**User Profile Modal**
- Title: "My Profile" or "[Username] Profile"
- Size: Medium
- Modal: True
- Body:
  - Sectioned layout:
    * Profile Information: Avatar, name, email, phone, bio
    * Preferences: Theme, notifications, language, format
    * Security: Password change, MFA setup, session management
    * Connected Applications: OAuth clients, API keys
    * Activity Summary: Recent logins, investigations, reports
  - Edit modes per section with save/cancel
- Footer:
  - Save Changes (primary, context-sensitive based on edited section)
  - Cancel (secondary)
- Features:
  - Avatar upload with cropping/resizing
  - Password strength indicator
  - MFA QR code and backup codes
  - Session list with location/IP and logout option
  - Connected apps with revoke access buttons
  - Export personal data (GDPR/CCPA)
- Accessibility:
  - Proper form labeling and validation
  - Screen reader announcements for dynamic updates
  - Focus management in edit modes
  - ARIA live regions for status updates

#### 4. Contextual & Helper Popups

**Tooltip**
- Trigger: Hover/focus on element with supplemental information
- Size: Auto-sizing based on content
- Position: Auto-positioning (prefer top, fallback to bottom/left/right)
- Content:
  - Plain text (most common)
  - Rich text with formatting (limited)
  - Images/icons (for visual examples)
  - Interactive elements (rare, for complex explanations)
- Behavior:
  - Appear after short delay (hover)
  - Appear on focus (keyboard navigation)
  - Disappear on hover-out/blur or ESC
  - Follow mouse/pointer with slight offset
  - Smart repositioning to stay within viewport
- Styling:
  - Subtle shadow, rounded corners
  - Dark text on light background or vice versa based on theme
  - Maximum width to prevent excessive stretching
- Accessibility:
  - ARIA-describedby association
  - Appears on keyboard focus
  - Dismissable with ESC
  - Sufficient contrast
  - Not relied upon as sole means of conveying information

**Column Filter Input**
- Location: Table header row
- Size: Small (fits in column header)
- Trigger: Click filter icon or focus
- Content:
  - Text input (for text columns)
  - Number range inputs (min/max) for numeric columns
  - Date range picker for date columns
  - Dropdown selector for enum/category columns
  - Multiselect for tag-based columns
- Behavior:
  - Appear in place or overlay slightly
  - Apply on Enter or debounce (300ms)
  - Clear button (X) when not empty
  - ESC cancels and closes
- Features:
  - Persistent filters (stored in URL or user preferences)
  - Visual indicator when active (highlighted header)
  - Tooltip showing current filter values
  - Multi-value display for complex filters
- Accessibility:
  - Label associated with input
  - Keyboard navigable controls
  - Screen reader announces filter application
  - Error states clearly communicated

**Date/Time Picker**
- Trigger: Click on date/input field or calendar icon
- Size: Medium
- Position: Anchored to input field (prefer below, fallback above/side)
- Content:
  - Calendar grid (month view)
  - Year/month selectors (dropdowns at top)
  - Time picker (if time included): hour/minute/second dials or inputs
  - Today button
  - Clear button
  - Cancel button (X)
- Behavior:
  - Click date to select
  - Type directly in supported inputs
  - Week numbers optional display
  - Minimum/maximum date restrictions
  - Disabled dates (holidays, blackout periods)
  - Timezone selection (if applicable)
- Features:
  - Range selection (two dates)
  - Relative date shortcuts (Today, Yesterday, Last 7 days, etc.)
  - Presets for common intervals
  - Keyboard navigation (arrows, page up/down, home/end)
  - Typing support with format validation
- Footer:
  - Apply/OK (primary)
  - Clear (secondary)
  - Cancel (secondary)
- Accessibility:
  - Proper labeling of all interactive elements
  - Keyboard navigable grid
  - Screen reader announces selected date
  - ARIA live region for changes
  - High contrast mode support

**Combo Box / Select Dropdown**
- Trigger: Click on field or dropdown arrow
- Size: Auto-width based on content (with max width)
- Position: Anchored to input (prefer below, fallback above)
- Content:
  - Searchable list (filter as you type)
  - Grouped options (with headers)
  - Selected state indicator
  - Disabled items (grayed out, not selectable)
  - Loading indicator (for remote options)
  - No results message
- Behavior:
  - Filter as you type in search box
  - Arrow keys to navigate options
  - Enter/Space to select
  - ESC to close without selection
  - Click outside to close
  - Select on blur if valid
  - Optional: Allow custom values (combobox vs select)
- Features:
  - Virtualization for long lists
  - Group headers and dividers
  - Icon support alongside text
  - Tooltips for truncated options
  - Custom templates for complex options (images, status indicators)
  - Prefetching for anticipated searches
- Footer:
  - None typically (selection closes dropdown)
  - Or: Clear selection button
- Accessibility:
  - Proper label association
  - ARIA expanded state
  - Keyboard navigable options
  - Screen reader announces selection
  - Sufficient touch target size

**Notification Toast**
- Trigger: System event requiring user awareness
- Size: Small (fixed width, auto height)
- Position: Default: top-right or bottom-right (configurable)
- Alternative positions: top-center, bottom-center, inline (for page-specific)
- Content:
  - Icon indicating type (success, error, warning, info)
  - Primary message (required)
  - Secondary message/detail (optional)
  - Action button(s) (optional, max 2)
  - Progress indicator (optional, for ongoing operations)
  - Dismiss button (X) or swipe to dismiss
- Behavior:
  - Appear with slide-in/fade-in animation
  - Auto-dismiss after timeout (success/info: 5s, warning: 10s, error: until dismissed)
  - Pause timer on hover
  - Queue multiple notifications
  - Prevent duplicate similar notifications (deduplication)
  - Action button triggers specific behavior
- Types:
  - Success: Green background, checkmark icon
  - Error: Red background, exclamation icon
  - Warning: Yellow background, warning icon
  - Info: Blue background, info icon
  - Loading: Blue background, spinner icon (typically no auto-dismiss)
- Features:
  - Action buttons: "Retry", "Undo", "View Details", "Settings"
  - Progress indication for uploads/processes
  - Persistent notifications for critical issues (until resolved)
  - Notification center/history access
  - Do-not-disturb mode
  - Per-type mute options
- Accessibility:
  - ARIA live region (polite for most, assertive for critical)
  - Dismissable with ESC
  - Keyboard navigable to action buttons
  - Sufficient contrast
  - Not relied upon as sole notification method for critical alerts
  - Announcement of number of active notifications

**Context Menu (Right-click)**
- Trigger: Right-click (desktop) or long-press (touch)
- Size: Auto-width based on content (with min/max constraints)
- Position: Anchored to cursor/touch point (with viewport collision avoidance)
- Content:
  - List of actions (icon + text)
  - Dividers for logical grouping
  - Submenus indicated by right arrow
  - Disabled items (grayed out)
  - Shortcut key display (if applicable)
  - Loading state (for dynamic menus)
- Behavior:
  - Appear near cursor with smart positioning
  - Click outside to close
  - ESC to close
  - Navigate with arrows, Enter/Space to activate
  - Typing to jump to letter (progressive filtering)
  - Submenu hover delay to prevent accidental activation
- Features:
  - Icons alongside text for recognition
  - Nested submenus for complex hierarchies
  - Separator lines for grouping
  - Access keys (Alt+letter) for frequent actions
  - Dynamic content based on context (selection, object state)
  - Caching of recently used menus
- Accessibility:
  - Keyboard trigger (Shift+F10 or context menu key)
  - Proper labeling of actions
  - Screen reader announces available actions
  - ESC to close
  - Not relied upon as sole means of accessing actions
  - Touch-friendly minimum size

#### 5. Specialized Investigation Popups

**Hypothesis Builder Dialog**
- Title: "Add Investigative Hypothesis"
- Size: Medium
- Modal: True
- Body:
  - Form fields:
    * Hypothesis Statement (required text area)
    - Confidence Level (slider 0-1.0 with labels: Low/Medium/High)
    - Supporting Evidence (multiselect from current evidence)
    - Contradicting Evidence (multiselect from current evidence)
    - Related Rules/Knowledge (multiselect)
    - Notes/Justification (text area)
  - Validation: Statement required
  - Preview: How this hypothesis fits in reasoning graph
- Footer:
  - Add Hypothesis (primary)
  - Cancel (secondary)
- Features:
  - Evidence lookup with relevance sorting
  - Confidence impact preview
  - Link to existing similar hypotheses
  - Tagging capability
  - Attach notes or documents
- Accessibility:
  - Proper form labeling
  - Live validation announcements
  - Focus management

**Request Information Form**
- Title: "Request Information from [Source]"
- Size: Medium/Large
- Modal: True
- Body:
  - Source Selection (if not pre-specified):
    * Dropdown of connected systems
    - Manual entry of contact information
  - Request Type:
    * Predefined templates (subpoena, data request, affidavit)
    - Custom request (free form with guidelines)
  - Information Requested:
    * Checklist of common data types
    - Specific fields/records description
    - Date range selectors
    - Format requirements (CSV, JSON, XML, PDF)
  - Legal/Jurisdictional:
    * Applicable laws/regulations
    - Required authorization level
    - Estimated response time
    - Cost implications (if any)
  - Delivery Method:
    * Secure portal, encrypted email, SFTP, physical media
    - Notification preference (email, portal alert)
- Footer:
  - Send Request (primary)
  - Cancel (secondary)
  - Save as Template (secondary)
- Features:
  - Template library with customization
  - Attach supporting documents/case numbers
  - Tracking number generation
  - Delivery confirmation requests
  - Legal review workflow option
- Accessibility:
  - Proper form labeling and validation
  - Screen reader friendly dynamic sections
  - Focus management on validation errors

#### 6. Administrative & Configuration Popups

**Role Permissions Matrix**
- Title: "Permissions for Role: [Role Name]"
- Size: Extra Large/Large
- Modal: True (often large enough to warrant)
- Body:
  - Two-panel layout:
    * Left: Permission categories/modules (accordion/tree)
    * Right: Detailed permissions grid for selected category
  - Grid shows:
    * Resource/Action rows
    * Permission columns: None, Read, Create, Update, Delete, Export
    - Cell states: Granted (check), Denied (X), Inherited (arrow), Not Applicable
  - Search/filter permissions
  - Select all/none for category
  - Inheritance visualization
- Footer:
  - Save Changes (primary)
  - Cancel (secondary)
  - Reset to Inherited (secondary, shows if modified)
- Features:
  - Bulk operations: Grant/Deny selected permissions
  - Copy permissions from another role
  - View effective permissions for sample user
  - Conflict highlighting (when rules contradict)
  - Export matrix (CSV/Excel)
  - History of changes
- Accessibility:
  - Proper table semantics
  - Keyboard navigable grid
  - Screen reader announces cell states
  - Focus management in editable cells
  - ARIA live region for bulk operations

**Integration Configuration Dialog**
- Title: "Configure [Integration Name]"
- Size: Medium/Large
- Modal: True
- Body:
  - Tabbed interface:
    * Connection: Authentication, endpoints, test connection
    * Data Mapping: How external data maps to internal models
    * Sync Settings: Frequency, filters, batch size
    * Error Handling: Retry policies, alerts, dead letter queue
    * Monitoring: Health checks, metrics, logging level
  - Connection tab:
    * Auth type selector (API key, OAuth, basic, custom)
    - Credential fields (masked input)
    - Endpoint URL(s) with validation
    - Test Connection button with results display
  - Data mapping tab:
    * Visual mapping interface or field-by-field editor
    * Transformation functions (date format, concatenation, lookup)
    - Validation rules and examples
    - Preview with sample data
  - Sync settings:
    * Frequency selector (disabled, manual, cron expression)
    - Filter builders for inclusion/exclusion
    - Batch size and concurrency settings
    - Timing windows (only run during off-hours)
- Footer:
  - Save Configuration (primary)
  - Cancel (secondary)
  - Test Connection (secondary)
- Features:
  - Environment-specific configurations (dev/stage/prod)
  - Credential vault integration indicators
  - Schema validation and compatibility checking
  - Usage analytics and performance metrics
  - Backup/restore configuration
- Accessibility:
  - Proper tab semantics
  - Form field associations
  - Screen reader friendly dynamic content
  - Focus management on validation errors

#### 7. Export & Import Dialogs

**Export Dialog**
- Title: "Export [Item Type]"
- Size: Medium
- Modal: True
- Body:
  - Format Selection:
    * Radio buttons: CSV, Excel (XLSX), JSON, PDF
    - Format-specific options appear below selection
  - CSV/Excel Options:
    * Include headers (checked by default)
    * Include metadata columns (toggle)
    * Date format selector
    * Text qualifier (none, single quote, double quote)
    - Character encoding (UTF-8, UTF-16, etc.)
  - JSON Options:
    * Pretty print (checked by default)
    * Include null values (toggle)
    * date format (ISO 8601, Unix timestamp)
  - PDF Options:
    * Page size (Letter, A4, etc.)
    * Orientation (Portrait/Landscape)
    * Include headers/footers (toggle)
    - Include page numbers (toggle)
  - Selection Scope:
    * All matching current filters/search
    * Currently selected items ([count])
    * Current page only ([count] items)
  - Advanced Options:
    * Include related data (toggle with specificity)
    * Compress output (ZIP for multiple files)
    - Split large outputs (by size or record count)
- Footer:
  - Export (primary)
  - Cancel (secondary)
  - Preview (secondary, shows first 10 rows)
- Features:
  - Progress bar for large exports
  - Estimated time/size display
  - Cancel during export
  - Open containing folder after completion
  - Email results option (for smaller exports)
  - Save as default format for user
- Accessibility:
  - Proper labeling of all controls
  - Screen reader announcements for progress
  - Focus management
  - Error handling with specific messages

**Import Dialog**
- Title: "Import [Item Type]"
- Size: Medium/Large
- Modal: True
- Body:
  - File Selection:
    * Drag & drop area or file picker
    - Supported formats listed (CSV, Excel, JSON, etc.)
    - Maximum file size indicator
  - Format Detection:
    * Auto-detected format display
    - Manual override dropdown
  - Mapping Preview:
    * First few rows with column detection
    - Manual column mapping interface (drag source to target)
    - Validation warnings for mismatches
    - Transform preview (show sample transformations)
  - Validation Options:
    * Validate before importing (checked by default)
    * Skip invalid rows (toggle)
    * Error report format (CSV, JSON)
    * Halt on first error (toggle)
  - Duplicate Handling:
    * Skip duplicates (default)
    * Update matching records
    * Reject and abort
    * Create new with different ID
- Footer:
  - Import (primary)
  - Cancel (secondary)
  - Download Template (secondary)
- Features:
  - Progress bar with stages (reading, validating, transforming, importing)
  - Error reporting with downloadable details
  - Preview of first 10 imported items
  - Ability to save mapping configuration for reuse
  - Transactional import (all or nothing) option
- Accessibility:
  - Proper labeling and associations
  - Screen reader announcements for stages
  - Focus management during mapping step
  - Error summarization and prevention

#### Implementation Guidelines

**Animation & Timing:**
1. **Entrance** - Fade-in (200ms) + scale-up (95% to 100%)
2. **Exit** - Fade-out (150ms) + scale-down (100% to 95%)
3. **Tooltips** - Fade-in/fade-out (100ms each)
4. **Notices/Toasts** - Slide-in (200ms) + delay + slide-out (200ms)
5. **Respect** - prefers-reduced-motion: use fade only or disable
6. **Loading States** - Spinner or skeleton with appropriate timing

**Focus Management:**
1. **On Open** - Focus first focusable element or close button
2. **During** - Trap focus for modals, allow escape for non-modals
3. **On Close** - Return focus to triggering element
4. **Exceptions** - For destructive actions, may focus on Cancel first
5. **Dynamic Content** - Announce significant changes to screen readers

**Positioning & Constraints:**
1. **Viewport Awareness** - Never exceed viewport dimensions
2. **Smart Positioning** - Adjust to stay visible (flip overlap)
3. **Maximum Height** - Calculate based on viewport minus header/chrome
4. **Overflow** - Scroll body content when exceeding max height
5. **Blocking Dialogs** - May disable background scroll when open
6. **Non-blocking** - Allow background interaction, may obscure briefly

**Responsive Behavior:**
1. **Mobile** - Often full width, top-attached modals
2. **Tablet** - May adjust width/height based on orientation
3. **Desktop** - Centered with appropriate max-width
4. **Full Screen** - Rarely used, for immersive workflows only
5. **Breakpoints** - Define specific behaviors at 640px, 768px, 1024px

**Layering & Z-index:**
1. **Background** - Page content (z-index: 1)
2. **Popup Backdrop** - Semi-transparent overlay (z-index: 1000)
3. **Popup Container** - Dialog content (z-index: 1050)
4. **Toasts/Notifications** - Temporary alerts (z-index: 1100)
5. **Tooltips** - Small contextual hints (z-index: 1200)
6. **Drag Placeholders** - During drag operations (z-index: 1300)
7. **Mouse Pointer** - Always on top (z-index: 1350)

**Accessibility Requirements:**
1. **Modal Semantics** - role="dialog" + aria-modal="true"
2. **Labeling** - aria-labelledby pointing to title element
3. **Description** - aria-describedby pointing to description (if present)
4. **Focus Trap** - Prevent escape for modal dialogs
5. **Return Focus** - Always return to triggering element on close
6. **Close Mechanism** - Visible X button + ESC key support
7. **Screen Reader** - Announce dialog opening/closing
8. **Live Regions** - For dynamic content updates
9. **Color Contrast** - WCAG AA minimum
10. **Touch Targets** - Minimum 44x44dp for interactive elements
11. **Keyboard Navigation** - Full navigation without mouse
12. **Skip Links** - For very large dialogs with internal navigation

**Performance Considerations:**
1. **Lazy Loading** - Load tab content when tab is activated
2. **Virtualization** - For long lists within dialogs (permissions, users, etc.)
3. **Memoization** - Cache expensive computations
4. **Image Optimization** - Proper sizing and compression for previews
5. **Debouncing** - Input filtering, resize events
6. **Component Mounting** - Unmount when closed to free resources
7. **State Cleanup** - Reset form state, cancel subscriptions on close
8. **Animation Performance** - Use transform/opacity, layout-threshold

**Testing Checklist:**
1. **Basic Functionality** - Open, interact, close via multiple methods
2. **Keyboard** - Full navigation, focus trapping, ESC behavior
3. **Accessibility** - Screen reader, color blindness, zoom, voice control
4. **Responsiveness** - All breakpoints, orientation changes
5. **State Management** - Form values, validation, dirty tracking
6. **Animation** - Smooth transitions, respects reduced motion
7. **Error Handling** - Network failures, invalid inputs, server errors
8. **Performance** - Large data handling, animations, memory leaks
9. **Accessibility** - Specific popup types (tooltips, modals, toasts)
10. **Internationalization** - Text expansion, RTL, localization

This comprehensive popup specification ensures that every overlay, modal, dialog, and contextual popup in the FFIRE system is designed for clarity, accessibility, and minimal disruption while providing the necessary focus for critical investigative actions and information display.