# ResearchReel Complete Page States

## Overview
Page states define the various UI conditions a page can be in based on data availability, user permissions, system status, and interaction context. Proper state handling ensures users always receive appropriate feedback and guidance regardless of circumstances.

## State Classification System
ResearchReel categorizes page states into:

1. **Data States**: Based on content availability
2. **Permission States**: Based on user access rights
3. **System States**: Based on application health and connectivity
4. **Interaction States**: Based on user actions and workflow progress
5. **Device States**: Based on screen size and input capabilities

Each state specifies:
- **Trigger Conditions**: When this state should be displayed
- **UI Composition**: What components are shown/hidden
- **Messaging**: Primary, secondary, and instructional text
- **Actions**: Available user actions in this state
- **Transitions**: How to exit this state
- **Accessibility**: Special considerations for assistive technologies

## 1. Data States

### Empty State
**Trigger**: No data matches current filters/query
**Applies To**: Dashboards, lists, libraries, search results, analytics views

#### Empty State Variations
- **First Time User**: 
  - **Trigger**: User has never created content of this type
  - **UI**: 
    - Large illustration or animation
    - Primary heading: "Welcome to [Feature Name]"
    - Subheading: Guidance on getting started
    - Primary CTA: Main action button (e.g., "New Project", "Upload Media")
    - Secondary CTA: Learning resources (tutorials, templates)
  - **Messaging**: 
    - Primary: "No [items] yet"
    - Secondary: "Start by creating your first [item]"
    - Instructional: Bulleted list of benefits or next steps
  - **Actions**: 
    - Primary action button
    - Tutorial/video links
    - Template gallery link
  - **Transitions**: 
    - Primary action → creation flow
    - Secondary action → learning resources
  - **Accessibility**: 
    - Heading level appropriate to context
    - Illustrations have decorative/empty alt or descriptive labels
    - Clear focus order

- **Filtered Results Empty**:
  - **Trigger**: Active filters yield no results
  - **UI**:
    - Smaller illustration or icon
    - Heading: "No [items] match your search results"
    - Subheading: Shows current filters applied
    - Action: Button to clear filters or adjust search
  - **Messaging**:
    - Primary: "No [items] found"
    - Secondary: "Try adjusting your filters or search terms"
    - Instructional: List of current active filters with remove options
  - **Actions**:
    - Clear all filters
    - Individual filter removal
    - Edit search query
  - **Transitions**:
    - Clear filters → show all results
    - Modify filters → re-execute search
  - **Accessibility**:
    - Live region announces when results change
    - Filter tags are accessible removable chips
    - Clear announcement of result count (zero)

- **Error-Induced Empty**:
  - **Trigger**: Data failed to load due to error
  - **UI**:
    - Error illustration/icon
    - Heading: "Unable to load [items]"
    - Subheading: Brief error explanation
    - Primary action: Retry button
    - Secondary action: Help/link to status page
  - **Messaging**:
    - Primary: "We couldn't load your [items]"
    - Secondary: Specific error message or "Please try again"
    - Instructional: Common troubleshooting tips
  - **Actions**:
    - Retry button
    - Link to help documentation
    - Link to system status (if applicable)
  - **Transitions**:
    - Retry → re-attempt data load
    - Help → documentation or support
  - **Accessibility**:
    - Error announced via aria-live="assertive"
    - Retry button has clear label
    - Focus moves to error container or retry button

### Loading State
**Trigger**: Data is being fetched or processed
**Applies To**: Any page awaiting data

#### Loading State Variations
- **Initial Load**:
  - **Trigger**: First data fetch after navigation
  - **UI**:
    - Skeleton screens matching expected layout
    - May include brand colored progress indicator
    - Page title and navigation remain visible
  - **Messaging**: None (skeleton implies loading)
  - **Actions**: None (interactive elements may be disabled)
  - **Transitions**: 
    - Data received → replace skeleton with actual content
    - Error → error state
  - **Accessibility**:
    - aria-busy="true" on loading regions
    - Live region announces when loading completes
    - Skeletons have appropriate landmark roles

