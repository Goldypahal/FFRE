# ResearchReel Complete Button Specification

## Button Classification System
ResearchReel uses a systematic approach to button design based on:
- **Visual Hierarchy**: Primary, Secondary, Tertiary, Link
- **Context**: Global, Page-specific, Item-specific, Tool-specific
- **State**: Default, Hover, Focus, Active, Disabled, Loading
- **Size**: Small (24px), Medium (32px), Large (40px), Extra Large (48px)
- **Icon Only**: Buttons with only icons (typically 32-48px touch target)
- **Icon + Text**: Buttons with both icon and label
- **Text Only**: Buttons with only text label

## Core Button Specifications

### 1. Global Navigation Buttons
#### Application Logo/Home Button
- **Name**: AppLogo/Home
- **Location**: Top-left of header (sidebar collapsed) or sidebar top
- **Permission**: All authenticated users
- **Action**: Navigate to personal dashboard
- **API Called**: None (client-side navigation)
- **Database Action**: None
- **Loading State**: None
- **Success State**: Smooth transition to dashboard
- **Failure State**: None (client-side route)
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/dashboard`
- **Analytics**: `nav_home_click`
- **Audit Log**: None (navigation action)
- **Edge Cases**: 
  - When in dashboard: Visual indication of current location
  - Mobile: May be hidden in favor of bottom navigation
  
#### Global Search Button
- **Name**: GlobalSearch
- **Location**: Header toolbar (right side)
- **Permission**: All authenticated users
- **Action**: Focus search input and show recent/popular
- **API Called**: `GET /api/v2/search/suggestions?scope=global`
- **Database Action**: Read search logs, update frequency
- **Loading State**: Show spinner in button during suggestion fetch
- **Success State**: Display suggestion dropdown
- **Failure State**: Show error tooltip, fallback to recent searches
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None (opens dropdown)
- **Analytics**: `search_global_focus`
- **Audit Log**: None
- **Edge Cases**:
  - Empty state: Show placeholder text "Search projects, assets, help..."
  - Connection error: Show cached suggestions with warning indicator
  - Rate limited: Show last known suggestions with rate limit notice

#### Notification Button
- **Name**: NotificationBell
- **Location**: Header toolbar
- **Permission**: All authenticated users
- **Action**: Open notification center dropdown
- **API Called**: `GET /api/v2/notifications?unread_only=false&limit=20`
- **Database Action**: Read notifications table, update last_seen timestamp
- **Loading State**: Show spinner instead of bell icon
- **Success State**: Display notification panel with badges
- **Failure State**: Show error badge, fallback to cached notifications
- **Toast Message**: None on open, except for permission errors
- **Modal**: None (dropdown panel)
- **Redirect**: None
- **Analytics**: `notifications_dropdown_open`
- **Audit Log**: None (viewing notifications doesn't change state)
- **Edge Cases**:
  - Zero notifications: Show empty state with "All caught up!" message
  - Permission error: Show login required message
  - New arrivals: Animate new items with subtle pulse
  
#### User Profile Button
- **Name**: UserProfileMenu
- **Location**: Header toolbar (far right)
- **Permission**: All authenticated users
- **Action**: Open user profile dropdown menu
- **API Called**: `GET /api/v2/users/me` (on first open or stale cache)
- **Database Action**: Read user profile, update last_seen
- **Loading State**: Show spinner or skeleton avatar
- **Success State**: Display profile menu with options
- **Failure State**: Show error state, retry option
- **Toast Message**: None
- **Modal**: None (dropdown)
- **Redirect**: None
- **Analytics**: `user_profile_dropdown_open`
- **Audit Log**: None
- **Edge Cases**:
  - Guest/Limited account: Show appropriate menu options
  - SSO users: Hide password management options
  - Admin users: Show admin console shortcut
  
#### Workspace Selector Button
- **Name**: WorkspaceSelector
- **Location**: Header toolbar (left of search)
- **Permission**: All authenticated users with access to multiple workspaces
- **Action**: Open workspace switcher dropdown
- **API Called**: `GET /api/v2/workspaces`
- **Database Action**: Read workspace memberships
- **Loading State**: Show spinner instead of workspace name
- **Success State**: Display workspace list with indicators
- **Failure State**: Show error state, default to personal workspace
- **Toast Message**: None
- **Modal**: None (dropdown)
- **Redirect**: None
- **Analytics**: `workspace_switcher_open`
- **Audit Log**: None
- **Edge Cases**:
  - Single workspace: Display workspace name without dropdown
  - No access: Redirect to onboarding or show error
  - Switching workflow: Persist last used tab/context when possible

### 2. Sidebar Navigation Buttons
#### Navigate to Dashboard
- **Name**: NavDashboard
- **Location**: Sidebar navigation (top section)
- **Permission**: All authenticated users
- **Action**: Set active tab to dashboard
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update URL and main content
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/dashboard`
- **Analytics**: `nav_dashboard_click`
- **Audit Log**: None
- **Edge Cases**:
  - Already on dashboard: Visual active state, no navigation
  
#### Navigate to Projects
- **Name**: NavProjects
- **Location**: Sidebar navigation
- **Permission**: All authenticated users
- **Action**: Set active tab to projects view
- **API Called**: None (may prefetch projects)
- **Database Action**: None (may update last_seen timestamp)
- **Loading State**: None
- **Success State**: Update URL and show projects view
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/projects`
- **Analytics**: `nav_projects_click`
- **Audit Log**: None
- **Edge Cases**:
  - Empty projects: Show empty state with create project CTA
  
#### Navigate to Assets
- **Name**: NavAssets
- **Location**: Sidebar navigation
- **Permission**: All authenticated users
- **Action**: Set active tab to assets library
- **API Called**: None (may prefetch recent assets)
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update URL and show assets view
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/assets`
- **Analytics**: `nav_assets_click`
- **Audit Log**: None
- **Edge Cases**:
  - First time: Show guided tour CTA for asset upload
  
#### Navigate to Templates
- **Name**: NavTemplates
- **Location**: Sidebar navigation
- **Permission**: All authenticated users
- **Action**: Set active tab to templates gallery
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update URL and show templates view
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/templates`
- **Analytics**: `nav_templates_click`
- **Audit Log**: None
- **Edge Cases**:
  - No custom templates: Show platform defaults with create CTA
  
#### Navigate to Settings
- **Name**: NavSettings
- **Location**: Sidebar navigation (bottom section)
- **Permission**: All authenticated users
- **Action**: Open settings page
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Navigate to `/app/settings`
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/settings`
- **Analytics**: `nav_settings_click`
- **Audit Log**: None
- **Edge Cases**:
  - Limited permissions: Show only available sections
  
### 3. Dashboard Buttons
#### New Project Button
- **Name**: NewProject
- **Location**: Dashboard header toolbar and welcome section
- **Permission**: All authenticated users
- **Action**: Open project creation wizard/modal
- **API Called**: None (client-side state initialization)
- **Database Action**: None
- **Loading State**: Show spinner in button during modal load
- **Success State**: Display project creation interface
- **Failure State**: Show error modal if unable to initialize
- **Toast Message**: None
- **Modal**: Project creation wizard
- **Redirect**: None (stays in dashboard context)
- **Analytics**: `dashboard_new_project_click`
- **Audit Log**: None
- **Edge Cases**:
  - Template selection: Default to blank project
  - Quota exceeded: Show upgrade modal with current usage
  
#### Upload Media Button
- **Name**: UploadMedia
- **Location**: Dashboard toolbar and welcome section
- **Permission**: All authenticated users with upload permissions
- **Action**: Open media upload interface
- **API Called**: None (client-side)
- **Database Action**: None
- **Loading State**: Show spinner during initialization
- **Success State**: Display upload interface
- **Failure State**: Show error if upload service unavailable
- **Toast Message**: None
- **Modal**: Media upload dialog
- **Redirect**: None
- **Analytics**: `dashboard_upload_click`
- **Audit Log**: None
- **Edge Cases**:
  - Storage limit: Show storage management options
  - Browser restrictions: Fallback to file picker dialog
  
#### Invite Team Button
- **Name**: InviteTeam
- **Location**: Dashboard toolbar and team section
- **Permission**: Users with team management rights
- **Action**: Open team invitation dialog
- **API Called**: `POST /api/v2/workspaces/{id}/invites`
- **Database Action**: Create invitation record, update workspace
- **Loading State**: Show spinner during invite send
- **Success State**: Display confirmation with invite details
- **Failure State**: Show error with specific reason (email invalid, quota exceeded)
- **Toast Message**: "Invitation sent to [email]" on success
- **Modal**: Team invitation dialog
- **Redirect**: None
- **Analytics**: `dashboard_invite_team_click`
- **Audit Log**: `USER_INVITE_SENT` (with invite ID, email, workspace)
- **Edge Cases**:
  - Self-invite: Show error "Cannot invite yourself"
  - Existing member: Show message "User already in workspace"
  
#### View Analytics Button
- **Name**: ViewAnalytics
- **Location**: Dashboard stats cards
- **Permission**: All authenticated users
- **Action**: Navigate to analytics dashboard
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Navigate to `/app/analytics`
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: `/app/analytics`
- **Analytics**: `dashboard_view_analytics_click`
- **Audit Log**: None
- **Edge Cases**:
  - Insufficient data: Show placeholder with guidance
  
### 4. Project Creation Wizard Buttons
#### Project Type Selection Buttons
- **Name**: SelectProjectType_[TYPE] (e.g., SelectProjectType_MarketingVideo)
- **Location**: Project creation wizard step 1
- **Permission**: All authenticated users
- **Action**: Select project type and advance to next step
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update wizard state, show template selection
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None (wizard step change)
- **Redirect**: None
- **Analytics**: `wizard_projecttype_selected_[TYPE]`
- **Audit Log**: None
- **Edge Cases**:
  - Limited by subscription: Grey out unavailable types with tooltip
  
#### Template Selection Buttons
- **Name**: SelectTemplate_[TEMPLATE_ID]
- **Location**: Project creation wizard step 2
- **Permission**: All authenticated users
- **Action**: Select template and advance to metadata step
- **API Called**: `GET /api/v2/templates/{id}` (to fetch full details)
- **Database Action**: Read template metadata
- **Loading State**: Show spinner in template card during fetch
- **Success State**: Preview template details, advance wizard step
- **Failure State**: Show error, revert to previous selection
- **Toast Message**: None
- **Modal**: None (stays in wizard)
- **Redirect**: None
- **Analytics**: `wizard_template_selected_[TEMPLATE_ID]`
- **Audit Log**: None
- **Edge Cases**:
  - Premium template: Show upgrade prompt if required
  
