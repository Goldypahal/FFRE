# FFIRE Button Specifications
## Financial Fraud Investigation Reasoning Engine

### Button Design System Overview

All buttons in the FFIRE system follow a consistent design language that prioritizes clarity, accessibility, and efficiency for fraud investigators working in high-stakes environments.

#### Button Variants:
1. **Primary** - Main call-to-action (solid background)
2. **Secondary** - Secondary actions (outline/border)
3. **Ghost** - Tertiary actions (transparent background)
4. **Danger** - Destructive actions (red-themed)
5. **Link** - Text-only for minimal visual weight

#### Sizes:
- **Extra Small** (xs): Compact spaces, toolbars
- **Small** (s): Dense information displays
- **Medium** (m): Default standard size
- **Large** (l): Touch-friendly, accessibility focus
- **Extra Large** (xl): Prominent calls-to-action

#### States:
- **Default**: Enabled, ready for interaction
- **Hover**: Visual feedback for mouse users
- **Active/Pressed**: During click/tap interaction
- **Disabled**: Unavailable action (with tooltip explaining why)
- **Loading**: Indicates asynchronous operation in progress
- **Focus**: Keyboard navigation highlight

### Complete Button Catalog

#### 1. Navigation & Layout Buttons

**Menu Toggle Button** (Sidebar Collapse/Expand)
- Location: Header (mobile) or Sidebar header
- Icon: Hamburger (☰) / Close (×)
- Variant: Ghost
- Size: Medium
- Tooltip: "Show/Hide Navigation"
- Behavior: Toggles sidebar visibility
- Shortcut: Ctrl+\ (Cmd+\ on Mac)
- Accessibility: aria-label="Toggle navigation", role="button"

**Back Button** 
- Location: Header left side
- Icon: Arrow left (←)
- Variant: Ghost or Link
- Size: Small/Medium
- Tooltip: "Go back"
- Behavior: Navigates to previous page in history
- Shortcut: Alt+Left Arrow
- Accessibility: aria-label="Go back to previous page"

**Close Button** (Modals, Drawers, Popovers)
- Location: Top-right corner
- Icon: X (×)
- Variant: Ghost
- Size: Small
- Tooltip: "Close"
- Behavior: Dismiss current overlay
- Shortcut: Escape key
- Accessibility: aria-label="Close dialog"

#### 2. Action Buttons - Investigation Lifecycle

**New Investigation Button**
- Location: Investigations page header, Dashboard quick actions
- Text: "New Investigation" (+ icon optional)
- Variant: Primary
- Size: Medium/Large
- Icon: Zap (⚡) or Plus (+)
- Tooltip: "Start a new fraud investigation"
- Behavior: Opens investigation creation modal/wizard
- Shortcut: Ctrl+N (Cmd+N on Mac)
- Accessibility: aria-label="Start new investigation"
- Loading State: Shows spinner when creating initial record

**Resume Investigation Button**
- Location: Investigation Detail header
- Text: "Resume" (▶️ icon)
- Variant: Primary
- Size: Small
- Tooltip: "Resume paused investigation"
- Behavior: Resumes suspended investigation processing
- Conditions: Only enabled when investigation is paused
- Accessibility: aria-label="Resume investigation"

**Pause Investigation Button**
- Location: Investigation Detail header
- Text: "Pause" (⏸️ icon)
- Variant: Secondary
- Size: Small
- Tooltip: "Pause investigation processing"
- Behavior: Temporarily halts AI analysis while preserving state
- Conditions: Only enabled when investigation is running
- Accessibility: aria-label="Pause investigation"

**Stop Investigation Button**
- Location: Investigation Detail header (in dropdown menu)
- Text: "Stop" (⏹️ icon)
- Variant: Danger
- Size: Small
- Tooltip: "Terminate investigation"
- Behavior: Cancels investigation with confirmation dialog
- Confirmation: "Are you sure you want to stop this investigation? All progress will be lost."
- Accessibility: aria-label="Stop investigation"

**Export Investigation Button**
- Location: Investigation Detail header, Investigation row actions
- Text: "Export" (📥 icon) or format-specific (PDF, CSV, JSON)
- Variant: Secondary
- Size: Small
- Tooltip: "Export investigation data"
- Behavior: Opens export format selection dialog
- Menu Options: PDF Report, JSON Data, CSV Evidence, Full Package
- Accessibility: aria-label="Export investigation"