- **Partial Load**:
  - **Trigger**: Some data loaded, waiting for remainder
  - **UI**:
    - Mixed actual content and skeletons
    - May show placeholder for specific sections
    - Visible indication of what's loaded vs pending
  - **Messaging**: 
    - Optional: "Loading additional data..." in non-intrusive location
  - **Actions**:
    - Available actions on loaded data
    - May disable actions requiring pending data
  - **Transitions**:
    - All data received → normal state
    - Error in partial data → mixed state with error indicators
  - **Accessibility**:
    - Live regions update as sections load
    - Focus management maintains context

- **Refresh/Reload**:
  - **Trigger**: User-initiated data refresh
  - **UI**:
    - Content remains visible
    - Loading indicator in relevant toolbar/button
    - May show "Last updated: [time]" that updates to "Updating..."
  - **Messaging**:
    - Optional toast: "Refreshing..."
    - Status indicator in toolbar
  - **Actions**:
    - Other actions may remain available
    - Refresh action typically disabled during operation
  - **Transitions**:
    - Refresh complete → update content, restore normal state
    - Error → show error with content still visible (stale data warning)
  - **Accessibility**:
    - Live region announces refresh start/completion
    - Focus remains where it was (unless context invalidated)

### Error State
**Trigger**: Data fetch or processing failed
**Applies To**: Any page relying on external data

#### Error State Variations
- **Network Error**:
  - **Trigger**: Failed to connect to server
  - **UI**:
    - Offline/error illustration
    - Heading: "Unable to connect"
    - Subheading: "Check your internet connection"
    - Primary action: Retry button
    - Secondary action: Diagnostic help
  - **Messaging**:
    - Primary: "We're having trouble connecting"
    - Secondary: "Please check your internet connection and try again"
    - Instructional: Common network troubleshooting steps
  - **Actions**:
    - Retry button
    - Network diagnostics link
    - Link to offline queue if applicable
  - **Transitions**:
    - Retry → re-attempt connection
    - Network restored → automatic retry or user-triggered refresh
  - **Accessibility**:
    - aria-live="assertive" announces connection loss
    - Focus moves to error message or retry button
    - Clear explanation of impact

- **Service Error**:
  - **Trigger**: Server returned error (5xx, 4xx not auth)
  - **UI**:
    - Service disruption illustration
    - Heading: "Something went wrong"
    - Subheading: Error code and brief explanation
    - Primary action: Retry button
    - Secondary action: Report problem / status page
  - **Messaging**:
    - Primary: "Our servers encountered an issue"
    - Secondary: Specific error message or reference ID
    - Instructional: Expected resolution time if known
  - **Actions**:
    - Retry button
    - Link to status page
    - Report problem feedback
  - **Transitions**:
    - Retry → re-attempt request
    - Service recovered → automatic recovery or user refresh
  - **Accessibility**:
    - Error announced immediately
    - Focus management to error container
    - Reference ID announced for support

- **Authentication Error**:
  - **Trigger**: Session expired or invalid credentials
  - **UI**:
    - Security/Icons illustration
    - Heading: "Session expired"
    - Subheading: "Please sign in again to continue"
    - Primary action: Sign in button
    - Secondary action: Help link
  - **Messaging**:
    - Primary: "You've been signed out"
    - Secondary: "For security, your session has expired"
    - Instructional: Benefits of staying signed in (if applicable)
  - **Actions**:
    - Sign in button (returns to original destination after)
    - Link to help documentation
  - **Transitions**:
    - Successful sign in → redirect to intended page
    - Sign up/new account → appropriate flow
  - **Accessibility**:
    - Focus moves to sign in form
    - Clear announcement of session expiry
    - Password managers can autofill

- **Permission Error**:
  - **Trigger**: User lacks required permissions
  - **UI**:
    - Permission/lock illustration
    - Heading: "Access restricted"
    - Subheading: Explanation of what's missing
    - Primary action: Request access (if applicable)
    - Secondary action: Contact admin / switch account
  - **Messaging**:
    - Primary: "You don't have permission to view this"
    - Secondary: Specific explanation (role, license, etc.)
    - Instructional: How to gain access
  - **Actions**:
    - Request access button
    - Contact administrator
    - Switch account/workspace
    - Upgrade license (if applicable)
  - **Transitions**:
    - Access granted → return to original page
    - Action completed → refresh or redirect appropriately
  - **Accessibility**:
    - Clear explanation of what permission is needed
    - Focus moves to primary action
    - Announces restriction and available remedies

### Partial Data State
**Trigger**: Some data available but incomplete or degraded
**Applies To**: Dashboards showing widgets, profile pages, analytics