#### Back Button (Wizard)
- **Name**: WizardBack
- **Location**: Wizard footer (left side)
- **Permission**: All authenticated users
- **Action**: Return to previous wizard step
- **API Called**: None
- **Database Action`: None
- **Loading State**: None
- **Success State**: Show previous wizard step
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None (remains in wizard)
- **Analytics**: `wizard_back_click`
- **Audit Log**: None
- **Edge Cases**:
  - First step: Button disabled or navigates to dashboard cancel
  
#### Next Button (Wizard)
- **Name**: WizardNext
- **Location**: Wizard footer (right side)
- **Permission**: All authenticated users (when form valid)
- **Action**: Advance to next wizard step or create project
- **API Called**: `POST /api/v2/projects` (on final step)
- **Database Action**: Create project record, initialize default assets
- **Loading State**: Show spinner during project creation
- **Success State**: Navigate to new project editor
- **Failure State**: Show validation errors or creation failure
- **Toast Message**: "Project created successfully" on success
- **Modal**: None (unless error)
- **Redirect**: `/app/projects/{projectId}/editor`
- **Analytics**: `wizard_next_click` or `project_create_success`
- **Audit Log**: `PROJECT_CREATED` (with project ID, type, template)
- **Edge Cases**:
  - Invalid form: Show inline validation errors
  - Duplicate name: Suggest alternatives with timestamp
  
#### Cancel Button (Wizard)
- **Name**: WizardCancel
- **Location**: Wizard footer (left side, next to back)
- **Permission**: All authenticated users
- **Action**: Cancel project creation and return to dashboard
- **API Called`: None
- **Database Action`: None
- **Loading State`: None
- **Success State`: Return to dashboard
- **Failure State`: None
- **Toast Message**: None
- **Modal`: None
- **Redirect`: `/app/dashboard`
- **Analytics`: `wizard_cancel_click`
- **Audit Log`: None
- **Edge Cases**:
  - Unsaved changes: Show confirmation modal if applicable
  
### 5. Project List/Grid Buttons
#### Project Card Menu Button
- **Name**: ProjectCardMenu
- **Location**: Top-right corner of project card (hover/reveal)
- **Permission**: Based on project role
- **Action**: Open context menu for project operations
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Display context menu
- **Failure State**: None
- **Toast Message**: None
- **Modal**: Context menu (positioned near button)
- **Redirect**: None
- **Analytics**: `project_card_menu_open`
- **Audit Log**: None
- **Edge Cases**:
  - Selection mode: Changes to checkbox for multi-select
  
#### Project Card Checkbox
- **Name**: ProjectCardSelect
- **Location**: Top-left corner of project card (in selection mode)
- **Permission**: All authenticated users
- **Action**: Toggle project selection for batch operations
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update selection state
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `project_selection_toggle_[ID]`
- **Audit Log**: None
- **Edge Cases**:
  - Select all: Header checkbox toggles all visible items
  
#### Project Card Favorite Button
- **Name**: ProjectCardFavorite
- **Location**: Bottom-left of project card
- **Permission**: Project member with view access
- **Action**: Toggle project favorite status
- **API Called**: `POST /api/v2/projects/{id}/favorite`
- **Database Action**: Update user_project_preferences table
- **Loading State**: Show spinner in button during request
- **Success State**: Toggle filled/empty star icon
- **Failure State**: Show error tooltip, revert icon state
- **Toast Message**: "Added to favorites"/"Removed from favorites"
- **Modal**: None
- **Redirect**: None
- **Analytics**: `project_favorite_toggle_[ID]`
- **Audit Log**: `USER_FAVORITE_TOGGLED` (with project ID, user ID)
- **Edge Cases**:
  - Offline: Queue for later sync with optimistic update
  
#### Project Card More Actions Button (in list)
- **Name**: ProjectCardMoreActions
- **Location**: Action column in list view
- **Permission**: Based on project role
- **Action**: Open context menu for project operations
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Display context menu
- **Failure State**: None
- **Toast Message**: None
- **Modal**: Context menu
- **Redirect**: None
- **Analytics**: `project_list_menu_open_[ID]`
- **Audit Log**: None
- **Edge Cases**:
  - Hover state: Tooltip showing "More actions"
  
### 6. Project Editor Buttons
#### Undo Button
- **Name**: Undo
- **Location**: Editor header toolbar (left side)
- **Permission**: Project editors and owners
- **Action**: Revert last user action
- **API Called**: None (client-side state management)
- **Database Action**: None
- **Loading State**: None (instantaneous)
- **Success State**: Restore previous state, update redo stack
- **Failure State**: None (client-side operation)
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_undo_performed`
- **Audit Log**: `EDITOR_ACTION_UNDONE` (with action details)
- **Edge Cases**:
  - No actions to undo: Button disabled
  - Complex state: May involve multiple substep reversals
  
#### Redo Button
- **Name**: Redo
- **Location**: Editor header toolbar (next to undo)
- **Permission**: Project editors and owners
- **Action**: Reapply last undone action
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Restore next state, update undo stack
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_redo_performed`
- **Audit Log**: `EDITOR_ACTION_REDONE` (with action details)
- **Edge Cases**:
  - No actions to redo: Button disabled
  
#### Play/Pause Button
- **Name**: PlayPause
- **Location**: Editor header toolbar and media player overlay
- **Permission**: Project viewers and above
- **Action**: Toggle playback of current composition
- **API Called**: None (client-side)
- **Database Action**: None (may update last_viewed timestamp)
- **Loading State**: None
- **Success State**: Toggle between play and pause states
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_playback_toggled` (with state: play/pause)
- **Audit Log**: None (frequent action, not individually logged)
- **Edge Cases**:
  - End of media: Auto-pause and reset to beginning
  - Seeking during play: Maintains play state
  
#### Stop Button
- **Name**: Stop
- **Location**: Editor header toolbar (next to play/pause)
- **Permission**: Project viewers and above
- **Action**: Stop playback and reset to beginning
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Pause playback, set time to 00:00:00:00
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_playback_stopped`
- **Audit Log**: None
- **Edge Cases**:
  - Already at beginning: No visual change
  
#### Frame Back/Forward Buttons
- **Name**: FrameBack/FrameForward
- **Location**: Editor header toolbar (near play controls)
- **Permission**: Project viewers and above
- **Action**: Move playhead by single frame forward/backward
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update playhead position by ±1 frame
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_frame_stepped_[BACK/FORWARD]`
- **Audit Log**: None
- **Edge Cases**:
  - At start/end: Button disabled when at boundary
  
#### Zoom In/Out Buttons
- **Name**: ZoomIn/ZoomOut
- **Location**: Editor header toolbar (right side)
- **Permission**: Project viewers and above
- **Action**: Increase/decrease timeline zoom level
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Update zoom level, re-render visible range
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_zoom_changed_[IN/OUT]` (with new level)
- **Audit Log**: None
- **Edge Cases**:
  - Minimum/maximum zoom: Button disabled at limits
  
#### Fit to Window Button
- **Name**: FitToWindow
- **Location**: Editor header toolbar (near zoom controls)
- **Permission**: Project viewers and above
- **Action**: Adjust zoom to show entire timeline
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Set optimal zoom level, re-render
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect`: None
- **Analytics`: `editor_fit_to_window_clicked`
- **Audit Log`: None
- **Edge Cases**:
  - Empty timeline: No action, button may be disabled
  
#### Add Track Button
- **Name**: AddTrack
- **Location**: Track header area (hover to reveal) or timeline context menu
- **Permission**: Project editors and above
- **Action**: Add new empty track of selected type
- **API Called**: None (client-side)
- **Database Action**: None
- **Loading State**: None
- **Success State**: Insert new track at specified position
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_track_added_[TYPE]` (video/audio/effects/title)
- **Audit Log**: None
- **Edge Cases**:
  - Track limits: Show warning if approaching practical limits
  
#### Delete Track Button
- **Name**: DeleteTrack
- **Location**: Track header (on hover) or track context menu
- **Permission**: Project editors and above
- **Action**: Remove selected track and its contents
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Remove track, shift subsequent tracks up
- **Failure State**: None
- **Toast Message**: "Track deleted" (with undo option)
- **Modal**: Confirmation dialog for tracks with content
- **Redirect**: None
- **Analytics**: `editor_track_deleted_[TYPE]`
- **Audit Log**: `TRACK_DELETED` (with track ID, type, clip count)
- **Edge Cases**:
  - Last track: Prevent deletion of final track in category
  - Protected tracks: Locked tracks require unlock first
  
#### Split Clip Button
- **Name**: SplitClip
- **Location**: Editor toolbar (active when clip selected)
- **Permission**: Project editors and above
- **Action**: Split selected clip at playhead position
- **API Called**: None (client-side)
- **Database Action**: None
- **Loading State**: None
- **Success State**: Replace clip with two clips at split point
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_clip_split_at_[TIMECODE]`
- **Audit Log**: None
- **Edge Cases**:
  - No clip selected: Button disabled
  - At clip boundaries: Show tooltip "Already at edge"
  
#### Duplicate Clip Button
- **Name**: DuplicateClip
- **Location**: Editor toolbar (active when clip selected)
- **Permission**: Project editors and above
- **Action**: Create copy of selected clip at same position
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Insert identical clip after original
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_clip_duplicated_[SOURCE_ID]`
- **Audit Log`: None
- **Edge Cases**:
  - Referenced assets: May create new proxy or reference same
  
#### Delete Clip Button
- **Name**: DeleteClip
- **Location**: Editor toolbar (active when clip selected)
- **Permission**: Project editors and above
- **Action**: Remove selected clip(s) from timeline
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Remove clips, close gap (ripple delete by default)
- **Failure State**: None
- **Toast Message**: "Clip(s) deleted" (with count)
- **Modal**: None (unless multiple clips selected)
- **Redirect**: None
- **Analytics**: `editor_clips_deleted_[COUNT]`
- **Audit Log`: None
- **Edge Cases**:
  - Ripple vs slide: Shift-click for slide delete (close gap vs leave space)
  
#### Enable/Disable Track Button
- **Name**: TrackEnableDisable
- **Location**: Track header (visibility toggle)
- **Permission**: Project viewers and above
- **Action**: Hide/show track in preview and exports
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Toggle track visibility, update preview
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_track_visibility_toggled_[ID]_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Solo mode: Enabling another track disables solo on others
  