**Share Investigation Button**
- Location: Investigation Detail header
- Text: "Share" (🔗 icon)
- Variant: Secondary
- Size: Small
- Tooltip: "Share investigation with team"
- Behavior: Opens sharing dialog with permission controls
- Options: Email link, Generate secure link, Assign to user/team
- Accessibility: aria-label="Share investigation"

**Add Note Button**
- Location: Investigation Detail, Evidence items, Timeline entries
- Text: "Add Note" or just (+) icon
- Variant: Ghost
- Size: Small
- Tooltip: "Add note or annotation"
- Behavior: Opens rich text note editor at current context
- Persistence: Notes saved with timestamp and user ID
- Accessibility: aria-label="Add note"

**Escalate Button**
- Location: Investigation Detail header, Investigation actions menu
- Text: "Escalate" (⚠️ icon)
- Variant: Warning/Secondary
- Size: Small
- Tooltip: "Escalate to supervisor or specialist team"
- Behavior: Opens escalation form with reason and priority selection
- Updates: Changes investigation status to "Escalated"
- Notification: Alerts designated responders
- Accessibility: aria-label="Escalate investigation"

**Assign to Me Button**
- Location: Investigation row actions, Investigation detail (when unassigned)
- Text: "Assign to Me" or just user icon (+)
- Variant: Secondary
- Size: Small
- Tooltip: "Assign this investigation to yourself"
- Behavior: Assigns current user as investigator
- Confirmation: May show undo toast briefly
- Accessibility: aria-label="Assign investigation to me"

**Reassign Button**
- Location: Investigation detail (when assigned)
- Text: "Reassign" (user icon with arrows)
- Variant: Secondary
- Size: Small
- Tooltip: "Assign investigation to another team member"
- Behavior: Opens user/picker selector
- Validation: Requires selecting valid user with appropriate role
- Accessibility: aria-label="Reassign investigation"

#### 3. Evidence Management Buttons

**Upload Evidence Button**
- Location: Evidence Explorer, Evidence Library
- Text: "Upload Evidence" or cloud upload icon
- Variant: Primary
- Size: Medium
- Icon: Cloud upload (☁️↓) or Paper clip (📎)
- Tooltip: "Add evidence from your device"
- Behavior: Opens file picker dialog
- Supported Types: Documents (PDF, DOC, TXT), Images (JPG, PNG), Spreadsheets (CSV, XLS), JSON/XML
- Validation: File type, size limits, virus scanning
- Accessibility: aria-label="Upload evidence"

**Drag & Drop Area**
- Location: Evidence panels
- Visual: Dashed border with "Drag files here or click to upload"
- Behavior: Accepts dropped files, shows preview on hover
- Feedback: Visual indication of valid/invalid file types
- Accessibility: Role="button", tabindex="0", aria-label="Drop files to upload evidence"

**Tag Evidence Button**
- Location: Evidence item toolbar, bulk actions
- Text: "Tag" or label icon
- Variant: Secondary
- Size: Small
- Tooltip: "Add tags or labels to evidence"
- Behavior: Opens tag selector/checklist
- Functionality: Multi-select, create new tags, suggest frequent tags
- Accessibility: aria-label="Tag evidence"

**Bookmark Evidence Button**
- Location: Evidence item header
- Icon: Bookmark (🔖) - filled when bookmarked
- Variant: Ghost
- Size: Small
- Tooltip: "Bookmark this evidence for quick access"
- Behavior: Toggles bookmark state
- Persistence: User-specific bookmarks
- Accessibility: aria-label="Bookmark evidence", aria-pressed="true/false"

**Mark as Relevant/Irrelevant Button**
- Location: Evidence item footer
- Text: "Relevant" (👍) / "Not Relevant" (👎)
- Variant: Secondary (active state changes appearance)
- Size: Small
- Tooltip: "Mark this evidence as relevant or irrelevant to the investigation"
- Behavior: Toggle between states, updates relevance score
- Analytics: Used to train/improve relevance algorithms
- Accessibility: aria-label="Mark evidence as relevant", aria-checked="true/false"