#### Variations
- **Degraded Mode**:
  - **Trigger**: Non-critical services unavailable
  - **UI**:
    - Main content visible
    - Specific widgets/sections show degraded state indicators
    - May show warning banner at top
  - **Messaging**:
    - Banner: "Some features may be unavailable"
    - Widget: "Data temporarily unavailable" with refresh option
  - **Actions**:
    - Refresh individual components
    - Link to status page for details
    - Available actions on functional components
  - **Transitions**:
    - Service restored → automatic recovery or manual refresh
    - User action → retry specific component
  - **Accessibility**:
    - Live regions announce when degraded services recover
    - Clear indication of what's affected

- **Stale Data Warning**:
  - **Trigger**: Data is usable but outdated
  - **UI**:
    - Content visible
    - Subtle indicator: "Last updated [time] ago"
    - May show refresh suggestion
  - **Messaging**:
    - Informative: "Data may be outdated"
    - Action-oriented: "Refresh for latest information"
  - **Actions**:
    - Manual refresh button
    - Auto-refresh toggle (if available)
  - **Transitions**:
    - Refresh → update timestamp, remove warning if fresh
    - Time threshold exceeded → may upgrade to full error state
  - **Accessibility**:
    - Timestamp announced as part of widget
    - Clear indication of staleness level

## 2. Permission States

### Full Access State
**Trigger**: User has all required permissions for current context
**Applies To**: All pages when permissions sufficient
**UI**: 
- All features and controls visible and enabled
- No permission-related restrictions or warnings
**Messaging**: None (normal operation)
**Actions**: All available actions per role and context
**Transitions**: Permission change → appropriate restricted state
**Accessibility**: Standard accessibility assumptions apply

### Limited Access State
**Trigger**: User has some but not all permissions
**Applies To**: Pages with feature tiers or modular permissions

#### Variations
- **Feature Gate**:
  - **Trigger**: Specific feature unavailable due to plan/role
  - **UI**:
    - Feature area visible but disabled
    - Lock icon or overlay on disabled components
    - Tooltip or badge indicating premium badge/icon indicating required plan/role
  - **Messaging**:
    - Inline: "Available in [Plan/Role] plan"
    - Tooltip: Detailed explanation of what's missing
    - CTA: "Upgrade to access" or "Request access"
  - **Actions**:
    - Upgrade/license change flow
    - Request access from admin
    - Learn more about feature
  - **Transitions**:
    - Permission granted → feature enabled
    - Plan changed → re-evaluate all feature gates
  - **Accessibility**:
    - Screen readers announce feature restriction
    - Clear path to request or upgrade
    - Upgrade path announced appropriately

- **Read-Only Mode**:
  - **Trigger**: User can view but not modify
  - **UI**:
    - All content visible
    - Edit controls hidden or disabled
    - May show banner: "View only mode"
    - Action buttons replaced with view-only alternatives
  - **Messaging**:
    - Banner: "You're viewing in read-only mode"
    - Tooltips on disabled actions: "Editing requires [role/permission]"
  - **Actions**:
    - View-only actions (comment, share, export if permitted)
    - Request edit access
    - Contact administrator for permission change
  - **Transitions**:
    - Edit access granted → enable controls
    - Session/context change → re-evaluate permissions
  - **Accessibility**:
    - Clearly announced as read-only on page load
    - Focus skips over disabled edit controls
    - Alternative actions announced

### No Access State
**Trigger**: User lacks minimum required permissions
**Applies To**: Entire pages or sections

#### Variations
- **Login Required**:
  - **Trigger**: Anonymous user accessing protected route
  - **UI**:
    - Centered or modal login prompt
    - May show blurred background of target page
    - Branding and value proposition reminder
  - **Messaging**:
    - Primary: "Please sign in to continue"
    - Secondary: Brief explanation of what they're trying to access
    - May show social login options
  - **Actions**:
    - Email/password sign in
    - Social login options
    - Sign up for new account
    - Help/forgot password links
  - **Transitions**:
    - Successful authentication → redirect to intended page
    - Sign up → complete registration flow
  - **Accessibility**:
    - Focus moves to username/email field
    - Clear announcement of authentication requirement
    - Error messages associated with fields