#### Solo Track Button
- **Name**: TrackSolo
- **Location**: Track header (solo toggle)
- **Permission**: Project editors and above
- **Action**: Mute all other tracks, hear only this track
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Enable solo mode, mute other tracks
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `editor_track_solo_toggled_[ID]_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Multiple solo: Only one track can be solo at a time
  
#### Mute Track Button
- **Name**: TrackMute
- **Location**: Track header (mute toggle)
- **Permission**: Project viewers and above
- **Action**: Silence track audio while keeping video visible
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Toggle mute state, update audio mix
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect`: None
- **Analytics`: `editor_track_mute_toggled_[ID]_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Video-only tracks: Button hidden or disabled
  
#### Lock Track Button
- **Name**: TrackLock
- **Location**: Track header (lock toggle)
- **Permission**: Project editors and above
- **Action**: Prevent accidental modification of track contents
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Lock track, show lock icon
- **Failure State`: None
- **Toast Message`: None
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_track_lock_toggled_[ID]_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Editing locked tracks: Requires unlock first
  
#### Add Effect Button
- **Name**: AddEffect
- **Location**: Effects panel header or track context menu
- **Permission**: Project editors and above
- **Action**: Open effect browser to add effect to selected item
- **API Called**: `GET /api/v2/effects?type=[selected_type]`
- **Database Action**: Read available effects
- **Loading State**: Show spinner in button during fetch
- **Success State**: Display effect browser modal
- **Failure State**: Show error if unable to load effects
- **Toast Message**: None
- **Modal**: Effect browser
- **Redirect**: None
- **Analytics**: `editor_add_effect_clicked`
- **Audit Log`: None
- **Edge Cases**:
  - No selection: Button disabled or applies to track
  
#### Remove Effect Button
- **Name**: RemoveEffect
- **Location**: Effect badge on clip/track or effect panel
- **Permission**: Project editors and above
- **Action**: Remove selected effect from item
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Remove effect, update appearance immediately
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect`: None
- **Analytics`: `editor_effect_removed_[EFFECT_ID]_[ITEM_TYPE]`
- **Audit Log`: None
- **Edge Cases**:
  - Multiple effects: Remove topmost or selected based on UI state
  
#### Playhead Snap Button
- **Name**: PlayheadSnap
- **Location**: Timeline ruler (toggle button)
- **Permission**: Project viewers and above
- **Action**: Toggle snapping of playhead to significant points
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Toggle snap state, update behavior
- **Failure State`: None
- **Toast Message`: None
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_playhead_snap_toggled_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Snap to: Grid, markers, clip boundaries, etc. (configurable)
  
#### Loop Region Button
- **Name**: LoopRegionToggle
- **Location**: Timeline ruler (related to loop controls)
- **Permission**: Project editors and above
- **Action**: Toggle loop region visibility and editing
- **API Called**: None
- **Database Action**: None
- **Loading State`: None
- **Success State**: Show/hide loop brackets, enable editing
- **Failure State`: None
- **Toast Message`: None
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_loop_region_toggled_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Setting loop: Drag handles to set in/out points
  
#### Marker Buttons
- **Name**: AddMarker/[MarkerType] (e.g., AddMarker_Chapter, AddMarker_Comment)
- **Location**: Timeline ruler or marker toolbar
- **Permission**: Project viewers and above (some marker types require edit)
- **Action**: Create new marker at playhead position
- **API Called**: None (client-side for temporary) or `POST /api/v2/markers`
- **Database Action`: Create marker record (if persistent)
- **Loading State`: None (client) or spinner (server)
- **Success State`: Display marker at position
- **Failure State`: Show error if unable to create
- **Toast Message`: None for client, "Marker added" for server
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_marker_added_[TYPE]_[TIMECODE]`
- **Audit Log`: `MARKER_CREATED` (for persistent markers)
- **Edge Cases**:
  - Duplicate position: May stack or merge based on type
  
#### Export Button
- **Name**: Export
- **Location**: Editor header toolbar (primary action)
- **Permission**: Project editors and above (export rights may vary)
- **Action**: Open export configuration dialog
- **API Called**: None
- **Database Action**: None
- **Loading State**: Show spinner during dialog initialization
- **Success State**: Display export configuration interface
- **Failure State**: Show error if export service unavailable
- **Toast Message`: None
- **Modal`: Export configuration dialog
- **Redirect`: None
- **Analytics`: `editor_export_dialog_opened`
- **Audit Log`: None
- **Edge Cases**:
  - In-progress render: Show queue position with estimate
  
#### Share Button
- **Name**: Share
- **Location**: Editor header toolbar (secondary action)
- **Permission**: Project members with share permissions
- **Action**: Open sharing and collaboration dialog
- **API Called**: None
- **Database Action**: None
- **Loading State**: Show spinner during dialog load
- **Success State**: Display sharing options
- **Failure State**: Show error if sharing service unavailable
- **Toast Message`: None
- **Modal`: Sharing and collaboration dialog
- **Redirect`: None
- **Analytics`: `editor_share_dialog_opened`
- **Audit Log`: None
- **Edge Cases**:
  - View-only users: Button disabled or shows request access
  
#### Settings Button
- **Name**: EditorSettings
- **Location**: Editor header toolbar (far right)
- **Permission**: Project members with settings access
- **Action**: Open project-specific settings dialog
- **API Called**: `GET /api/v2/projects/{id}/settings`
- **Database Action**: Read project settings
- **Loading State**: Show spinner during settings fetch
- **Success State**: Display project settings interface
- **Failure State**: Show error if unable to load settings
- **Toast Message`: None
- **Modal`: Project settings dialog
- **Redirect`: None
- **Analytics`: `editor_settings_dialog_opened`
- **Audit Log`: None
- **Edge Cases**:
  - Inherited settings: Show which settings come from workspace/template
  
#### Fullscreen Button
- **Name**: ToggleFullscreen
- **Location**: Editor header toolbar or media player overlay
- **Permission**: Project viewers and above
- **Action**: Toggle fullscreen mode for video preview
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Enter/exit fullscreen with appropriate UI changes
- **Failure State`: None
- **Toast Message`: None
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_fullscreen_toggled_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Browser restrictions: Fallback to maximizing window
  
#### Cinema Mode Button
- **Name**: ToggleCinemaMode
- **Location**: Editor header toolbar or media player overlay
- **Permission**: Project viewers and above
- **Action**: Hide UI chrome for distraction-free preview
- **API Called**: None
- **Database Action**: None
- **Loading State`: None
- **Success State**: Hide non-essential UI, focus on video
- **Failure State`: None
- **Toast Message`: None
- **Modal`: None
- **Redirect`: None
- **Analytics`: `editor_cinema_mode_toggled_[STATE]`
- **Audit Log`: None
- **Edge Cases**:
  - Responsive: May behave differently on narrow screens
  
### 7. Asset Library Buttons
#### Upload Button
- **Name**: AssetUpload
- **Location**: Asset library toolbar and drag zone
- **Permission**: All authenticated users with upload permissions
- **Action**: Open file selection dialog
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Display native file picker
- **Failure State**: None
- **Toast Message**: None
- **Modal**: Native file dialog
- **Redirect**: None
- **Analytics**: `asset_upload_dialog_opened`
- **Audit Log**: None
- **Edge Cases**:
  - Drag/drop available: Visual hints when dragging over zone
  
#### New Folder Button
- **Name**: NewFolder
- **Location**: Asset library toolbar
- **Permission**: Users with folder creation rights
- **Action**: Create new folder in current location
- **API Called**: `POST /api/v2/folders`
- **Database Action**: Create folder record
- **Loading State**: Show spinner during creation
- **Success State**: Display folder in grid, open rename prompt
- **Failure State**: Show error if unable to create (name conflict, etc.)
- **Toast Message**: "Folder created"
- **Modal**: Inline rename or separate dialog
- **Redirect**: None
- **Analytics**: `asset_folder_created_[ID]`
- **Audit Log**: `FOLDER_CREATED` (with folder ID, parent ID)
- **Edge Cases**:
  - Root folder: May have different naming rules
  
#### Select All Button
- **Name**: SelectAllAssets
- **Location**: Asset library toolbar (left side)
- **Permission**: All authenticated users
- **Action**: Select all visible assets in current view
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Select all assets in current viewport
- **Failure State**: None
- **Toast Message**: None
- **Modal**: None
- **Redirect**: None
- **Analytics**: `asset_select_all_[VIEW_TYPE]`
- **Audit Log**: None
- **Edge Cases**:
  - Virtualized grid: Selects all loaded items, not all total
  
#### Delete Button
- **Name**: AssetDelete
- **Location**: Asset library toolbar (right side) and item context menu
- **Permission**: Users with delete rights on assets
- **Action**: Move selected assets to trash
- **API Called**: `DELETE /api/v2/assets/{id}` (batch endpoint available)
- **Database Action**: Update asset status to trashed, track quota
- **Loading State**: Show spinner during deletion process
- **Success State**: Remove items from grid, show undo toast
- **Failure State**: Show error with specific reason per item
- **Toast Message**: "X item(s) moved to trash"
- **Modal**: Confirmation dialog for multiple items
- **Redirect**: None
- **Analytics**: `asset_deleted_[COUNT]`
- **Audit Log**: `ASSET_TRASHED` (with asset IDs, reason)
- **Edge Cases**:
  - Referenced in projects: Show warning with project count
  - System assets: May be protected from deletion
  
#### Download Button
- **Name**: AssetDownload
- **Location**: Asset item toolbar (on hover/select) or context menu
- **Permission**: Users with download rights on assets
- **Action**: Download original file to local device
- **API Called**: `GET /api/v2/assets/{id}/download`
- **Database Action**: Log download, update last_accessed timestamp
- **Loading State**: Show progress indicator during download prep
- **Success State**: Initiate browser download
- **Failure State**: Show error if file unavailable or permission denied
- **Toast Message**: "Download started" (browser handles completion)
- **Modal**: Progress dialog for large files
- **Redirect**: None (browser download)
- **Analytics**: `asset_downloaded_[ID]`
- **Audit Log**: `ASSET_DOWNLOADED` (with asset ID, user ID, size)
- **Edge Cases**:
  - Large files: May use chunked download or signed URLs
  