**Download Evidence Button**
- Location: Evidence item actions, evidence detail view
- Text: "Download" or download icon (💾)
- Variant: Secondary
- Size: Small
- Tooltip: "Download original evidence file"
- Behavior: Initiates file download
- Security: Scans for malware, logs access for audit
- Accessibility: aria-label="Download evidence"

**View Evidence Button**
- Location: Evidence grid/list items
- Icon: Eye (👁) or "View"
- Variant: Ghost
- Size: Small
- Tooltip: "View full evidence details"
- Behavior: Opens evidence in modal or detail view
- Features: Zoom for images, text search for documents, playback for media
- Accessibility: aria-label="View evidence details"

**Add Comment Button**
- Location: Evidence discussion thread, investigation notes
- Text: "Add Comment" or comment icon (💬)
- Variant: Secondary
- Size: Small
- Tooltip: "Add a comment or discussion"
- Behavior: Expands comment input field
- Features: Rich text, @mentions, file attachments
- Persistence: Threaded conversations with notifications
- Accessibility: aria-label="Add comment"

#### 4. Filter & Search Buttons

**Apply Filters Button**
- Location: Filter panels, search bars
- Text: "Apply" or "Filter"
- Variant: Primary
- Size: Small
- Tooltip: "Apply selected filters"
- Behavior: Executes filtering operation with current criteria
- Features: Debounce to prevent excessive requests
- Accessibility: aria-label="Apply filters"

**Clear Filters Button**
- Location: Filter panels
- Text: "Clear" or "Reset"
- Variant: Secondary/Ghost
- Size: Small
- Tooltip: "Clear all filters"
- Behavior: Resets all filter controls to default state
- Confirmation: May ask for confirmation if many filters set
- Accessibility: aria-label="Clear all filters"

**Save View Button**
- Location: Filter bar (when filters applied)
- Text: "Save View" or bookmark icon
- Variant: Secondary
- Size: Small
- Tooltip: "Save current filter configuration"
- Behavior: Opens dialog to name and save filter set
- Features: Shared/private views, default view setting
- Accessibility: aria-label="Save current view as"

**Search Button**
- Location: Search bars, header search
- Icon: Magnifying glass (🔍)
- Variant: Ghost
- Size: Medium
- Tooltip: "Search"
- Behavior: Executes search with current query
- Trigger: Also activated by Enter key in search field
- Features: Autosuggest, search history, advanced search toggle
- Accessibility: aria-label="Search"

**Clear Search Button**
- Location: Search input field (appears when text entered)
- Icon: X (×)
- Variant: Ghost
- Size: Small
- Tooltip: "Clear search"
- Behavior: Empties search field and clears results
- Appearance: Only visible when search field has content
- Accessibility: aria-label="Clear search"

#### 5. Data Management Buttons

**Create Button**
- Location: List views (empty state or toolbar)
- Text: "New [Item Type]" or "+" icon
- Variant: Primary
- Size: Medium
- Tooltip: "Create new item"
- Behavior: Opens creation form/wizard
- Examples: New User, New Report Template, New Alert Rule
- Accessibility: aria-label="Create new [item type]"

**Edit Button**
- Location: Item rows, detail views
- Text: "Edit" or pencil icon (✏️)
- Variant: Secondary
- Size: Small
- Tooltip: "Edit this item"
- Behavior: Switches to edit mode or opens edit dialog
- Features: Inline editing for simple fields, form dialog for complex
- Accessibility: aria-label="Edit [item name]"

**Delete Button**
- Location: Item rows (often in dropdown menu), detail views
- Text: "Delete" or trash icon (🗑️)
- Variant: Danger
- Size: Small
- Tooltip: "Delete this item permanently"
- Behavior: Shows confirmation dialog before deletion
- Confirmation: Requires explicit confirmation ("Type DELETE to confirm")
- Safety: May have soft delete/trash option first
- Accessibility: aria-label="Delete [item name]", role="button"

**Duplicate Button**
- Location: Item rows (actions menu), detail views
- Text: "Duplicate" or copy icon (📋)
- Variant: Secondary
- Size: Small
- Tooltip: "Create a copy of this item"
- Behavior: Opens creation form with current values pre-filled
- Exceptions: Certain immutable fields may be cleared (ID, timestamps)
- Accessibility: aria-label="Duplicate [item name]"