- **Insufficient Permissions**:
  - **Trigger**: Logged in user lacks required role/permission
  - **UI**:
    - Access denied page or modal
    - May show current role and required role
    - Explanation of what the permission enables
  - **Messaging**:
    - Primary: "Access denied"
    - Secondary: "You need [permission/role] to access this"
    - Instructional: How to obtain required permissions
  - **Actions**:
    - Request access from administrator
    - Contact support
    - Switch to different account/workspace
    - Return to previous page
  - **Transitions**:
    - Permission granted → redirect to intended page
    - Action completed → appropriate feedback
  - **Accessibility**:
    - Clear announcement of access denial
    - Focus moves to primary action (request access)
    - Announces current status and required status

### Permission Request State
**Trigger**: User has requested permission and awaiting response
**Applies To**: Any page where user initiated permission request

#### Variations
- **Access Request Pending**:
  - **Trigger**: User requested access, waiting for approval
  - **UI**:
    - Informative banner or badge
    - Shows request details and timestamp
    - Option to cancel request or check status
  - **Messaging**:
    - Informative: "Access request submitted"
    - Detail: "Requested [permission] for [resource]"
    - Optional: "Approvers typically respond within [timeframe]"
  - **Actions**:
    - Check request status
    - Cancel request
    - Contact administrator for expedited review
  - **Transitions**:
    - Approved → redirect to resource or refresh access
    - Denied → show denial reason and alternatives
    - Cancelled → return to previous state
  - **Accessibility**:
    - Live region announces status changes
    - Clear announcement of request state
    - Announces when decision is made

## 3. System States

### Online State
**Trigger**: Normal connectivity to all required services
**Applies To**: All pages under normal operation
**UI**: 
- All features functioning normally
- No connectivity indicators or warnings
**Messaging**: None
**Actions**: All available actions
**Transitions**: 
- Connectivity loss → offline or degraded state
- Service disruption → specific service error state
**Accessibility**: Standard assumptions

### Offline State
**Trigger**: Lost connection to primary services
**Applies To**: Any page requiring server communication

#### Variations
- **Complete Offline**:
  - **Trigger**: No network connectivity
  - **UI**:
    - Offline illustration/banner
    - May show last successful sync time
    - Core functionality may remain if cached
  - **Messaging**:
    - Primary: "You're offline"
    - Secondary: "Some features may be unavailable"
    - Instructional: "Changes will sync when you're back online"
  - **Actions**:
    - Limited to offline-capable features
    - Queue actions for later sync
    - Diagnostic help
  - **Transitions**:
    - Connection restored → sync queue, resume normal operation
    - Manual retry → re-attempt connection
  - **Accessibility**:
    - aria-live="polite" announces connection loss/restoration
    - Focus management appropriate to context
    - Clear indication of what works offline

- **Intermittent Connectivity**:
  - **Trigger**: Unstable or slow connection
  - **UI**:
    - Content visible with quality indicators
    - May show "connecting..." or "retrying..." in relevant areas
    - Reduced fidelity modes may activate
  - **Messaging**:
    - Informative: "Experiencing connectivity issues"
    - Action-oriented: "Switch to lower quality mode" if applicable
  - **Actions**:
    - Retry failed operations
    - Reduce data usage mode
    - Report persistent issues
  - **Transitions**:
    - Stable connection → resume normal quality
    - User action → adjust settings or retry
  - **Accessibility**:
    - Live regions announce significant connectivity changes
    - Clear indication of current connection quality

### Maintenance State
**Trigger**: System undergoing scheduled maintenance
**Applies To**: All pages during maintenance windows

#### Variations
- **Scheduled Maintenance**:
  - **Trigger**: Known maintenance window active
  - **UI**:
    - Maintenance illustration or banner
    - Shows scheduled start/end times
    - May show progress indicator for ongoing tasks
  - **Messaging**:
    - Primary: "Scheduled maintenance in progress"
    - Secondary: "Service expected to resume at [time]"
    - Instructional: Link to status page for details
  - **Actions**:
    - View status page
    - Set reminder for when service returns
    - Access limited read-only features if available
  - **Transitions**:
    - Maintenance complete → automatic recovery to normal state
    - Early completion → immediate resumption
  - **Accessibility**:
    - Live region announces maintenance start/end
    - Clear announcement of expected duration
    - Focus management appropriate to announcements