#### Add to Project Button
- **Name**: AssetAddToProject
- **Location**: Asset item toolbar or bulk actions menu
- **Permission**: Users with edit rights on target projects
- **Action**: Add selected asset(s) to target project timeline
- **API Called**: None (client-side, adds to timeline state)
- **Database Action**: None (until project save)
- **Loading State**: None
- **Success State**: Asset appears in project timeline
- **Failure State**: None
- **Toast Message**: "Added to project" (with undo option)
- **Modal**: None
- **Redirect**: None
- **Analytics**: `asset_added_to_project_[PROJECT_ID]_[COUNT]`
- **Audit Log**: None (until project save)
- **Edge Cases**:
  - Multiple projects: Prompt for target project selection
  - Current project: May show "Already in project" indicator
  
#### Details Button
- **Name**: AssetDetails
- **Location**: Asset item toolbar or double-click action
- **Permission**: All authenticated users with view access
- **Action**: Open detailed asset view
- **API Called**: `GET /api/v2/assets/{id}`
- **Database Action**: Read asset metadata, usage stats
- **Loading State**: Show skeleton during data load
- **Success State**: Display asset details view
- **Failure State**: Show error if asset not found or access denied
- **Toast Message**: None
- **Modal**: Asset details view (full screen or sidebar)
- **Redirect**: None
- **Analytics**: `asset_details_viewed_[ID]`
- **Audit Log**: None
- **Edge Cases**:
  - Processing asset: Show current stage and estimated time
  
#### Favorite Button
- **Name**: AssetFavorite
- **Location**: Asset item toolbar (top corner)
- **Permission**: All authenticated users
- **Action**: Toggle asset favorite status
- **API Called**: `POST /api/v2/assets/{id}/favorite`
- **Database Action**: Update user_asset_preferences table
- **Loading State**: Show spinner during request
- **Success State**: Toggle filled/empty star icon
- **Failure State**: Show error tooltip, revert icon state
- **Toast Message**: "Added to favorites"/"Removed from favorites"
- **Modal**: None
- **Redirect**: None
- **Analytics**: `asset_favorite_toggle_[ID]`
- **Audit Log**: `USER_FAVORITE_TOGGLED` (with asset ID, user ID)
- **Edge Cases**:
  - Offline: Queue for later sync with optimistic update
  
#### Share Button
- **Name**: AssetShare
- **Location**: Asset item toolbar or context menu
- **Permission**: Users with share rights on assets
- **Action**: Open sharing options for asset
- **API Called**: None
- **Database Action**: None
- **Loading State**: None
- **Success State**: Display sharing dialog
- **Failure State**: None
- **Toast Message**: None
- **Modal**: Sharing dialog
- **Redirect**: None
- **Analytics**: `asset_shared_[ID]`
- **Audit Log**: `ASSET_SHARED` (with asset ID, user ID, method)
- **Edge Cases**:
  - Public assets: May show link copying option
  
#### Move to Folder Button
- **Name**: AssetMoveToFolder
- **Location**: Asset item toolbar or bulk actions menu
- **Permission**: Users with modify rights on assets and target folder
- **Action**: Move selected asset(s) to target folder
- **API Called**: `PUT /api/v2/assets/{id}/folder/{folderId}`
- **Database Action**: Update folder_id foreign key
- **Loading State**: Show spinner during move operation
- **Success State**: Asset appears in target folder
- **Failure State**: Show error if move fails (quota, permissions)
- **Toast Message**: "Moved to folder"
- **Modal**: Folder selection dialog
- **Redirect**: None
- **Analytics**: `asset_moved_to_folder_[COUNT]`
- **Audit Log**: `ASSET_MOVED` (with asset IDs, source folder, target folder)
- **Edge Cases**:
  - Same folder: No action, may show tooltip
  
#### Copy Button
- **Name**: AssetCopy
- **Location**: Asset item toolbar or context menu
- **Permission**: Users with create rights on assets
- **Action**: Create duplicate of selected asset(s)
- **API Called**: `POST /api/v2/assets/{id}/copy`
- **Database Action**: Create new asset record with copied metadata
- **Loading State**: Show spinner during copy process
- **Success State**: Duplicate appears in same location
- **Failure State**: Show error if copy fails (quota exceeded)
- **Toast Message**: "Copied"
- **Modal**: None (unless batch with progress)
- **redirect**: None
- **Analytics**: `asset_copied_[COUNT]`
- **Audit Log**: `ASSET_COPIED` (with source IDs, new IDs)
- **Edge Cases**:
  - Large assets: May reference same storage with copy-on-write
  
#### Rename Button
- **Name**: AssetRename
- **Location**: Asset item toolbar (inline edit) or context menu
- **Permission**: Users with edit rights on assets
- **Action**: Rename selected asset
- **API Called**: `PATCH /api/v2/assets/{id}`
- **Database Action**: Update name field
- **Loading State**: Show spinner during request
- **Success State**: Asset displays new name
- **Failure State**: Show error if name invalid or duplicated
- **Toast Message**: "Renamed"
- **Modal**: Inline edit or separate dialog
- **Redirect**: None
- **Analytics**: `asset_renamed_[ID]_[OLD_NAME]_[NEW_NAME]`
- **Audit Log**: `ASSET_RENAMED` (with asset ID, old name, new name)
- **Edge Cases**:
  - Special characters: May be restricted or auto-sanitized
  
#### Properties Button
- **Name**: AssetProperties
- **Location**: Asset item toolbar or details view
- **Permission**: All authenticated users with view access
- **Action**: Open asset properties/technical details view
- **API Called**: `GET /api/v2/assets/{id}/properties`
- **Database Action**: Read technical metadata
- **Loading State**: Show spinner during load
- **Success State**: Display properties view
- **Failure State**: Show error if properties unavailable
- **Toast Message**: None
- **Modal**: Properties view dialog
- **Redirect**: None
- **Analytics**: `asset_properties_viewed_[ID]`
- **Audit Log**: None
- **Edge Cases**:
  - Processing: Show estimated time for metadata extraction
  
#### Use as Template Button
- **Name**: AssetUseAsTemplate
- **Location**: Asset item toolbar or context menu
- **Permission**: Users with template creation rights
- **Action**: Create template from selected asset
- **API Called**: `POST /api/v2/templates` (with asset data)
- **Database Action**: Create template record
- **Loading State**: Show spinner during template creation
- **Success State**: Template appears in template library
- **Failure State**: Show error if creation fails
- **Toast Message**: "Template created"
- **Modal**: Template creation confirmation
- **Redirect**: None
- **analytics**: `asset_used_as_template_[ID]`
- **Audit Log**: `TEMPLATE_CREATED_FROM_ASSET` (with source asset ID)
- **Edge Cases**:
  - Already template: Show "Already a template" indicator
  
### 8. AI Generation Studio Buttons
#### Generate Button
- **Name**: AIGenerate
- **Location**: AI generation studio primary action
- **Permission**: Users with AI generation credits/access
- **Action**: Start AI generation process with current settings
- **API Called**: `POST /api/v2/ai/generate`
- **Database Action**: Create generation job record, deduct credits
- **Loading State**: Disable button, show progress spinner
- **Success State**: Transition to results view, start polling
- **Failure State**: Show error with specific reason (quota, invalid prompt, etc.)
- **Toast Message**: "Generation started" or error message
- **Modal**: None (stays in studio, shows results area)
- **redirect**: None
- **analytics**: `ai_generation_started_[JOB_ID]`
- **audit log**: `AI_GENERATION_STARTED` (with job ID, user ID, model, credits used)
- **edge cases**:
  - Insufficient credits: Show upgrade/purchase modal
  - Invalid prompt: Highlight problematic sections
  - Model unavailable: Show estimated time until available
  
#### Stop Generation Button
- **Name**: AIGenerateStop
- **Location**: AI generation studio (replaces Generate during process)
- **Permission**: Users who started the generation
- **Action**: Cancel ongoing AI generation process
- **API Called**: `DELETE /api/v2/ai/generate/{jobId}`
- **database action**: Update job status to cancelled, refund credits (partial)
- **loading state**: None
- **success state**: Return to idle state, enable Generate button
- **failure state**: Show error if unable to cancel
- **toast message**: "Generation cancelled"
- **modal**: None
- **redirect**: None
- **analytics**: `ai_generation_stopped_[JOB_ID]`
- **audit log**: `AI_GENERATION_CANCELLED` (with job ID, user ID, reason)
- **edge cases**:
  - Already completed/failed: Button hidden
  
#### Refresh Results Button
- **Name**: AIResultsRefresh
- **Location**: AI generation studio results header
- **permission**: Users who initiated generation
- **action**: Manually check generation status
- **api called**: `GET /api/v2/ai/generate/{jobId}`
- **database action**: Read job status, update UI
- **loading state**: Show spinner in button during request
- **success state**: Update results display based on latest status
- **failure state**: Show error if unable to fetch status
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `ai_results_refreshed_[JOB_ID]`
- **audit log**: None
- **edge cases**:
  - Already complete: No action needed
  
#### Generate Variations Button
- **Name**: AIVariations
- **location**: Action menu on generated result item
- **permission**: Users who own the generation result
- **action**: Create variations based on selected result
- **api called**: `POST /api/v2/ai/generate` (with parent job ID as reference)
- **database action**: Create new generation job record
- **loading state**: Show spinner during request
- **success state**: Transition to generation studio with pre-filled settings
- **failure state**: Show error if unable to start variations
- **toast message**: "Variation generation started"
- **modal**: None
- **redirect**: None
- **analytics**: `ai_variation_started_[PARENT_JOB_ID]_[NEW_JOB_ID]`
- **audit log**: `AI_GENERATION_STARTED` (as variation job)
- **edge cases**:
  - No generations: Button hidden
  
#### Remix Button
- **name**: AIRemix
- **location**: Action menu on generated result item
- **permission**: Users who own the generation result
- **action**: Open generation studio with result as reference
- **api called**: None (client-side state transfer)
- **database action**: None
- **loading state**: None
- **success state**: Generation studio opens with result loaded as reference
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `ai_result_remixed_[RESULT_ID]`
- **audit log**: None
- **edge cases**:
  - Different model required: May auto-switch or prompt for selection
  
#### Download Result Button
- **name**: AIDownloadResult
- **location**: Action menu on generated result item
- **permission**: Users who own the generation result
- **action**: Download generated media file
- **api called**: `GET /api/v2/ai/generate/{jobId}/output`
- **database action**: Log download, update job completion metrics
- **loading state**: Show progress during preparation
- **success state**: Initiate browser download
- **failure state**: Show error if output unavailable
- **toast message**: "Download started"
- **modal**: Progress dialog for large files
- **redirect**: None (browser download)
- **analytics**: `ai_result_downloaded_[JOB_ID]`
- **audit log**: `AI_RESULT_DOWNLOADED` (with job ID, user ID, size)
- **edge cases**:
  - Processing: Show estimated time until ready
  