**Archive Button**
- Location: Item rows, bulk actions, detail views
- Text: "Archive" or archive icon (📦)
- Variant: Secondary
- Size: Small
- Tooltip: "Move item to archive"
- Behavior: Changes status to archived, removes from active views
- Retrieval: Accessible via archive filters/search
- Accessibility: aria-label="Archive [item name]"

**Restore Button**
- Location: Archive/views, item details when archived
- Text: "Restore" or undo icon (↩️)
- Variant: Secondary
- Size: Small
- Tooltip: "Restore item from archive"
- Behavior: Moves item back to active state
- Availability: Only shown for archived items
- Accessibility: aria-label="Restore [item name]"

**Publish Button**
- Location: Content/template creation, report generation
- Text: "Publish" or rocket icon (🚀)
- Variant: Primary
- Size: Medium
- Tooltip: "Make this item available for use"
- Behavior: Changes status from draft to published
- Effects: May trigger notifications, make available in selections
- Accessibility: aria-label="Publish [item name]"

**Unpublish Button**
- Location: Published items, management views
- Text: "Unpublish" or blocked icon (🚫)
- Variant: Secondary
- Size: Medium
- Tooltip: "Remove this item from general availability"
- Behavior: Changes status from published to draft or archived
- Considerations: May affect existing usages
- Accessibility: aria-label="Unpublish [item name]"

#### 6. Form & Input Buttons

**Save Button**
- Location: Form footers, edit dialogs, settings pages
- Text: "Save" or checkmark icon (✅)
- Variant: Primary
- Size: Medium
- Tooltip: "Save changes"
- Behavior: Persists form data to backend
- Validation: Runs client-side validation before submission
- Feedback: Success/toast message or inline validation errors
- Shortcut: Ctrl+Enter (Cmd+Enter on Mac)
- Accessibility: aria-label="Save changes"

**Cancel Button**
- Location: Form footers, edit dialogs, alongside Save
- Text: "Cancel" or close icon (✕)
- Variant: Secondary/Ghost
- Size: Medium
- Tooltip: "Cancel and discard changes"
- Behavior: Returns to previous state without saving
- Confirmation: May show warning if unsaved changes exist
- Shortcut: Escape key
- Accessibility: aria-label="Cancel"

**Reset Button**
- Location: Forms with mutable values
- Text: "Reset" or circular arrow (🔄)
- Variant: Secondary
- Size: Small
- Tooltip: "Reset form to initial values"
- Behavior: Restores form to original loaded state
- Difference from Cancel: Keeps user in edit mode
- Accessibility: aria-label="Reset form"

**Submit Button**
- Location: Final step in wizards, modal dialogs requiring action
- Text: Action-specific ("Request Review", "Send Alert", "Run Report")
- Variant: Primary
- Size: Medium/Large
- Tooltip: Varies by action
- Behavior: Performs primary action and closes dialog
- Validation: May require all fields valid before enabling
- Loading State: Shows progress indicator during submission
- Accessibility: aria-label="Submit [action]"

**Run Button**
- Location: Reports, analytics, simulation tools
- Text: "Run" or play icon (▶️)
- Variant: Primary
- Size: Medium
- Tooltip: "Execute this operation"
- Behavior: Starts the configured process (report generation, query execution)
- Feedback: Progress indicator, results display upon completion
- Cancellation: May provide stop button during long operations
- Accessibility: aria-label="Run [operation name]"

**Schedule Button**
- Location: Report/configuration tools
- Text: "Schedule" or calendar icon (📅)
- Variant: Secondary
- Size: Medium
- Tooltip: "Set up recurring execution"
- Behavior: Opens scheduling dialog (frequency, time, recipients)
- Output: Creates scheduled job/task entry
- Management: Visible in scheduled jobs view
- Accessibility: aria-label="Schedule [operation name]"

**Test Button**
- Location: Integration settings, API configuration, notification setup
- Text: "Test" or flask icon (🧪)
- Variant: Secondary
- Size: Small
- Tooltip: "Test this configuration"
- Behavior: Performs validation check without saving
- Feedback: Success/error message with details
- Safety: Does not persist changes or trigger actual events
- Accessibility: aria-label="Test [configuration name]"