- **Emergency Maintenance**:
  - **Trigger**: Unplanned service disruption
  - **UI**:
    - Urgent maintenance/banner
    - May show estimated time to resolution
    - Service status indicator
  - **Messaging**:
    - Primary: "We're experiencing technical difficulties"
    - Secondary: "Our team is working to restore service"
    - Instructional: "Check status page for updates"
  - **Actions**:
    - View status page
    - Subscribe to incident updates
    - Report impact if applicable
  - **Transitions**:
    - Service restored → automatic recovery
    - Degraded mode → limited functionality if available
  - **Accessibility**:
    - Immediate announcement of issue
    - Regular updates on status
    - Clear communication of impact and ETA

### Degraded State
**Trigger**: Some non-critical services unavailable
**Applies To**: Pages where core functionality remains

#### Variations
- **Feature Unavailable**:
  - **Trigger**: Specific backend service degraded or down
  - **UI**:
    - Core functionality visible
    - Affected features show disabled state with explanation
    - May show system status indicator in header/footer
  - **Messaging**:
    - Informative: "[Feature] temporarily unavailable"
    - Action-oriented: "Try again later" or "Use alternative"
    - May show known issue reference
  - **Actions**:
    - Retry specific feature
    - Use alternative workflow if available
    - Report problem
    - View status page
  - **Transitions**:
    - Service restored → feature re-enabled
    - User action → retry or alternative
  - **Accessibility**:
    - Live regions announce when degraded features recover
    - Clear indication of what's affected
    - Alternative paths announced

- **Reduced Performance**:
  - **Trigger**: Services operating with higher latency or reduced capacity
  - **UI**:
    - All features visible
    - Performance indicators where relevant (spinners, progress)
    - May show banner: "Experiencing higher than normal load"
  - **Messaging**:
    - Informative: "Service may be slower than usual"
    - Instructional: "Consider performing intensive tasks during off-peak hours"
  - **Actions**:
    - All actions available but may be slower
    - Schedule intensive tasks for later
    - Report persistent performance issues
  - **Transitions**:
    - Performance restored → return to normal indicators
    - User action → adjust timing or report issues
  - **Accessibility**:
    - Performance indicators properly labeled
    - Clear indication of degraded state
    - Alternatives suggested accommodations for time-sensitive tasks

## 4. Interaction States

### Pristine State
**Trigger**: Page loaded, no user interaction yet
**Applies To**: Forms, editors, configuration panels
**UI**: 
- Default values shown
- Placeholders in empty fields
- No validation indicators
- Clean, untouched appearance
**Messaging**: 
- Field-specific placeholders or helper text
- May show guided tour invitation for complex interfaces
**Actions**: 
- All available interactions enabled
- Focus typically on first meaningful input
**Transitions**: 
- User interaction → dirty or modified state
- External change → may remain pristine or update accordingly
**Accessibility**: 
- Placeholders properly associated with inputs
- Clear indication of editable regions
- Screen reader announces initial state

### Dirty State
**Trigger**: User has modified form/data but not saved
**Applies To**: Forms, settings, project properties, metadata editors

#### Variations
- **Locally Modified**:
  - **Trigger**: User changed values, unsaved
  - **UI**:
    - Modified fields highlighted (subtle background/border)
    - May show undo/redo controls
    - Save button enabled
    - Navigation may show warning about unsaved changes
  - **Messaging**:
    - Informative: "You have unsaved changes"
    - Action-oriented: "Save changes" or "Discard changes"
    - Field-level: Indicates what's been changed
  - **Actions**:
    - Save changes
    - Discard changes (reset to original)
    - Undo/redo individual changes
    - Navigate away (with unsaved changes warning)
  - **Transitions**:
    - Save → clean state with success feedback
    - Discard → pristine state
    - Navigation away → either discard or show confirmation
  - **Accessibility**:
    - Live region announces when save completes
    - Clear indication of modified fields
    - Undo/redo history accessible

- **Validation Error**:
  - **Trigger**: User input fails validation rules
  - **UI**:
    - Affected fields highlighted with error color
    - Error message displayed below or in tooltip
    - Save/submit button typically disabled
    - May show inline suggestion for correction
  - **Messaging**:
    - Primary: "Please fix the following issues"
    - Field-specific: Clear explanation of what's wrong
    - Instructional: How to correct the issue
  - **Actions**:
    - Correct the invalid input
    - May show example of valid format
    - Reset to last valid state (if applicable)
  - **Transitions**:
    - Valid input → error state cleared, save enabled
    - User correction → re-validation
  - **Accessibility**:
    - Error messages announced via aria-live="assertive"
    - Errors associated with fields via aria-describedby
    - Focus management to first error on submit attempt