#### Delete Result Button
- **name**: AIDeleteResult
- **location**: Action menu on generated result item
- **permission**: Users who own the generation result
- **action**: Delete generated media file
- **api called**: `DELETE /api/v2/ai/generate/{jobId}`
- **database action**: Update job status to deleted, clean storage
- **loading state**: Show spinner during deletion
- **success state**: Remove result from gallery
- **failure state**: Show error if deletion fails
- **toast message**: "Generation result deleted"
- **modal**: Confirmation dialog
- **redirect**: None
- **analytics**: `ai_result_deleted_[JOB_ID]`
- **audit log**: `AI_RESULT_DELETED` (with job ID, user ID)
- **edge cases**:
  - Already deleted: Button hidden
  
#### Use Prompt Template Button
- **name**: AIPromptTemplateUse
- **location**: Prompt template gallery or insertion menu
- **permission**: All authenticated users with template access
- **action**: Insert selected prompt template at cursor position
- **api called**: None (client-side)
- **database action**: None
- **loading state**: None
- **success state**: Template text inserted at cursor position
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `ai_prompt_template_used_[TEMPLATE_ID]`
- **audit log**: None
- **edge cases**:
  - No selection: Insert at end of current prompt
  
#### Save as Prompt Template Button
- **name**: AIPromptTemplateSave
- **location**: Action menu on prompt editor or prompt history item
- **permission**: Users with template creation rights
- **action**: Save current prompt or selection as new template
- **api called**: `POST /api/v2/ai/prompt-templates`
- **database action**: Create prompt template record
- **loading state**: Show spinner during request
- **success state**: Template appears in template library
- **failure state**: Show error if creation fails (duplicate, etc.)
- **toast message**: "Prompt template saved"
- **modal**: Template creation confirmation
- **redirect**: None
- **analytics**: `ai_prompt_template_saved_[NEW_TEMPLATE_ID]`
- **audit log**: `PROMPT_TEMPLATE_CREATED` (with user ID)
- **edge cases**:
  - Duplicate name: Suggest alternatives with timestamp or hash
  
### 9. Review & Approval Workflow Buttons
#### Add Comment Button
- **name**: ReviewAddComment
- **location**: Review toolbar and timeline context menu
- **permission**: Project members with comment rights
- **action**: Start comment creation at current playhead position
- **api called**: None (client-side state)
- **database action**: None
- **loading state**: None
- **success state**: Show comment input box at timeline position
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `review_comment_started_[TIMECODE]`
- **audit log**: None
- **edge cases**:
  - Playing media: May pause or continue based on settings
  
#### Submit Comment Button
- **name**: ReviewCommentSubmit
- **location**: Comment input toolbar
- **permission**: Project members with comment rights
- **action**: Submit comment at specified timestamp/range
- **api called**: `POST /api/v2/comments` (with project ID, timestamp, text)
- **database action**: Create comment record, update activity feed
- **loading state**: Show spinner during request
- **success state**: Clear input, show comment in thread
- **failure state**: Show validation error or submission failure
- **toast message**: "Comment added"
- **modal**: None
- **redirect**: None
- **analytics**: `review_comment_submitted_[COMMENT_ID]`
- **audit log**: `COMMENT_CREATED` (with comment ID, project ID, timestamp)
- **edge cases**:
  - Empty comment: Show "Comment cannot be empty" validation
  
#### Reply to Comment Button
- **name**: ReviewCommentReply
- **location**: Comment action menu (hover/swipe)
- **permission**: Project members with comment rights
- **action**: Reply to specific comment
- **api called**: `POST /api/v2/comments/{parentId}/reply`
- **database action**: Create reply record, link to parent comment
- **loading state**: Show spinner during request
- **success state**: Show reply indented under parent comment
- **failure state**: Show error if parent not found or permission denied
- **toast message**: "Reply added"
- **modal**: None
- **redirect**: None
- **analytics**: `comment_reply_submitted_[REPLY_ID]`
- **audit log**: `COMMENT_REPLIED` (with reply ID, parent ID)
- **edge cases**:
  - Self-reply: May be prevented or show warning
  
#### Resolve Comment Button
- **name**: ReviewCommentResolve
- **location**: Comment action menu
- **permission**: Project members with resolve rights (editors, approvers)
- **action**: Mark comment as resolved
- **api called**: `PATCH /api/v2/comments/{id}` (with status: resolved)
- **database action**: Update comment status, check thread resolution
- **loading state**: Show spinner during request
- **success state**: Update comment UI to resolved state
- **failure state**: Show error if unable to update
- **toast message**: "Comment resolved"
- **modal**: None
- **redirect**: None
- **analytics**: `comment_resolved_[COMMENT_ID]`
- **audit log**: `COMMENT_RESOLVED` (with comment ID)
- **edge cases**:
  - Already resolved: No visual change
  
#### Reopen Comment Button
- **name**: ReviewCommentReopen
- **location**: Comment action menu (when resolved)
- **permission**: Project members with resolve rights
- **action**: Mark comment as open again
- **api called**: `PATCH /api/v2/comments/{id}` (with status: open)
- **database action**: Update comment status to open
- **loading state**: Show spinner during request
- **success state**: Update comment UI to open state
- **failure state**: Show error if unable to update
- **toast message**: "Comment reopened"
- **modal**: None
- **redirect**: None
- **analytics**: `comment_reopened_[COMMENT_ID]`
- **audit log**: `COMMENT_REOPENED` (with comment ID)
- **edge cases**:
  - Already open: No visual change
  
#### Like/Dislike Comment Button
- **name**: CommentLikeDislike
- **location**: Comment action menu
- **permission**: All authenticated users (may be limited by org policy)
- **action**: Toggle like/dislike on comment
- **api called**: `POST /api/v2/comments/{id}/reaction`
- **database action**: Update reaction count, track user reaction
- **loading state**: Show spinner during request
- **success state**: Toggle liked/disliked state
- **failure state**: Show error if unable to update
- **toast message**: "Reaction added"/"Reaction removed"
- **modal**: None
- **redirect**: None
- **analytics**: `comment_reaction_toggled_[COMMENT_ID]_[TYPE]`
- **audit log**: `COMMENT_REACTION_TOGGLED` (with comment ID, user ID, type)
- **edge cases**:
  - Already reacted: Toggle state (like→dislike→none→like)
  
#### Request Changes Button
- **name**: ReviewRequestChanges
- **location**: Review resolution controls
- **permission**: Project members with review rights (approvers, owners)
- **action**: Request changes to the project with explanation
- **api called**: `PATCH /api/v2/projects/{id}/review` (with action: request_changes)
- **database action**: Update project review status, create audit log
- **loading state**: Show spinner during request
- **success state**: Update review status UI, notify project owner
- **failure state**: Show error if unable to update
- **toast message**: "Changes requested"
- **modal**: Explanation required dialog
- **redirect**: None
- **analytics**: `review_request_changes_[PROJECT_ID]`
- **audit log**: `PROJECT_REVIEW_REQUESTED_CHANGES` (with project ID, user ID)
- **edge cases**:
  - Already in changes requested: Show current status with explanation
  
#### Approve Button
- **name**: ReviewApprove
- **location**: Review resolution controls (primary action)
- **permission**: Project members with approval rights
- **action**: Approve project as final
- **api called**: `PATCH /api/v2/projects/{id}/review` (with action: approve)
- **database action**: Update project status to approved, create audit log
- **loading state**: Show spinner during request
- **success state**: Update UI to approved state, show confetti (optional)
- **failure state**: Show error if unable to update
- **toast message**: "Project approved"
- **modal**: Optional comments dialog
- **redirect**: None
- **analytics**: `review_approved_[PROJECT_ID]`
- **audit log**: `PROJECT_APPROVED` (with project ID, user ID)
- **edge cases**:
  - Already approved: Show current status with timestamp
  
#### Reset to Review Button
- **name**: ReviewResetToReview
- **location**: Review resolution controls
- **permission**: Project members with review rights
- **action**: Return project to needs review state
- **api called**: `PATCH /api/v2/projects/{id}/review` (with action: reset_to_review)
- **database action**: Update project status to needs review
- **loading state**: Show spinner during request
- **success state**: Update UI to needs review state
- **failure state**: Show error if unable to update
- **toast message**: "Returned to review"
- **modal**: None
- **redirect**: None
- **analytics**: `review_reset_to_review_[PROJECT_ID]`
- **audit log**: `PROJECT_RESET_TO_REVIEW` (with project ID, user ID)
- **edge cases**:
  - Already needs review: No visual change
  
#### Compare Versions Button
- **name**: ReviewCompareVersions
- **location**: Review toolbar or version history menu
- **permission**: Project members with view access
- **action**: Open version comparison view
- **api called**: None (client-side navigation)
- **database action**: None
- **loading state**: None
- **success state**: Display version comparison interface
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: `/app/projects/{id}/compare`
- **analytics**: `review_compare_versions_opened`
- **audit log**: None
- **edge cases**:
  - Only one version: Show tooltip "No other versions to compare"
  
#### Version History Button
- **name**: ReviewVersionHistory
- **location**: Review toolbar
- **permission**: Project members with view access
- **action**: Open version history panel
- **api called**: None (client-side)
- **database action**: None
- **loading state**: None
- **success state**: Show version history sidebar
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `review_version_history_opened`
- **audit log**: None
- **edge cases**:
  - No history: Show empty state with guidance
  
### 10. Export & Delivery Buttons
#### Start Export Button
- **name**: ExportStart
- **location**: Export configuration dialog primary action
- **permission**: Users with export rights on project
- **action**: Start export process with current settings
- **api called**: `POST /api/v2/exports` (with project ID and settings)
- **database action**: Create export job record, set status to queued
- **loading state**: Disable button, show progress spinner
- **success state**: Show queue position with estimated start time
- **failure state**: Show error with specific reason (settings invalid, quota, etc.)
- **toast message**: "Export queued"
- **modal**: None (stays in dialog, shows queue info)
- **redirect**: None
- **analytics**: `export_started_[JOB_ID]`
- **audit log**: `EXPORT_STARTED` (with job ID, user ID, project ID)
- **edge cases**:
  - Quota exceeded: Show storage management options
  