#### 7. Modal & Dialog Buttons

**OK Button**
- Location: Simple confirmation dialogs, alerts
- Text: "OK" or checkmark
- Variant: Primary
- Size: Small
- Tooltip: "Confirm and proceed"
- Behavior: Closes dialog and accepts action
- Default: Often default action (activated by Enter)
- Accessibility: aria-label="OK"

**Cancel Button**
- Location: Dialogs alongside OK or primary action
- Text: "Cancel"
- Variant: Secondary
- Size: Small
- Tooltip: "Cancel and close dialog"
- Behavior: Closes dialog without action
- Escape: Often bound to Escape key
- Accessibility: aria-label="Cancel"

**Yes/No Buttons**
- Location: Confirmation dialogs
- Text: "Yes" / "No" or "Accept" / "Decline"
- Variants: Yes=Primary, No=Secondary
- Size: Small
- Tooltips: Context-specific
- Behavior: Resolve the posed question
- Accessibility: aria-label="Yes" / aria-label="No"

**Save & Close Button**
- Location: Edit forms where saving and exiting is common
- Text: "Save & Close" or checkmark + arrow
- Variant: Primary
- Size: Medium
- Tooltip: "Save changes and close"
- Behavior: Saves data then closes the dialog/tab
- Efficiency: Combines two common operations
- Accessibility: aria-label="Save and close"

**Apply Button**
- Location: Settings panels, preference dialogs
- Text: "Apply"
- Variant: Primary
- Size: Medium
- Tooltip: "Apply changes without closing"
- Behavior: Saves settings but keeps dialog open for further adjustments
- Contrast: Unlike Save which might close, Apply keeps context
- Accessibility: aria-label="Apply settings"

#### 8. Status & Toggle Buttons

**Toggle Switch** (Visualized as Button)
- Location: Settings, preferences, feature flags
- Appearance: Slider or pill shape with on/off states
- States: On (active/enabled) or Off (disabled/inactive)
- Feedback: Immediate visual change, optional animation
- Accessibility: role="switch", aria-checked="true/false", aria-label descriptive

**Status Indicator Button**
- Location: Dashboard widgets, list views
- Appearance: Colored circle or badge with text
- Variants: 
  - Success: Green (●) Online, Active, Healthy
  - Warning: Yellow (●) Degraded, Pending, Attention Needed
  - Error: Red (●) Offline, Failed, Critical
  - Info: Blue (●) Informational, In Progress
  - Neutral: Gray (●) Unknown, Disabled, Not Applicable
- Tooltip: Detailed status information on hover
- Click Behavior: May drill down to details or log view
- Accessibility: aria-label="[Status description]", role="status"

**Bulk Select Toggle**
- Location: Table headers, list views
- Text: Checkbox in header or "Select All"
- Variant: Ghost/Special (checkbox styling)
- Size: Small
- Tooltip: "Select all visible items"
- Behavior: Toggles selection state of all items in current view
- Variants: Select All / Deselect All, Select All in Results
- Indeterminate State: Shows when some but not all items selected
- Accessibility: aria-label="Select all items", aria-checked="true/false/mixed"

#### 9. Help & Guidance Buttons

**Help/Tooltip Button**
- Location: Form labels, complex controls, header
- Icon: Question mark (?) or info (i)
- Variant: Ghost
- Size: Small
- Tooltip: "Show help" (becomes "Hide help" when active)
- Behavior: Toggles display of contextual help text
- Content: May include links to documentation, examples, videos
- Persistence: May remember user preference for always showing hints
- Accessibility: aria-label="Show help", aria-expanded="true/false"

**Tour Button**
- Location: Onboarding screens, feature announcements
- Text: "Take Tour" or play circle (⏵)
- Variant: Secondary
- Size: Medium
- Tooltip: "Walkthrough of this feature"
- Behavior: Initiates guided product tour
- Features: Step-by-step highlighting, progress indicators, skip option
- Completion: May offer reward/badge or set seen flag
- Accessibility: aria-label="Start guided tour"