### Modified State
**Trigger**: Changes saved but user may want to revert
**Applies To**: Any entity with version history or undo capability

#### Variations
- **Recently Saved**:
  - **Trigger**: Changes just saved successfully
  - **UI**:
    - Brief success indicator (toast, banner, button state change)
    - May show "Saved" timestamp
    - Controls return to default enabled state
  - **Messaging**:
    - Informative: "Changes saved successfully"
    - Optional: "Last saved [time] ago"
    - May show what was saved (summary)
  - **Actions**:
    - Continue editing
    - View history/changelog
    - Navigate away
  - **Transitions**:
    - Additional edits → dirty state
    - Time passes → saved state indication ages
  - **Accessibility**:
    - Success announcement via aria-live="polite"
    - Clear indication of save status
    - Timestamp announced if present

- **Has Unsaved Changes** (vs saved baseline):
  - **Trigger**: Current state differs from last saved version
  - **UI**:
    - Document/header shows modified indicator (dot, asterisk)
    - Title may show "[unsaved]" suffix
    - Save button enabled
    - Close/navigate may prompt about unsaved changes
  - **Messaging**:
    - Informative: "You have unsaved changes"
    - Contextual: Describes what type of changes
    - May show list of modified components
  - **Actions**:
    - Save changes
    - View diff/changelog
    - Revert to last saved
    - Navigate away (with confirmation if enabled)
  - **Transitions**:
    - Save → clean saved state
    - Revert → return to last saved version
    - Discard → return to last saved version
  - **Accessibility**:
    - Document title or live region announces modified status
    - Clear explanation of what's unsaved
    - Options announced for handling changes

### Processing State
**Trigger**: System performing user-initiated action
**Applies To**: Any action requiring significant time

#### Variations
- **Immediate Processing** (<2s):
  - **Trigger**: Quick action initiated
  - **UI**:
    - Button shows loading state
    - May show inline progress indicator
    - Related UI may show temporary disabled state
  - **Messaging**: 
    - Optional: Brief status in button or nearby
  - **Actions**:
    - Cancel if long-running (>500ms threshold)
    - Related actions may be disabled
  - **Transitions**:
    - Complete → success or error state
    - Cancel → return to pre-action state
  - **Accessibility**:
    - Live region announces start/completion of action
    - Clear indication of cancellation option

- **Extended Processing** (2s-30s):
  - **Trigger**: Moderate length action
  - **UI**:
    - Dedicated progress indicator (bar, spinner, circle)
    - Shows percentage or step description
    - May allow minimization to background
    - Estimated time remaining if calculable
  - **Messaging**:
    - Primary: "[Action] in progress"
    - Secondary: "Estimated time remaining: [time]"
    - Instructional: What happens upon completion
  - **Actions**:
    - Cancel operation
    - Minimize to background/notification
    - May perform related preparatory work
  - **Transitions**:
    - Complete → success state with results
    - Error → error state with details
    - Cancel → return to pre-action state with cleanup
  - **Accessibility**:
    - Live region announces progress updates
    - Estimated time announced
    - Clear indication of cancellation option

- **Background Processing** (>30s or user may navigate away):
  - **Trigger**: Long-running action
  - **UI**:
    - Progress notification in non-intrusive location
    - May show in app header or system tray equivalent
    - Allows full navigation away
    - Completion may show toast or badge
  - **Messaging**:
    - Primary: "[Action] started"
    - Secondary: "You'll be notified when complete"
    - May show queue position if applicable
  - **Actions**:
    - View operation details
    - Cancel if still queued/processing
    - Related actions may be limited
  - **Transitions**:
    - Complete → completion notification with results access
    - Error → error notification with details
    - Cancel → cleanup notification
  - **Accessibility**:
    - Notification announces start/progress/completion
    - Persistent indication until addressed
    - Clear indication of completion or failure

### Confirmation State
**Trigger**: User initiated potentially destructive or significant action
**Applies To**: Delete, permanently modify, exit without save, etc.