#### Cancel Export Button
- **name**: ExportCancel
- **location**: Export queue item or dialog (replaces Start during process)
- **permission**: Users who started the export or admins
- **action**: Cancel queued or processing export job
- **api called**: `DELETE /api/v2/exports/{jobId}`
- **database action**: Update export job status to cancelled
- **loading state**: None
- **success state**: Remove from queue or show as cancelled
- **failure state**: Show error if unable to cancel
- **toast message**: "Export cancelled"
- **modal**: None (unless batch with progress)
- **redirect`: None
- **analytics`: `export_cancelled_[JOB_ID]`
- **audit log`: `EXPORT_CANCELLED` (with job ID, user ID)
- **edge cases**:
  - Already completed/failed: Button hidden
  
#### Retry Export Button
- **name**: ExportRetry
- **location**: Export queue item (for failed exports)
- **permission**: Users who own the export or admins
- **action**: Retry failed export job with same settings
- **api called**: `POST /api/v2/exports/{jobId}/retry`
- **database action**: Reset job status to queued, prepare for retry
- **loading state**: Show spinner during request
- **success state**: Job returns to queue with same position
- **failure state**: Show error if unable to retry
- **toast message**: "Export retried"
- **modal**: None
- **redirect**: None
- **analytics**: `export_retried_[JOB_ID]`
- **audit log`: `EXPORT_RETRY` (with job ID, user ID)
- **edge cases**:
  - Not in failed state: Button hidden
  
#### View Logs Button
- **name**: ExportViewLogs
- **location**: Export queue item or details view
- **permission**: Users who own the export or admins
- **action**: View detailed logs for export job
- **api called**: `GET /api/v2/exports/{jobId}/logs`
- **database action**: Read job log records
- **loading state**: Show spinner during log fetch
- **success state**: Display logs view
- **failure state**: Show error if logs unavailable
- **toast message**: None
- **modal**: Logs view dialog
- **redirect**: None
- **analytics**: `export_logs_viewed_[JOB_ID]`
- **audit log`: None
- **edge cases**:
  - No logs: Show empty state with guidance
  
#### Download Export Button
- **name**: ExportDownload
- **location**: Export queue item (when completed)
- **permission**: Users who own the export
- **action**: Download exported file to local device
- **api called**: `GET /api/v2/exports/{jobId}/download`
- **database action**: Log download, update job completion metrics
- **loading state**: Show progress during preparation
- **success state**: Initiate browser download
- **failure state**: Show error if file unavailable
- **toast message**: "Download started"
- **modal**: Progress dialog for large files
- **redirect**: None (browser download)
- **analytics**: `export_downloaded_[JOB_ID]`
- **audit log`: `EXPORT_DOWNLOADED` (with job ID, user ID, size)
- **edge cases**:
  - Not completed: Button hidden or shows estimated time
  
#### Share Export Button
- **name**: ExportShare
- **location**: Export queue item or details view
- **permission**: Users with share rights on export
- **action**: Share exported file via link or integration
- **api called**: None (varies by method)
- **database action**: Create share record or call external API
- **loading state**: Show spinner during share preparation
- **success state**: Share initiated successfully
- **failure state**: Show error if sharing fails
- **toast message**: "Shared via [method]"
- **modal**: Method-specific dialog (email, link, integration)
- **redirect**: None (unless external redirect)
- **analytics**: `export_shared_[JOB_ID]_[METHOD]`
- **audit log`: `EXPORT_SHARED` (with job ID, user ID, method)
- **edge cases**:
  - Already shared: May show existing links or resend option
  
### 11. Settings Buttons
#### Save Settings Button
- **name**: SettingsSave
- **location**: Settings dialog footer (primary action)
- **permission**: Users with rights to modify settings being edited
- **action**: Save current settings changes
- **api called**: `PATCH /api/v2/settings/[section]` (various endpoints)
- **database action**: Update settings records
- **loading state**: Show spinner during save process
- **success state**: Close settings dialog, apply changes immediately
- **failure state**: Show validation errors or save failure
- **toast message**: "Settings saved"
- **modal**: None (unless validation errors)
- **redirect**: None
- **analytics**: `settings_saved_[SECTION]`
- **audit log`: `SETTINGS_UPDATED` (with section, user ID, changes)
- **edge cases**:
  - No changes: Button disabled or shows "No changes to save"
  
#### Reset to Defaults Button
- **name**: SettingsReset
- **location**: Settings dialog footer (secondary action)
- **permission**: Users with rights to modify settings
- **action**: Reset current section to system defaults
- **api called**: `DELETE /api/v2/settings/[section]` or `PUT` with defaults
- **database action**: Reset settings to default values
- **loading state**: None
- **success state**: Form fields reset to default values
- **failure state**: Show error if reset fails
- **toast message**: "Settings reset to defaults"
- **modal**: Confirmation dialog (especially for security settings)
- **redirect**: None
- **analytics**: `settings_reset_[SECTION]`
- **audit log`: `SETTINGS_RESET_TO_DEFAULTS` (with section, user ID)
- **edge cases**:
  - Already at defaults: Button disabled
  
#### Cancel Settings Button
- **name**: SettingsCancel
- **location**: Settings dialog footer (next to save)
- **permission**: All users accessing settings
- **action**: Discard changes and close settings dialog
- **api called**: None
- **database action**: None
- **loading state**: None
- **success state**: Close dialog without saving changes
- **failure state**: None
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `settings_cancelled`
- **audit log`: None
- **edge cases**:
  - Unsaved changes: May show confirmation if changes detected
  
#### Toggle Setting Button
- **name**: SettingsToggle_[SETTING_NAME]
- **location**: Settings form (checkbox/toggle switch)
- **permission**: Users with rights to modify this setting
- **action**: Toggle boolean setting value
- **api called**: `PATCH /api/v2/settings/[section]` (with specific field)
- **database action**: Update specific setting field
- **loading state**: None
- **success state**: Toggle switch state updated immediately
- **failure state**: Show error if toggle fails
- **toast message**: None
- **modal**: None
- **redirect**: None
- **analytics**: `setting_toggled_[SECTION]_[FIELD]_[NEW_VALUE]`
- **audit log`: `SETTING_UPDATED` (with section, field, user ID, old value, new value)
- **edge cases**:
  - Read-only setting: Button hidden or disabled
  
### 12. Help & Support Buttons
#### Search Help Button
- **name**: HelpSearch
- **location**: Help center header
- **permission**: All users (may be rate limited)
- **action**: Search knowledge base for articles
- **api called**: `GET /api/v2/help/search` (with query parameters)
- **database action**: Search help articles table
- **loading state**: Show spinner in search box during request
- **success state**: Display search results
- **failure state**: Show error or no results message
- **toast message**: None
- **modal**: None
- **redirect**: `/app/help/search?[query]`
- **analytics**: `help_search_performed_[QUERY_HASH]`
- **audit log`: None
- **edge cases**:
  - Empty query: Show placeholder or recent searches
  
#### View Article Button
- **name**: HelpArticleView
- **location**: Help search results or category listings
- **permission**: All users
- **action**: Open help article for reading
- **api called**: `GET /api/v2/help/articles/{id}`
- **database action**: Read help article record
- **loading state`: Show skeleton during load
- **success state`: Display article content
- **failure state`: Show error if article not found
- **toast message`: None
- **modal`: None (unless in app, then full screen view)
- **redirect`: `/app/help/articles/{id}`
- **analytics`: `help_article_viewed_[ID]`
- **audit log`: None
- **edge cases`:
  - Offline: Show cached version with stale indicator
  
#### Mark Helpful Button
- **name**: HelpFeedbackHelpful
- **location**: Article footer (positive feedback)
- **permission**: All users who viewed article
- **action**: Mark article as helpful
- **api called**: `POST /api/v2/help/articles/{id}/feedback` (with rating: helpful)
- **database action`: Update helpful count, track user feedback
- **loading state`: Show spinner during request
- **success state`: Update helpful count display
- **failure state`: Show error if unable to record feedback
- **toast message`: "Thanks for your feedback!"
- **modal`: None
- **redirect`: None
- **analytics`: `help_feedback_given_[ID]_[HELPFUL]`
- **audit log`: `HELP_FEEDBACK_GIVEN` (with article ID, user ID, rating)
- **edge cases`:
  - Already voted: May show current vote with option to change
  
#### Mark Not Helpful Button
- **name**: HelpFeedbackNotHelpful
- **location**: Article footer (negative feedback)
- **permission**: All users who viewed article
- **action**: Mark article as not helpful
- **api called**: `POST /api/v2/help/articles/{id}/feedback` (with rating: not_helpful)
- **database action`: Update not_helpful count, track user feedback
- **loading state`: Show spinner during request
- **success state`: Update not_helpful count display
- **failure state`: Show error if unable to record feedback
- **toast message`: "Thanks for your feedback! We'll improve this article."
- **modal`: None
- **redirect`: None
- **analytics`: `help_feedback_given_[ID]_[NOT_HELPFUL]`
- **audit log`: `HELP_FEEDBACK_GIVEN` (with article ID, user ID, rating)
- **edge cases`:
  - Already voted: May show current vote with option to change
  
#### Contact Support Button
- **name**: HelpContactSupport
- **location**: Help center footer or error states
- **permission**: All users
- **action**: Open support contact options
- **api called**: None
- **database action`: None
- **loading state`: None
- **success state`: Display support options (chat, email, phone, ticket)
- **failure state`: None
- **toast message`: None
- **modal`: Support contact dialog
- **redirect`: None
- **analytics`: `help_contact_support_initiated`
- **audit log`: None
- **edge cases`:
  - Outside support hours: Show next available time
  
#### Start Live Chat Button
- **name**: HelpLiveChatStart
- **location**: Support contact options
- **permission**: All users
- **action**: Initiate live chat session with support agent
- **api called**: `POST /api/v2/support/chat` (to request session)
- **database action`: Create chat session record
- **loading state`: Show spinner during request
- **success state`: Open chat interface with agent
- **failure state`: Show error if unable to start chat
- **toast message`: "Connecting to support..."
- **modal`: Live chat interface
- **redirect`: None
- **analytics`: `help_live_chat_started`
- **audit log`: `LIVE_CHAT_STARTED` (with user ID)
- **edge cases`:
  - Agents unavailable: Show estimated wait time or alternative
  
#### Submit Ticket Button
- **name**: HelpTicketSubmit
- **location**: Support ticket form
- **permission**: All users
- **action**: Submit support ticket for tracking
- **api called**: `POST /api/v2/support/tickets`
- **database action`: Create ticket record with initial message
- **loading state`: Show spinner during submission
- **success state`: Show ticket confirmation with ticket number
- **failure state`: Show validation errors or submission failure
- **toast message`: "Ticket submitted successfully"
- **modal`: None (unless validation errors)
- **redirect`: `/app/support/tickets/{ticketId}`
- **analytics`: `help_ticket_submitted_[TICKETID]`
- **audit log`: `SUPPORT_TICKET_CREATED` (with ticket ID, user ID)
- **edge cases`:
  - Duplicate issue: May suggest existing ticket or KB article
  
### 13. Specialized Workflow Buttons
#### Brand Approval Button
- **name**: BrandApproval
- **location**: Brand management workflow
- **permission**: Brand managers and above
- **action**: Approve asset for brand use
- **api called**: `POST /api/v2/assets/{id}/brand-approval`
- **database action`: Update asset brand approval status
- **loading state`: Show spinner during request
- **success state`: Asset marked as brand approved
- **failure state`: Show error if unable to update
- **toast message`: "Asset approved for brand use"
- **modal`: None
- **redirect`: None
- **analytics`: `asset_brand_approved_[ID]`
- **audit log`: `ASSET_BRAND_APPROVED` (with asset ID, user ID)
- **edge cases`:
  - Already approved: No visual change
  
#### Localization Request Button
- **name**: LocalizationRequest
- **location**: Asset action menu in localization workflow
- **permission**: Project managers and above
- **action**: Request localization/translation of asset
- **api called`: `POST /api/v2/localization/requests`
- **database action`: Create localization request record
- **loading state`: Show spinner during request
- **success state`: Request queued for localization team
- **failure state`: Show error if unable to create request
- **toast message`: "Localization requested"
- **modal`: Localization request details form
- **redirect`: None
- **analytics`: `localization_requested_[ASSET_ID]`
- **audit log`: `LOCALIZATION_REQUESTED` (with asset ID, user ID)
- **edge cases`:
  - Already requested: Show current status with ETA
  