**Feedback Button**
- Location: Footer, sidebar, user menu
- Text: "Feedback" or chat/message icon (💬)
- Variant: Secondary
- Size: Small/Medium
- Tooltip: "Send feedback or report issue"
- Behavior: Opens feedback form or support channel
- Options: Bug report, feature request, general praise, contact support
- Tracking: Includes context (page, user agent, version) automatically
- Anonymity: Option to submit anonymously or with contact info
- Accessibility: aria-label="Send feedback"

**Video Tutorial Button**
- Location: Documentation pages, complex feature introductions
- Icon: Play button in circle (▶️ in ○)
- Variant: Secondary
- Size: Small
- Tooltip: "Watch video tutorial"
- Behavior: Plays embedded or linked video
- Features: Captions, speed control, picture-in-picture option
- Tracking: View completion analytics for content improvement
- Accessibility: aria-label="Watch video tutorial", role="button"

#### 10. System & Admin Buttons

**Refresh Button**
- Location: Dashboard widgets, data views, toolbar
- Icon: Circular arrow (🔄) or refresh
- Variant: Ghost
- Size: Small
- Tooltip: "Refresh data"
- Behavior: Reloads data from source
- Indicator: May show spinning refresh during operation
- Prevention: Debounce to prevent excessive refreshing
- Shortcut: F5 or Ctrl+R (Cmd+R on Mac)
- Accessibility: aria-label="Refresh data"

**Settings Button**
- Location: User menu, header, sidebar
- Icon: Gear (⚙️)
- Variant: Ghost
- Size: Small/Medium
- Tooltip: "Settings" or "Account Settings"
- Behavior: Navigates to settings page or opens settings dialog
- Destinations: Personal settings, organization settings, system settings (admin)
- Accessibility: aria-label="User settings"

**User Menu Button**
- Location: Header top-right
- Content: User avatar/initials + downward caret
- Variant: Ghost
- Size: Medium
- Tooltip: "User menu" or shows username on hover
- Behavior: Opens dropdown with profile, settings, help, logout
- Items: My Profile, Settings, Help, Sign Out
- Accessibility: aria-label="Account menu for [username", role="menu"

**Logout Button**
- Location: User menu, sometimes sidebar bottom
- Text: "Sign Out" or "Log Out" with power icon (⏻)
- Variant: Danger/Text (often standalone)
- Size: Small
- Tooltip: "Sign out of your account"
- Behavior: Ends session, clears tokens, redirects to login
- Confirmation: May show confirmation for shared/public computers
- Cleanup: Removes local storage, clears caches where appropriate
- Feedback: May show "You've been logged out" message
- Accessibility: aria-label="Sign out"

**Help/Support Button**
- Location: Footer, header (right of user menu)
- Text: "Help" or life preserver / headset icon
- Variant: Secondary
- Size: Small/Medium
- Tooltip: "Get help and support"
- Behavior: Opens help center or support dropdown
- Options: Documentation, Contact Support, Community Forums, Live Chat
- Availability: May vary by user role/time of day
- Accessibility: aria-label="Help and support"

**Notification Bell Button**
- Location: Header top-right (left of user menu)
- Icon: Bell (🔔) with badge for count
- Variants: 
  - Default: Outline bell
  - Active: Solid bell when unread notifications
  - Muted: Bell with slash through it
- Badge: Shows count of unread notifications (may show "99+" for large numbers)
- Tooltip: "Notifications" + count = "You have X unread notifications"
- Behavior: Opens notification panel/dropdown
- Features: Mark all as read, gear icon for settings, see all link
- Auto-hide: May hide after timeout or when user navigates elsewhere
- Accessibility: aria-label="Notifications, you have [count] unread", role="button"

#### 11. Specialized Investigation Buttons

**Hypothesis Button**
- Location: Investigation detail, reasoning graph nodes
- Text: "Add Hypothesis" or light bulb icon (💡)
- Variant: Secondary
- Size: Small
- Tooltip: "Add investigative hypothesis"
- Behavior: Opens hypothesis formulation dialog
- Fields: Statement, confidence, evidence supporting/refuting
- Integration: Appears in reasoning graph as special node type
- Collaboration: Can be shared/discussed with team members
- Accessibility: aria-label="Add investigation hypothesis"