#### Variations
- **Delete Confirmation**:
  - **Trigger**: User initiated delete action
  - **UI**:
    - Confirmation dialog or modal
    - Shows what will be deleted
    - May show impact (references, dependencies)
    - Clear primary (confirm) and secondary (cancel) actions
  - **Messaging**:
    - Primary: "Delete [item]?"
    - Secondary: Brief description of what will be deleted
    - Instructional: List of consequences or dependencies
    - Warning: "This action cannot be undone" (if true)
  - **Actions**:
    - Confirm deletion
    - Cancel and return
    - May show alternative (archive instead of delete)
  - **Transitions**:
    - Confirm → perform deletion
    - Cancel → return to original state
    - Alternative → perform alternative action
  - **Accessibility**:
    - Focus moves to cancel button (protective)
    - Clear announcement of what action will be performed
    - Announces irreversible nature if applicable

- **Exit Without Save**:
  - **Trigger**: User attempts to leave with unsaved changes
  - **UI**:
    - Confirmation modal or banner
    - Shows what changes will be lost
    - Options to save, discard, or cancel exit
  - **Messaging**:
    - Primary: "You have unsaved changes"
    - Secondary: "Are you sure you want to leave?"
    - Instructional: Summary of what will be lost
  - **Actions**:
    - Save and exit
    - Discard and exit
    - Cancel and continue editing
  - **Transitions**:
    - Save and exit → save then navigate
    - Discard and exit → navigate without saving
    - Cancel → remain in editor
  - **Accessibility**:
    - Focus management appropriate to action
    - Clear announcement of unsaved changes
    - Options clearly distinguished

- **Permission Change**:
  - **Trigger**: User modifying access rights or roles
  - **UI**:
    - Confirmation showing what permissions will change
    - May show affected users/resources
    - Clear indication of permission levels
  - **Messaging**:
    - Primary: "Change permissions for [item]?"
    - Secondary: Describes what will change
    - Instructional: List of affected parties and what changes
  - **Actions**:
    - Confirm changes
    - Review and modify
    - Cancel
  - **Transitions**:
    - Confirm → apply permission changes
    - Review → return to configuration
    - Cancel → return to original state
  - **Accessibility**:
    - Focus management appropriate to action
    - Clear announcement of permission changes
    - Announces affected parties and implications

## 5. Device States

### Desktop State
**Trigger**: Screen width ≥ 1024px
**Applies To**: Desktop and laptop computers
**UI Characteristics**:
- Full sidebar navigation (collapsible)
- Horizontal primary navigation
- Multi-column layouts
- Hover states for interaction feedback
- Keyboard shortcuts visible in tooltips
- Context menus on right-click
- Drag-and-drop with visual feedback
- Pixel-precise interactions possible
**Interactions**:
- Mouse and primary input
- Keyboard with extensive shortcuts
- Scroll wheel for precise control
- Large touch targets for accessibility
**Performance Considerations**:
- Higher fidelity visuals possible
- More complex animations acceptable
- Larger resource budgets for computations

### Tablet State
**Trigger**: Screen width ≥ 768px and < 1024px
**Applies To**: Tablets and large phones in landscape
**UI Characteristics**:
- Collapsible sidebar (often bottom navigation)
- Vertical or hybrid layouts
- Touch-optimized controls (minimum 48x48pt)
- Gesture-based navigation
- Split-screen capable
- Adaptive density based on orientation
**Interactions**:
- Touch primary, keyboard optional
- Multi-touch gestures (pinch, swipe, rotate)
- Stylus support where available
- Voice input integration
**Performance Considerations**:
- Medium fidelity visuals
- Moderate animation complexity
- Balanced resource usage for battery life

### Mobile State
**Trigger**: Screen width < 768px
**Applies To**: Smartphones and small devices
**UI Characteristics**:
- Bottom navigation bar (3-5 items)
- Full-screen modals for primary actions
- Vertical stacking layouts
- Large touch targets (minimum 48x48pt)
- Gesture-based navigation
- Collapsible sections as accordions
- Voice-first interaction options
**Interactions**:
- Touch primary
- Gestures (swipe, tap, pinch, zoom)
- Voice commands
- Limited keyboard (typically visible on demand)
**Performance Considerations**:
- Optimized for battery life
- Reduced visual complexity
- Minimal animations
- Efficient resource usage