#### Accessibility Check Button
- **name**: AccessibilityCheck
- **location**: Export settings or review toolbar
- **permission**: All users with view access
- **action**: Run accessibility analysis on current project
- **api called`: `POST /api/v2/accessibility/check` (with project ID)
- **database action`: None (reads project data)
- **loading state`: Show spinner during analysis
- **success state`: Display accessibility report
- **failure state`: Show error if analysis fails
- **toast message`: "Accessibility check completed"
- **modal`: Accessibility report dialog
- **redirect`: None
- **analytics`: `accessibility_check_run_[PROJECT_ID]`
- **audit log`: `ACCESSIBILITY_CHECK_COMPLETED` (with project ID)
- **edge cases`:
  - Already run recently: Show cached results with timestamp
  
#### Legal Review Button
- **name**: LegalReviewRequest
- **location**: Asset action menu or project toolbar
- **permission**: Legal reviewers and above
- **action**: Send asset/project for legal review
- **api called`: `POST /api/v2/legal/review/request`
- **database action`: Create legal review request record
- **loading state`: Show spinner during request
- **success state`: Request queued for legal team
- **failure state`: Show error if unable to create request
- **toast message`: "Legal review requested"
- **modal`: Legal review details form
- **redirect`: None
- **analytics`: `legal_review_requested_[TARGET_ID]`
- **audit log`: `LEGAL_REVIEW_REQUESTED` (with target ID, user ID)
- **edge cases`:
  - Already requested: Show current status with estimator
  
### Button State Specifications

#### Default State
- **Appearance**: Normal colors, no elevation change
- **Interaction**: Ready for user input
- **Use Case**: Button visible and enabled