**Request Information Button**
- Location: Evidence items, investigation timeline
- Text: "Request Info" or envelope with plus (📨➕)
- Variant: Secondary
- Size: Small
- Tooltip: "Request additional information from source"
- Behavior: Opens request form (subpoena, data request, etc.)
- Tracking: Creates audit trail of requests and responses
- Templates: May use predefined request types/formats
- Notification: Alerts when response received
- Accessibility: aria-label="Request information from source"

**Link Evidence Button**
- Location: Evidence items, timeline events
- Text: "Link" or chain icon (🔗)
- Variant: Secondary
- Size: Small
- Tooltip: "Link this evidence to another item"
- Behavior: Opens search/picker to select target item to link to
- Types: Evidence-to-evidence, evidence-timeline-event, investigation-investigation
- Properties: Relationship type, description, confidence
- Navigation: Clicking link shows related item
- Accessibility: aria-label="Link evidence to another item"

**Compare Button**
- Location: Multi-select toolbar, evidence comparison view
- Text: "Compare" or vs icon (vs)
- Variant: Secondary
- Size: Small
- Tooltip: "Compare selected items"
- Behavior: Enters comparison mode showing differences/similarities
- Features: Side-by-side view, diff algorithms, highlighting changes
- Applications: Document versions, transaction sets, entity profiles
- Exit: Clear selection or click "Cancel Compare"
- Accessibility: aria-label="Compare selected items"

**Anonymize Button**
- Location: Evidence containing PII, export dialogs
- Text: "Anonymize" or mask icon (🎭)
- Variant: Warning
- Size: Small
- Tooltip: "Remove personally identifiable information"
- Behavior: Applies redaction/masking techniques
- Techniques: Blackout, blurring, tokenization, synthetic data generation
- Levels: Full anonymization, pseudonymization, selective field masking
- Audit: Logs what was anonymized and how
- Accessibility: aria-label="Anonymize sensitive data"

**Validate Button**
- Location: Data entry forms, import dialogs, rule editors
- Text: "Validate" or checkmark with magnifying glass (✅🔍)
- Variant: Secondary
- Size: Small
- Tooltip: "Check for errors or issues"
- Behavior: Runs validation rules against current data
- Feedback: Inline warnings/errors, summary panel
- Types: Schema validation, business rule validation, consistency checks
- Prevention: May disable submit until validation passes
- Accessibility: aria-label="Validate data"

#### Button Implementation Guidelines

**Consistency Rules:**
1. Same action → Same appearance everywhere (consistency principle)
2. Similar actions → Similar appearance (analogical consistency)
3. Primary action per screen → One primary button maximum
4. Dangerous actions → Clearly differentiated (color, confirmation)
5. Frequently used actions → Accessible via keyboard shortcuts
6. Icons → Always paired with text for accessibility (except universally understood)
7. Loading states → Never change button size/shift layout during transition
8. Disabled state → Always provide explanatory tooltip on hover

**Accessibility Requirements:**
- Minimum 44x44dp touch target size
- Sufficient color contrast (WCAG AA minimum)
- Keyboard navigable and operable
- ARIA labels describing action and state
- Focus management for modal dialogs
- Screen reader announcements for dynamic changes
- Skip navigation for keyboard users

**Performance Considerations:**
- Lazy load icon sets (use SVG sprites or font icons)
- Debounce rapid click actions
- Smooth transitions/animations (respect reduced motion preferences)
- Virtualize large button groups (token bars, filter chips)
- Consider hover card delays to prevent accidental triggers

**Internationalization (i18n):**
- Text externalization for all labels/tooltips
- Right-to-left (RTL) layout support
- Format-aware strings (plurals, gender, date/time)
- Icon mirroring where appropriate (arrows, progress indicators)
- Text expansion accommodation (up to 30% longer in some languages)

**Testing Checklist:**
- Visual regression testing across breakpoints
- Keyboard-only navigation testing
- Screen reader testing (JAWS, NVDA, VoiceOver)
- Color blindness simulation (Deuteranopia, Protanopia, Tritanopia)
- Touch target size verification
- Animation performance testing
- Error state and recovery testing
- Long text handling (especially in buttons with icons)
- Rapid click/spam testing for race conditions

This comprehensive button specification ensures that every interactive element in the FFIRE system is intentional, accessible, and contributes to an efficient investigation workflow while maintaining safety and clarity for high-stakes fraud analysis work.