### Touch State
**Trigger**: Touch input detected
**Applies To**: Any device with touch capability
**UI Characteristics**:
- Larger touch targets appear
- Hover states may be disabled
- Gesture guides may appear
- Palm rejection considerations
**Interactions**:
- Touch prioritized over mouse
- Gesture recognition active
- Pressure sensitivity where available
- Stylus input prioritized
**Accessibility Considerations**:
- Touch targets meet minimum size requirements
- Gestures have discoverable alternatives
- Force touch/haptic feedback considered

### Keyboard State
**Trigger**: Keyboard input detected
**Applies To**: Any device with keyboard capability
**UI Characteristics**:
- Focus indicators clearly visible
- Keyboard shortcuts documented
- Navigation optimized for tab order
- Modal dialogs trap focus appropriately
**Interactions**:
- Keyboard primary for navigation
- Enter/Space for activation
- Arrow keys for spatial navigation
- Escape for cancellation/dismissal
**Accessibility Considerations**:
- Logical tab order
- Visible focus indicators
- No keyboard traps
- All functionality available via keyboard

## State Transitions and Hierarchy

### State Priority Order
When multiple states could apply, the following priority determines which is shown:
1. **System States** (Offline, Maintenance, Degraded) - Highest priority
2. **Permission States** (No Access, Limited Access) 
3. **Data States** (Error, Empty, Loading, Partial Data)
4. **Interaction States** (Confirmation, Processing, Modified, Dirty, Pristine) - Lowest priority

### Concurrent States
Some states can coexist and should be composed:
- **Data + Permission**: E.g., Limited access with loading state
- **Device + Any**: All states adapt to device characteristics
- **Interaction + Data**: E.g., Processing state while loading additional data

### Transition Guidelines
- **Immediate Transitions**: State changes that happen instantly (permission changes)
- **Animated Transitions**: State changes with visual feedback (loading → loaded)
- **Buffered Transitions**: State changes with delayed feedback (offline → online)
- **Cancelable Transitions**: States that can be interrupted (long processing)
- **Irreversible Transitions**: States that cannot be undone (certain destructive actions)

## Implementation Guidelines

### State Detection
- **Centralized State Management**: Use application state container to track all state flags
- **Derived States**: Compute complex states from basic flags (e.g., "has unsaved changes")
- **Real-time Updates**: Subscribe to relevant events for state changes
- **Initial State**: Determine state on mount based on props and context
- **Cleanup**: Unsubscribe from events on unmount to prevent memory leaks

### UI Composition
- **State Components**: Create components that render different UIs based on state props
- **State HOCs**: Higher-order components that wrap base components with state logic
- **Render Props**: Pass state handling functions as props for maximum flexibility
- **Custom Hooks**: Encapsulate state logic in reusable hooks (usePageState, usePermissionState)
- **Suspense Integration**: Integrate with React Suspense for data loading states

### Accessibility Considerations
- **Live Regions**: Use aria-live for announcements that don't take focus
- **Focus Management**: Move focus appropriately when state changes
- **Screen Reader Announcements**: Ensure state changes are announced
- **Color Contrast**: Maintain contrast ratios in all state variations
- **Touch Targets**: Ensure minimum sizes in all states
- **Keyboard Navigation**: Maintain logical tab order across state transitions

### Testing
- **State Isolation**: Test each state in isolation
- **Transition Testing**: Test entering and exiting each state
- **Concurrent State Testing**: Test combinations of states
- **Accessibility Testing**: Verify each state with screen readers and keyboard-only
- **Performance Testing**: Ensure state transitions don't cause jank
- **Edge Case Testing**: Test rapid state changes, network fluctuations, etc.

## Conclusion
This comprehensive page states specification ensures that ResearchReel provides appropriate feedback and guidance in all possible scenarios. By clearly defining states, their triggers, UI composition, messaging, actions, transitions, and accessibility considerations, we create a robust foundation for handling the complexity of a modern web application.

Implementation teams can use this specification to:
1. Ensure consistent state handling across all features and pages
2. Guide accessibility testing and validation for all states
3. Inform automated testing strategies for state transitions
4. Provide clear handoff to design and development teams
5. Maintain consistency as the platform evolves over time

The state-driven approach ensures that users always receive appropriate feedback regardless of network conditions, permissions, data availability, or interaction context, creating a reliable and trustworthy user experience.