#### Hover State
- **Appearance**: 
  - Primary: Slightly darker background (#1D4ED8 from #2563EB)
  - Secondary: Slightly darker border (#6D28D9 from #7C3AED)
  - Tertiary: Text color change (#1D4ED8 from #6B7280)
  - Background change on containment: rgba(37, 99, 235, 0.08)
- **Interaction**: Cursor changes to pointer
- **Use Case**: User hovering with mouse

#### Focus State
- **Appearance**: 
  - Outline: 2px solid #2563EB (primary) or #7C3AED (secondary)
  - Offset: 2px from button edge
  - May include inner shadow or glow
- **Interaction**: Keyboard focus indicator
- **Use Case**: User navigating with keyboard (Tab key)

#### Active/Pressed State
- **Appearance**: 
  - Primary: Darker background (#1E40AF from #2563EB)
  - Secondary: Inverted colors on some platforms
  - Tertiary: Slightly darker text
  - Scale: 95% scale down (subtle press effect)
- **Interaction**: Button appears pressed
- **Use Case**: Mouse button down or spacebar/enter activated

#### Disabled State
- **Appearance**: 
  - Background: #F3F4F6 (gray 100)
  - Border: #E5E7EB (gray 200) for outlined
  - Text: #9CA3AF (gray 500)
  - Icon: #9CA3AF (gray 500)
  - Opacity: May be reduced to 50-60%
- **Interaction**: 
  - No cursor change
  - Ignores click/keyboard events
  - May show tooltip on hover explaining why disabled
- **Use Case**: Button temporarily unavailable due to:
  - Insufficient permissions
  - Invalid state (no selection, incomplete form)
  - Resource limits (quota exceeded, rate limited)
  - Dependencies not met (must select item first)

#### Loading State
- **Appearance**:
  - Text hidden, replaced with spinner
  - Spinner: 16px or 20px size, currentColor
  - Button maintains same dimensions
  - May show progressive text: "Saving...", "Exporting..."
- **Interaction**:
  - Ignores further clicks
  - May show cancel option (changes to cancel button)
  - Pointer may change to not-allowed or remain default
- **Use Case**: Button awaiting asynchronous operation completion

#### Success State
- **Appearance**:
  - Brief visual feedback: checkmark icon replaces text
  - Background: Success color at 10% opacity
  - Border: Success color
  - Duration: 1500ms then returns to default or advances state
- **Interaction**:
  - Temporarily disabled during animation
  - May auto-advance to next step
- **Use Case**: Successful completion of action

#### Error State
- **Appearance**:
  - Background: Error color at 10% opacity
  - Border: Error color
  - May shake or pulse slightly
  - Error message appears below or in tooltip
- **Interaction**:
  - Returns to default state after timeout or user action
  - May show retry button alongside
- **Use Case**: Action failed due to:
  - Validation errors
  - Service unavailable
  - Permission denied
  - Conflict with existing state

### Size Variants
- **Icon Only**:
  - Small: 24x24px (toolbar compacts)
  - Medium: 32x32px (standard toolbar)
  - Large: 40x40px (prominent actions)
  - Extra Large: 48x48px (floating action buttons)
  
- **Icon + Text**:
  - Small: 24px height, auto width (min 80px)
  - Medium: 32px height, auto width (min 100px)
  - Large: 40px height, auto width (min 120px)
  - Extra Large: 48px height, auto width (min 140px)
  
- **Text Only**:
  - Small: 24px height, auto width (min 64px)
  - Medium: 32px height, auto width (min 80px)
  - Large: 40px height, auto width (min 96px)
  - Extra Large: 48px height, auto width (min 112px)

### Special Button Types
#### Floating Action Button (FAB)
- **Use Case**: Primary promoted action on screen
- **Appearance**: 
  - Circular: 56x56px or 64x64px
  - Elevation: Higher than surrounding elements
  - Position: Fixed bottom-right (with safe area consideration)
  - Icon Only: Typically uses primary brand color
- **Behavior**:
  - Morphs into speed dial on long press (reveals related actions)
  - Transforms during scroll (hides/shows based on direction)
  - Hero animation when navigating between screens
- **Examples**:
  - New Project FAB on dashboard
  - New Asset FAB in asset library
  - AI Generate FAB in generation studio

#### Speed Dial Button
- **Use Case**: Reveals related actions from FAB
- **Appearance**:
  - Circular: 48x48px
  - Arranged in arc or grid above FAB
  - Label: May show on long press or hover
  - Background: Secondary or tertiary color
- **Behavior**:
  - Reveals on FAB long press or specific gesture
  - Hides after action selection or timeout
  - May have subtle scale animation
- **Examples**:
  - From New Project FAB: Upload Media, Import from Camera, New Folder
  - From AI Generate FAB: Text-to-Video, Image-to-Video, Audio Generation

#### Toggle Button
- **Use Case**: Binary state switching
- **Appearance**:
  - Pill shape or rounded rectangle
  - Left/right or on/off indication
  - Background changes with state
  - Thumb or indicator moves with state
- **Examples**:
  - Play/Pause (complex state, not simple toggle)
  - Visibility toggles (tracks, layers)
  - Lock toggles
  - Mute/solo toggles
  - Snapping toggles

#### Segmented Control
- **Use Case**: Mutually exclusive options (typically 2-5 choices)
- **Appearance**:
  - Grouped buttons with shared borders
  - Selected state: Filled background
  - Unselected state: Outline only
  - Consistent height and padding
- **Examples**:
  - View mode (Grid/List/Column)
  - Timeline zoom presets
  - Audio waveform types (Peak/RMS/Spectral)
  - Marker types (Chapter/Comment/Edit)

#### Dropdown Button
- **Use Case**: Opening a list of options
- **Appearance**:
  - Text label with downward chevron
  - Background: Usually transparent or container color
  - Border: May show on hover/focus
- **Behavior**:
  - Shows options panel on click/tap
  - May show selected value when closed
  - Supports search/filter for long lists
  - May allow custom input (combobox)
- **Examples**:
  - Model selector in AI studio
  - Resolution presets in export
  - Font family selector
  - Language selector
  - Timezone selector

#### Button Group
- **Use Case**: Related actions that benefit from visual grouping
- **Appearance**:
  - Buttons touching with shared borders
  - First button: Left border radius
  - Middle buttons: No border radius
  - Last button: Right border radius
  - Consistent height
- **Examples**:
  - Undo/Redo group
  - Zoom controls
  - Playback controls
  - Color correction wheels
  - Transformation gizmos

### Accessibility Specifications
#### Keyboard Navigation
- **Tab Order**: Logical sequence following visual flow
- **Focus Indicator**: 2px solid #2563EB with 2px offset
- **Activation**: 
  - Enter/Space: Activate button
  - Arrow keys: Navigate within groups (radio, tab groups)
  - Escape: Cancel action or close dropdown/menu
- **Shortcuts**:
  - Documented in tooltips (e.g., "G" for new project)
  - Customizable in advanced settings
  - Reserved for common actions (Ctrl+Z/Y, Ctrl+S, etc.)

#### Screen Reader Support
- **Labels**: Every button has accessible label
  - Visible text: Used directly
  - Icon-only: Aria-label describes action
  - Contextual: May change based on state (Play/Pause)
- **States**: 
  - Disabled: Announced as disabled
  - Selected: Announced as selected (for toggle buttons)
  - Expanded/collapsed: For menu buttons
- **Groups**: 
  - Fieldset/legend for related radio buttons
  - ARIA-label for button groups
  - Menu role for context menus

#### Touch Target Specifications
- **Minimum Size**: 44x44pt iOS, 48x48dp Android
- **Recommended Size**: 48x48px for primary actions
- **Spacing**: Minimum 8px between touch targets
- **Thumb Zone**: Consider primary actions in easy-to-reach areas
- **Tablet Optimization**: May increase size for precision tasks

#### Motion and Animation
- **Reduced Motion**: 
  - Respects prefers-reduced-motion media query
  - Substitutes animation with instant state changes
  - Preserves feedback mechanisms (color change, etc.)
- **Animation Duration**:
  - Entrance: 100-200ms
  - Exit: 75-150ms
  - Feedback: 50-100ms
  - Transition: 150-250ms
- **Easing Functions**:
  - Standard: ease-in-out for most transitions
  - Entrance: ease-out
  - Exit: ease-in
  - Feedback: linear or ease-in-out
- **Performance**:
  - Maintains 60fps when possible
  - Uses transform and opacity for GPU acceleration
  - Avoids layout thrashing
  - Requests animation frame for synchronization

### Localization Considerations
- **Text Expansion**: 
  - German: Up to 35% longer than English
  - Finnish: Up to 50% longer
  - Japanese: May require vertical layout options
  - Arabic/Hebrew: Right-to-left layout support
- **Icon Universality**:
  - Prefer universally recognized symbols
  - Provide text labels for ambiguous icons
  - Consider cultural differences in symbol interpretation
- **RTL Support**:
  - Mirror horizontally asymmetric icons
  - Adjust padding and spacing
  - Ensure proper text alignment
  - Test with actual Arabic/Hebrew content
- **Date/Time Formats**:
  - Respect locale-specific formats
  - Use ISO 8601 for machine-readable dates
  - Provide both relative and absolute timestamps

### Platform-Specific Considerations
#### Web
- **Cursor Pointers**: 
  - Default: pointer for clickable
  - Text-select: text for editable regions
  - Move: grabbing/grabbed for drag operations
  - Not-allowed: for disabled states
- **Keyboard Events**:
  - Prevent default for spacebar on buttons (to prevent scrolling)
  - Handle keydown/keyup for repeat prevention
  - Support modifier combinations (Ctrl, Shift, Alt, Meta)
#### Mobile (iOS/Android)
- **Native Feel**:
  - Use platform-standard button styles where appropriate
  - Respect platform navigation patterns (back gesture, etc.)
  - Consider safe areas (notch, home indicator)
  - Platform-specific haptics
- **Touch Events**:
  - Prevent default for touchstart to avoid mouse events
  - Handle touch cancellation (system interruptions)
  - Support multi-touch gestures where appropriate
- **Performance**:
  - Optimize for 60fps on mid-tier devices
  - Consider battery impact of animations
  - Use requestAnimationFrame for synchronization
#### Desktop (Windows/macOS/Linux)
- **Platform Conventions**:
  - Follow platform-specific keyboard shortcuts
  - Respect platform theme settings (dark/light)
  - Use standard dialog patterns
  - Consider menu bar integration
- **Input Methods**:
  - Support mouse, trackpad, touchscreen, stylus
  - Consider precision mice and gaming mice
  - Support voice input where applicable
- **Accessibility**:
  - Follow platform accessibility guidelines
  - Consider high contrast modes
  - Support screen readers and voice control

### Error Handling and Recovery
#### Validation Errors
- **Inline**: 
  - Appear below field or in tooltip
  - Clear and actionable message
  - Uses error color (#EF4444)
- **Modal**:
  - For blocking errors requiring user action
  - Includes primary action to resolve
  - May include secondary actions for alternatives
- **Toast**:
  - For recoverable errors (network blips)
  - Short duration (3000-5000ms)
  - Action-oriented ("Try again", "Check connection")

#### Service Errors
- **5xx Errors**:
  - Show retry option with exponential backoff
  - Display estimated time until recovery
  - Offer alternative actions if available
- **4xx Errors**:
  - Client-side: Validation errors (handled inline)
  - Permission: Show login/upgrade prompts
  - Not Found: Show helpful alternatives or creation options
- **Network Errors**:
  - Show offline queue indicator
  - Offer to save for later
  - Synchronize when connection returns

#### State Conflicts
- **Immutable State**:
  - Show current state with explanation
  - Offer to create new instance instead
- **Race Conditions**:
  - Last-write-wins with timestamp
  - Show conflict resolution dialog when detectable
- **Dependent Actions**:
  - Disable until prerequisites met
  - Show guidance on what's needed first
- **Resource Limits**:
  - Show current usage and limit
  - Offer upgrade or cleanup options
  - Provide estimation of time until reset

### Analytics and Tracking Specifications
#### Click Tracking
- **Event Naming**: `{context}_{action}_{specifics}`
- **Properties**: 
  - `timestamp`: ISO 8601 UTC
  - `user_id`: UUID
  - `session_id`: Session identifier
  - `page_url`: Current page
  - `element_id`: DOM element or component ID
  - `button_type`: primary/secondary/territiary/link
  - **access_method**: mouse/touch/keyboard/voice
- **Examples**:
  - `project_editor_undo_clicked`
  - `asset_library_upload_initiated`
  - `ai_generation_started`
  - `review_comment_submitted`
  - `export_download_completed`

#### Funnel Tracking
- **Creation Funnel**:
  1. New project clicked
  2. Wizard step 1 completed
  3. Wizard step 2 completed
  4. Project created
  5. First asset added
  6. First edit made
- **Generation Funnel**:
  1. AI studio opened
  2. Prompt entered
  3. Settings configured
  4. Generate clicked
  5. Generation completed
  6. Result added to project
- **Export Funnel**:
  1. Export dialog opened
  2. Settings configured
  3. Start export clicked
  4. Export completed
  5. File downloaded
  6. File shared

#### Performance Tracking
- **Button Response**:
  - Time from click to visual feedback
  - Time from click to action completion
  - Frame drops during animation
- **Interaction Quality**:
  - Misclicks (adjacent buttons)
  - Repeated attempts (suggests unclear feedback)
  - Time to complete common tasks

### Implementation Guidelines
#### Component Library Standards
- **API Consistency**:
  - All buttons accept: `onClick`, `disabled`, `loading`, `size`, `variant`
  - Icon buttons accept: `icon` (name or component), `iconPosition` (left/right)
  - Text buttons accept: `children` (text), `href` (for link variant)
  - All buttons support: `aria-label`, `title` (tooltip), `data-testid`
- **State Management**:
  - Internal state for loading, hover, focus, pressed
  - Controlled props override internal state where appropriate
  - Reset to default state when unmounted
- **Accessibility Built-in**:
  - Proper HTML button element (not div/span with role)
  - Correct type attribute (submit, button, reset)
  - Focus management for modal dialogs
  - Return focus to trigger on modal close
- **Performance**:
  - Memoize expensive computations
  - Avoid unnecessary re-renders
  - Use CSS transforms for animations
  - Lazy load icon sets where appropriate

#### Theming and Customization
- **Color Variables**:
  - `--color-primary`: #2563EB
  - `--color-secondary`: #7C3AED
  - `--color-success`: #10B981
  - `--color-warning`: #F59E0B
  - `--color-error`: #EF4444
  - `--color-info`: #06B6D4
  - `--color-background`: #FFFFFF
  - `--color-surface`: #F9FAFB
  - `--color-border`: #E5E7EB
  - `--color-text-primary`: #111827
  - `--color-text-secondary`: #6B7280
- **Radius Variables**:
  - `--radius-none`: 0
  - `--radius-sm`: 0.125rem
  - `--radius-default`: 0.25rem
  - `--radius-md`: 0.375rem
  - `--radius-lg`: 0.5rem
  - `--radius-xl`: 0.75rem
  - `--radius-2xl`: 1rem
  - `--radius-3xl`: 1.5rem
  - `--radius-full`: 9999px
- **Spacing Variables**:
  - Follows standard spacing scale (0.5px increments)
  - Allows for custom spacing systems
- **Shadow Variables**:
  - `--shadow-xs` through `--shadow-2xl`
  - `--shadow-inner`
  - `--shadow-outline` for focus rings
- **Transition Variables**:
  - `--transition-fast`: 75ms
  - `--transition-normal`: 150ms
  - `--transition-slow`: 300ms
  - `--transition-slower`: 500ms

#### Testing Guidelines
- **Unit Tests**:
  - Click handler invocation
  - Disabled state prevents interaction
  - Loading state shows appropriate UI
  - State transitions work correctly
  - Props are properly forwarded to underlying element
- **Integration Tests**:
  - Keyboard navigation works
  - Screen reader announces correctly
  - Touch events handled appropriately
  - Visual regression testing for states
- **Accessibility Tests**:
  - Color contrast ratios
  - Keyboard operable
  - Screen reader friendly
  - Focus visible and logical
  - No trapping in modals or dropdowns
- **Performance Tests**:
  - Render time under threshold
  - Animation maintains 60fps
  - Memory usage stable
  - Event listener cleanup

### Conclusion
This comprehensive button specification ensures that ResearchReel provides a consistent, accessible, and intuitive user interface across all platforms and user contexts. By defining every button's behavior, states, and interactions, we create a foundation for reliable implementation and cohesive user experience.

The specification balances:
- **Consistency**: Similar actions have similar interactions
- **Discoverability**: Common actions are visible and identifiable
- **Efficiency**: Power users can leverage keyboard shortcuts and accelerators
- **Accessibility**: Designed for diverse abilities from the start
- **Feedback**: Clear indication of system state and action outcomes
- **Forgiveness**: Undo/redo, confirmation for destructive actions
- **Performance**: Optimizes for perceived and actual performance

Implementation teams can use this specification to:
1. Ensure UI consistency across all features and platforms
2. Guide accessibility testing and validation
3. Inform automated UI testing strategies
4. Provide clear handoff to design and development teams
5. Maintain consistency as the platform evolves over time