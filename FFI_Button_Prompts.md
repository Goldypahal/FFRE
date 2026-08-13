# FFIRE Button Prompts
## Financial Fraud Investigation Reasoning Engine

### AI Prompt System for Button Actions

The FFIRE system leverages AI assistance to enhance investigator efficiency through context-aware prompts and suggestions attached to button actions. These prompts provide intelligent assistance, reducing cognitive load and ensuring consistent, thorough investigations while maintaining investigator autonomy.

#### Core Principles:
1. **Context-Aware** - Prompts adapt to investigation state, evidence, and user role
2. **Non-Intrusive** - Suggestions appear as optional guidance, not mandates
3. **Action-Oriented** - Focused on facilitating the specific button action being considered
4. **Evidence-Based** - All suggestions reference specific evidence or investigative principles
5. **Role-Appropriate** - Tailored to investigator experience level and permissions
6. **Transparent** - Clear indication when AI is providing suggestions vs. system guidance
7. **Reversible** - All AI suggestions can be accepted, modified, or rejected

#### Implementation Approach:
- **Tooltip-style suggestions** appear on hover/focus of action buttons
- **Modal previews** show potential outcomes before execution
- **In-line suggestions** within forms and dialogs
- **Post-action insights** showing impact of completed actions
- **Learning system** that adapts to investigator acceptance patterns
- **Confidence scoring** for all AI suggestions

### Button-Specific AI Prompts

#### 1. Navigation & Layout Buttons

**New Investigation Button Prompt**
```
Investigation Initiation Assistant:
Based on your recent patterns and current queue:
- Suggested starting point: Transaction ID [similar to recent cases]
- Recommended initial focus: [High-frequency fraud type based on your workload]
- Suggested tags: [Auto-generated based on transaction characteristics]
- Estimated complexity: [Low/Medium/High] based on transaction features
- Similar recent cases: [List of 2-3 similar investigations with outcomes]
Actionable suggestion: "Start with transaction verification, then customer history review"
```

**Resume Investigation Button Prompt**
```
Investigation Continuation Assistant:
Current state analysis:
- Last completed step: [Step name] at [timestamp]
- Pending actions: [List of 2-3 pending automated tasks]
- Evidence gaps: [Specific types of evidence still needed]
- Recommended next focus: [Specific investigation area based on gaps]
- Blocking issues: [Any system or data issues preventing progress]
- Time estimate to completion: [Based on similar cases at this stage]
Actionable suggestion: "Review pending location velocity results before proceeding to knowledge base query"
```

**Pause Investigation Button Prompt**
```
Investigation Pause Assistant:
Pause implications:
- Current progress will be preserved exactly
- Automated processing will pause at current step
- Manual evidence addition remains available
- Timeline continues to update with manual entries
- Recommend pausing for: [Specific reason based on state]
  * Waiting for external response
  * Need for supervisory review
  * Evidence collection required
  * Complexity requiring specialist consultation
Suggested pause duration: [Estimated based on typical resolution time]
```

**Export Investigation Button Prompt**
```
Export Format Advisor:
Based on intended use and investigation contents:
- For legal proceedings: PDF report with chain of custody
- For technical analysis: JSON with full evidence objects  
- For team collaboration: Excel with summary matrices
- For regulatory submission: Standardized SAR format
- Selected evidence count: [number] items
- Recommended format: [Format] with [specific options]
- Estimated file size: [size] 
- Include options: [Recommended inclusions based on use case]
Actionable suggestion: "Select PDF format with timeline included for supervisor review"
```

**Share Investigation Button Prompt**
```
Collaboration Assistant:
Sharing recommendations based on content and recipient roles:
- For supervisors: Summary view with key findings and recommendations
- For specialists: Full evidence access with reasoning trace
- For legal team: Exhibit-ready package with annotations
- For analysts: Working copy with edit permissions
- Suggested recipients based on: [Investigation characteristics]
  * Fraud type: [Specialist team recommendation]
  * Jurisdiction: [Appropriate legal/contact person]
  * Amount: [Escalation path if applicable]
- Access levels: [Recommended permission set]
- Notification preference: [Based on urgency indicators]
Actionable suggestion: "Share with Fraud Specialist Team (View Only) and notify lead investigator"
```

**Add Note Button Prompt**
```
Note-Taking Assistant:
Contextual suggestions based on current view:
- In evidence viewer: "Tag this evidence as relevant/irrelevant with brief rationale"
- In timeline: "Note any timing discrepancies or sequence observations"
- In reasoning graph: "Document assumptions or confidence adjustments for this node"
- General: "Summarize key insight or question for future reference"
- Template suggestion: [Based on note location and recent notes]
  * Evidence assessment: [Template]
  * Procedural note: [Template]
  * Question for follow-up: [Template]
Auto-tag suggestion: [Based on content analysis]
- Recommended tags: [Auto-generated from content analysis]
- Privacy level: [Suggested based on content sensitivity]
Actionable suggestion: "Add note: 'Transaction timing inconsistent with customer travel patterns'"
```

**Escalate Button Prompt**
```
Escalation Advisor:
Escalation rationale based on investigation state:
- Confidence level: [Current AI assessment score]
- Uncertainty factors: [List of specific unknowns or conflicting evidence]
- Complexity indicators: [Multi-jurisdiction, novel scheme, high volume]
- Regulatory triggers: [Amount thresholds, specific regulation flags]
- Recommended escalation path:
  * Primary: [Specific team or role]
  * Secondary: [Alternate if primary unavailable]
  * Tertiary: [Management notification path]
- Suggested escalation reason: [Concise, actionable statement]
- Required preparation: [Specific information to gather before escalating]
- Estimated review time: [Based on team workload]
Actionable suggestion: "Escalate to Senior Fraud Analyst due to conflicting evidence in location velocity analysis"
```

**Assign to Me Button Prompt**
```
Workload Management Assistant:
Assignment recommendations based on current capacity:
- Your current load: [Number] active investigations
- Average completion time: [Based on your history]
- Skill match: [Analysis of how this case fits your expertise]
- Workload balance: [Comparison to team averages]
- Suggested priority adjustment: [Based on case characteristics]
- Collaboration opportunity: [If relevant, suggest specific teammate for consultation]
- Learning value: [Assessment of skill development potential]
Actionable suggestion: "Accept assignment - matches your expertise in payment fraud patterns"
```

**Reassign Button Prompt**
```
Team Allocation Assistant:
Reassignment recommendations:
- Current assignee workload: [Analysis of their current capacity]
- Your workload comparison: [Relative to team and this investigator]
- Skill alignment: [How your expertise matches case requirements]
- Availability factors: [Schedule, pending time off, etc.)
- Development opportunity: [Assessment for both parties]
- Continuity considerations: [What context should be transferred]
- Recommended transition approach: [Specific handoff suggestions]
Actionable suggestion: "Reassign to Specialist Team Lead - better match for cryptocurrency expertise"
```

#### 2. Evidence Management Buttons

**Upload Evidence Button Prompt**
```
Evidence Intake Assistant:
Upload recommendations:
- File type analysis: [Automatic detection of what the file contains]
- Duplicate check: [Similarity score against existing evidence]
- Virus scan recommendation: [Recommended based on file source]
- Metadata extraction: [What information will be automatically gathered]
- Processing time estimate: [Based on file type and size]
- Suggested tags: [Auto-generated from file analysis]
- Relevant investigation connections: [Auto-detected links to other cases]
- Priority suggestion: [Based on content analysis]
Actionable suggestion: "Upload completed - system detects bank statement with relevant transaction dates"
```

**Tag Evidence Button Prompt**
```
Tagging Suggestion Engine:
Context-based tag recommendations:
- Content analysis: [Identified entities, dates, amounts, locations]
- Similar evidence: [Tags applied to visually/similar content]
- Investigation context: [Tags from other evidence in this case]
- Taxonomy compliance: [Suggested tags from controlled vocabulary]
- Confidence scores: [For each suggested tag]
- Bulk application: [Recommendation to apply to similar evidence]
- New tag suggestion: [If analysis suggests beneficial new category]
Actionable suggestion: "Apply tags: 'Bank Statement', 'Transaction Evidence', 'Date Range: 2024-03-01 to 2024-03-15'"
```

**Bookmark Evidence Button Prompt**
```
Bookmarking Assistant:
Bookmark value assessment:
- Reference frequency: [How often this evidence type is consulted]
- Connection strength: [Number of explicit links to other evidence]
- Uniqueness score: [Rarity within this investigation]
- Future reference likelihood: [Based on similar cases]
- Suggested folder/category: [For organizing bookmarks]
- Related bookmarks: [Other evidence users often bookmark together]
- Annotation recommendation: [What to note when bookmarking]
Actionable suggestion: "Bookmark with note: 'Key transaction showing abnormal timing pattern'"
```

**Mark as Relevant/Irrelevant Button Prompt**
```
Relevance Feedback Assistant:
Impact assessment of your decision:
- Current relevance score: [X.X] -> [New estimated score if marked relevant]
- Current relevance score: [X.X] -> [New estimated score if marked irrelevant]
- Effect on overall risk: [Quantitative impact assessment]
- Similar items affected: [Recommendation to review similar evidence]
- Learning contribution: [How this feedback improves future assessments]
- Confidence in suggestion: [Based on pattern matching]
- Alternative perspective: [Consider if marking opposite might be warranted]
Actionable suggestion: "Mark as relevant - strongly supports timeline contradiction hypothesis"
```

**Download Evidence Button Prompt**
```
Download Preparation Assistant:
Download considerations:
- Original format preservation: [Yes/no/conversion details]
- Virus re-scanning: [Recommendation for downloaded file]
- Metadata inclusion: [What additional data will be included]
- Redaction applied: [If any PII was automatically removed]
- Usage tracking: [This download will be logged for audit]
- Package options: [If multiple files, suggest grouping]
- Temporary access link: [Alternative to direct download for sharing]
Actionable suggestion: "Download approved - includes original metadata and virus check passed"
```

**View Evidence Button Prompt**
```
Evidence Viewing Assistant:
Viewing recommendations based on content type:
- For documents: "Use search for '[relevant term]' to find key sections"
- For images: "Zoom to 200% to examine [specific detail]"
- For spreadsheets: "Sort by [column] to see anomalous patterns"
- For transactions: "Filter by [amount range/date] to focus on suspicious activity"
- For communications: "Sort by date to establish timeline"
- Related evidence suggestions: [Items often viewed together]
- Annotation opportunities: [Common insights users document for this type]
- Time-saving tips: [Keyboard shortcuts or features specific to this view]
Actionable suggestion: "View enabled - use date filter to isolate weekend transactions"
```

**Add Comment Button Prompt**
```
Discussion Stimulator:
Comment context suggestions:
- Location-based: [Specific questions about this evidence/context]
- Pattern-based: [Observations that often generate discussion]
- Gap-filling: [Information that would complete the picture]
- Controversial aspects: [Elements reasonable people might interpret differently]
- Expert consultation: [When to involve specific specialists]
- Knowledge base links: [Relevant past cases or guidelines]
- Actionable next steps: [What resolving this comment might lead to]
Actionable suggestion: "Comment suggested: 'Could this timestamp be explained by timezone difference?'"
```

#### 3. Filter & Search Buttons

**Apply Filters Button Prompt**
```
Filter Optimization Assistant:
Filter effectiveness analysis:
- Current result count: [Number] items
- Selectivity: [Percentage reduction from unfiltered]
- Suggested refinements: [Based on empty/overly broad results]
  * If too many results: "Consider adding [specific filter] to reduce by [estimated%]"
  * If too few results: "Consider relaxing [specific filter] to increase by [estimated%]"
- Performance impact: [Estimated query time based on complexity]
- Alternative approaches: [Different filter combinations achieving similar goals]
- Saved pattern suggestion: [If this combination might be useful repeatedly]
- Index usage: [Which database fields are optimally used]
Actionable suggestion: "Apply filters - current selection shows 47 high-risk transactions from last 48 hours"
```

**Clear Filters Button Prompt**
```
Reset Assistance:
Clearing implications:
- Will reset: [List of all active filters]
- Current result impact: [From X filtered results to Y total items]
- Saved state: [Option to save current filter set before clearing]
- Alternatives: [Consider adjusting specific filters instead of full reset]
- Recovery: [How to restore if cleared accidentally]
- Suggested approach: [If partially clearing, which filters to keep]
Actionable suggestion: "Clear filters - you currently have 3 active filters showing 12 results from 1,248 total"
```

**Save View Button Prompt**
```
View Preservation Assistant:
Save recommendation analysis:
- Uniqueness score: [How unique this filter combination is]
- Reuse potential: [Likelihood you'll need similar view again]
- Team applicability: [How useful this might be for others]
- Performance characteristics: [Query efficiency of this saved view]
- Suggested name: [Auto-generated descriptive name]
- Suggested category: [Based on filters used]
- Sharing recommendation: [Private/team/organization based on content]
- Default consideration: [Whether this should be your personal default view]
Actionable suggestion: "Save as 'High Risk Recent Transactions' - matches your weekly review pattern"
```

**Search Button Prompt**
```
Search Intelligence Assistant:
Query enhancement suggestions:
- Current query: "[User's search term]"
- Alternative phrasings: [Based on thesaurus and domain terms]
- Related concepts: [System-suggested expansions]
- Field-specific hints: [Which data fields this searches]
- No results guidance: [If zero results, suggest alternatives]
- Too many results: [If overwhelming, suggest constraints]
- Synonym expansion: [Automatically adds related terms]
- Fuzzy matching: [When enabled for typo tolerance]
- Search scope: [Current: all fields, suggested: specific fields]
- Popular related: [What others search for when looking at similar terms]
Actionable suggestion: "Search for 'wire transfer' instead of 'wire xfer' - matches official terminology in 92% of cases"
```

**Clear Search Button Prompt**
```
Search Reset Helper:
Clearing effects:
- Current query: "[User's search text]"
- Result impact: [From X results to Y total items]
- Search history: [This query will remain accessible via history]
- Alternative: [Consider editing instead of clearing for minor changes]
- Recovery: [Access via search history if needed]
- Suggested action: [If lengthy query, consider using backspace for efficiency]
- Recent related: [Other searches you've made recently]
Actionable suggestion: "Clear search - current query 'international wire' showing 8 of 1,248 items"
```

#### 4. Data Management Buttons

**Create Button Prompt**
```
Creation Assistant:
Pre-creation guidance:
- Template suggestion: [Based on context and recent creations]
- Required fields: [List of mandatory information]
- Recommended defaults: [Based on similar items]
- Validation rules: [What will be checked during creation]
- Similar existing items: [To avoid duplication]
- Recommended naming convention: [If applicable]
- Initial setup steps: [What to configure immediately after creation]
- Time estimate: [Typical completion time for setup]
Actionable suggestion: "Create new investigation - recommended to start with transaction ID lookup"
```

**Edit Button Prompt**
```
Edit Preparation Assistant:
Edit context analysis:
- Current state summary: [Key attributes of item being edited]
- Change impact: [What modifying each field affects]
- Dependency warnings: [Fields that affect other calculations/processes]
- Validation preview: [What rules will apply to your changes]
- Similar edits: [What others commonly change in this context]
- Recommended approach: [Order of edits to minimize validation issues]
- Undo considerations: [How to revert if needed]
Actionable suggestion: "Edit investigation priority - changing from Medium to High will escalate review timeline"
```

**Delete Button Prompt**
```
Deletion Impact Analyzer:
Deletion consequences:
- Direct removal: [Specific item and any immediate children]
- Cascade effects: [Related items that will also be affected]
- Orphan prevention: [Items that will become disconnected but preserved]
- Audit trail: [What deletion records will be maintained]
- Recovery options: [Time window and process for restoration]
- Alternatives to consider: [Archiving, deactivating, hiding instead]
- Impact assessment: [Quantitative effect on reports, dashboards, etc.]
- Confirmation requirement: [Additional verification needed for sensitive deletes]
Actionable suggestion: "Delete evidence item - this will remove 1 linkage but preserve the evidence record itself"
```

**Duplicate Button Prompt**
```
Duplication Advisor:
Duplication implications:
- What gets copied: [List of exactly which attributes/relationships]
- What gets reset: [Identifiers, timestamps, status indicators]
- What gets cleared: [Certain flags, approvals, temporary states]
- Naming convention: [Suggested name for duplicate]
- Relationship handling: [How connections to other items are treated]
- Validation status: [Whether validation errors carry over]
- Modification suggestions: [What typically needs changing after duplication]
- Use cases: [Common legitimate reasons for duplicating this item type]
Actionable suggestion: "Duplicate investigation template - recommended to change transaction ID and customer information"
```

**Archive Button Prompt**
```
Archival Assessment:
Archival implications:
- Access change: [From active daily to periodic to archive-only access]
- Retrieval process: [How to restore if needed]
- Retention period: [How long archived items are kept]
- Storage implications: [Cost/performance considerations]
- Reporting impact: [Whether appears in standard reports]
- Legal hold considerations: [If applicable]
- Recommended timing: [Based on inactivity or completion]
- Alternative states: [Consider inactive vs archived based on needs]
Actionable suggestion: "Archive investigation - closed for 60 days with no recent activity"
```

**Restore Button Prompt**
```
Restoration Readiness Check:
Restoration implications:
- Source location: [Where item is being restored from]
- Current conflicts: [ naming or state conflicts with existing items]
- Dependency restoration: [What related items will be restored alongside]
- Status upon restore: [Default state after restoration]
- Notification triggers: [Who gets alerted by restoration]
- Validation needed: [What should be checked post-restoration]
- Cleanup recommendations: [Temporary items that may need removal]
Actionable suggestion: "Restore investigation - no conflicts detected, will return to active status with original ID"
```

**Publish Button Prompt**
```
Publication Readiness Review:
Publication effects:
- Visibility change: [From draft/private to available for use]
- Notification triggers: [Who gets alerted by publication]
- Update mechanisms: [How consumers will receive future changes]
- Rollback options: [Ability to revert to previous version]
- Impact assessment: [Effect on templates, reports, automated processes]
- Pre-flight checklist: [Specific items to verify before publishing]
- Version notes: [Recommended summary of changes]
- Audience consideration: [Who will see this and how they might use it]
Actionable suggestion: "Publish report template - includes all required fields and passes validation checks"
```

#### 5. Form & Input Buttons

**Save Button Prompt**
```
Save Impact Preview:
Save analysis:
- Changes to be saved: [Specific field modifications]
- Validation status: [All/currently valid/invalid fields]
- Dependency updates: [What calculations/processes will be triggered]
- Conflict detection: [Any simultaneous edits by others]
- Backup/version info: [What previous state is being replaced]
- Performance impact: [Expected processing time]
- Notification recipients: [Who gets alerted by these changes]
- Recommended timing: [Based on system load if applicable]
- Undo information: [How to revert if needed immediately after]
Actionable suggestion: "Save changes - 3 fields modified, all valid, will trigger risk score recalculation"
```

**Cancel Button Prompt**
```
Cancel Confirmation Helper:
Cancel consequences:
- Unsaved changes: [List of modifications that will be lost]
- Recovery options: [Whether draft auto-save exists]
- Navigation impact: [Where you'll be returned to]
- Alternatives to consider: [Save first, then navigate if preferred]
- Time investment: [Approximate time spent on current edits]
- Reminder system: [Whether you'll be prompted to return]
- Exit survey: [Optional quick feedback on abandonment reason]
Actionable suggestion: "Cancel edit - 2 unsaved changes will be lost, no auto-save available"
```

**Reset Button Prompt**
```
Reset Effect Clarifier:
Reset scope:
- Fields to be reset: [Specific list of what returns to original]
- Fields unaffected: [User preferences, system metadata, etc.]
- Comparison to reload: [Difference from full page refresh]
- State checkpoints: [What specific version is being restored]
- Unsaved change warning: [If modifications exist since last save]
- Alternative: [Consider individual field resets instead of full reset]
Actionable suggestion: "Reset form - 5 fields will return to original values entered 2 minutes ago"
```

**Submit Button Prompt**
```
Submission Readiness Check:
Submission analysis:
- Validity status: [All/passing/failing specific validations]
- Incomplete sections: [Required fields or sections needing attention]
- Readiness indicators: [System-derived completion percentage]
- Similar submissions: [Outcomes of comparable recent submissions]
- Processing time estimate: [Based on current queue and complexity]
- Notification chain: [Who/what gets alerted upon submission]
- Irreversibility check: [Any aspects that cannot be changed post-submission]
- Recommended preparations: [What to have ready for potential follow-up]
Actionable suggestion: "Submit investigation review - all validations complete, estimated processing 2 minutes"
```

**Run Button Prompt**
```
Execution Preparedness Guide:
Run implications:
- Resource usage: [Estimated CPU/memory/time consumption]
- Queue position: [Current wait time if applicable]
- Cancellation availability: [Whether and how to stop mid-execution]
- Progress tracking: [What monitoring will be available]
- Output disposition: [Where results will appear and how to access]
- Intermediate checkpoints: [Opportunity to review partial results]
- Failure recovery: [What happens if interrupted, restart behavior]
- Alternative approaches: [Less resource-intensive options if available]
- Optimal timing: [Based on system load patterns]
Actionable suggestion: "Run risk assessment - estimated completion in 90 seconds, cancellable at any stage"
```

**Schedule Button Prompt**
```
Scheduling Optimization Assistant:
Schedule effectiveness:
- Frequency analysis: [Is suggested interval optimal for data volatility?]
- Timing consideration: [Best time of day for minimal system impact]
- Conflict detection: [Scheduled maintenance or peak usage times]
- Resource forecasting: [Expected cumulative impact over time]
- Alternative frequencies: [Different intervals with trade-off analysis]
- Retention planning: [How long results will be stored]
- Notification strategy: [Who should be informed and when]
- Cost-benefit: [Value received versus system cost]
Actionable suggestion: "Schedule daily report generation for 2 AM - low system usage period"
```

**Test Button Prompt**
```
Validation Scope Clarifier:
Test coverage:
- What gets tested: [Specific aspects of the configuration]
- What is NOT tested: [Limitations of this test]
- Environment used: [Production-like, sandbox, or isolated]
- Data impact: [Whether test writes, modifies, or deletes data]
- Duration estimate: [Expected time to complete test]
- Prerequisites: [What must be true for test to run successfully]
- Failure diagnostics: [What information will be provided if test fails]
- Success criteria: [Clear definition of what constitutes passing]
- Next steps: [Recommended actions based on pass/fail outcome]
Actionable suggestion: "Test API connection - validates connectivity and authentication only, does not test data synchronization"
```

#### 6. Modal & Dialog Buttons

**OK Button Prompt**
```
Confirmation Assistant:
Decision context:
- Immediate effects: [What happens immediately upon confirmation]
- Delayed effects: [What processes start as a result]
- Irreversibility: [Which aspects cannot be undone]
- Alternatives considered: [Why this option was selected over others]
- Risk assessment: [Any potential downsides and their likelihood]
- Mitigation steps: [What can be done to address potential issues]
- Confirmation recommendation: [Based on analysis of above factors]
Actionable suggestion: "Confirm action - immediate effect: investigation paused, reversible within 24 hours"
```

**Cancel Button Prompt**
```
Dismissal Consequence Clarifier:
Dismissal effects:
- State changes: [What modifications will NOT be saved]
- Process impacts: [What automated actions will NOT be triggered]
- Navigation result: [Where interface returns to]
- Recovery options: [Whether any work is preserved as draft]
- Alternative actions: [Consider saving first if applicable]
- User intention: [Opportunity to confirm desire to abandon changes]
Actionable suggestion: "Cancel changes - returns to investigation list, 4 unsaved modifications will be lost"
```

**Yes/No Buttons Prompt**
```
Binary Choice Evaluator:
Choice analysis:
- Question restatement: [Clear representation of what is being decided]
- Yes consequences: [Specific outcomes if affirmative selected]
- No consequences: [Specific outcomes if negative selected]
- Default recommendation: [Based on safety, convention, or efficiency]
- Context factors: [Situational elements affecting the recommendation]
- Uncertainty markers: [Where information is incomplete]
- Reversibility assessment: [Which option is easier to change later]
- Long-term implications: [Effects beyond immediate outcome]
Actionable suggestion: "Select Yes - initiates immediate backup while preserving current state for rollback"
```

**Save & Close Button Prompt**
```
Efficient Exit Advisor:
Combined action analysis:
- Save outcome: [Specific changes that will be persisted]
- Close outcome: [Exact navigation destination]
- Alternative approaches: [Save then navigate separately]
- Efficiency gain: [Time saved versus separate actions]
- Risk assessment: [Compared to saving separately then navigating]
- Validation status: [Whether save will succeed before closing]
- Recovery path: [How to retrieve if needed after closing]
Actionable suggestion: "Save and close - preserves all 3 edits and returns to investigation dashboard"
```

**Apply Button Prompt**
```
Immediate Effect Preview:
Application effects:
- Immediate changes: [What takes effect without closing dialog]
- Persistence: [Whether changes survive dialog cancellation]
- Scope: [Which components or views are affected]
- Performance impact: [Immediate resource consumption]
- Preview available: [How to see effects before committing]
- Reversibility: [How to undo if effects are undesirable]
- Recommended sequencing: [If multiple changes, optimal order]
Actionable suggestion: "Apply filter changes - updates current view immediately, can be adjusted further before finalizing"
```

#### 7. Status & Toggle Buttons

**Toggle Switch Prompt**
```
Configuration Impact Analyzer:
Toggle consequences:
- Immediate effect: [What changes when switched]
- Dependency impact: [What other features/settings are affected]
- Resource usage change: [Increase/decrease in system consumption]
- User experience change: [How workflow or interface alterations]
- Data handling difference: [What gets processed/stored differently]
- Reversibility: [Ease and impact of switching back]
- Default recommendation: [Based on security, performance, or usability best practice]
- Similar configurations: [How peers in your role/organization typically set this]
- Trial period suggestion: [Consider temporary enablement for evaluation]
Actionable suggestion: "Enable real-time notifications - increases responsiveness, minimal battery impact on mobile"
```

**Status Indicator Button Prompt**
```
Status Interpretation Guide:
Current state meaning:
- Literal interpretation: [What the indicator specifically measures]
- Implication: [What this means for your workflow or decisions]
- Trend information: [Whether improving, degrading, or stable]
- Comparison points: [How this compares to historical averages or peers]
- Action recommendation: [Suggested response based on state]
- Escalation criteria: [When this should trigger concern or action]
- Related indicators: [Other metrics that provide complementary view]
- False positive/negative: [Common reasons for misleading readings]
Actionable suggestion: "System status: Healthy - all services operating within normal parameters"
```

**Bulk Select Toggle Prompt**
```
Selection Scope Clarifier:
Selection implications:
- Current selection: [How many items are currently selected]
- Total affected: [How many items this toggle will change]
- Visibility scope: [Whether applies to visible items only or all filtered]
- Selection type: [Adding to current selection vs replacing entirely]
- Action preparation: [What bulk operations become available/unavailable]
- Clear indication: [Visual feedback showing exactly what will change]
- Reversal ease: [How simple it is to undo this action]
- Alternative approaches: [Consider shift-click or command-click for granular control]
Actionable suggestion: "Select all 24 visible items - matches current filter results exactly"
```

#### 8. Help & Guidance Buttons

**Help/Tooltip Button Prompt**
```
Contextual Assistance Offer:
Help content relevance:
- Immediate applicability: [How directly this helps with current task]
- Depth recommendation: [Whether quick tip or detailed guide is better]
- Prerequisite knowledge: [What you should know before reading]
- Related topics: [What else you might want to explore afterward]
- Format suggestion: [Video, step-by-step, reference, or troubleshooting]
- Timeliness: [How current this information is relative to recent changes]
- Skill level targeting: [Beginner, intermediate, or advanced focused]
- Alternative sources: [Where else this information might be found]
Actionable suggestion: "View help - explains advanced filtering options relevant to your current task"
```

**Tour Button Prompt**
```
Onboarding Value Assessment:
Tour benefits:
- Features covered: [Specific aspects of interface/functionality being shown]
- Time investment: [Estimated duration to complete]
- Skill progression: [Where this takes you from beginner to proficient]
- Immediate applicability: [What you can do right after finishing]
- Prerequisites covered: [What foundational knowledge is established]
- Advanced preparation: [What this sets you up to learn next]
- Alternative learning: [Other ways to cover this material]
- Completion recognition: [Badge, certificate, or progress tracking]
- Skip value: [What you miss by skipping versus time saved]
Actionable suggestion: "Take guided tour - covers investigation workflow features you haven't used yet"
```

**Feedback Button Prompt**
```
Contribution Effectiveness:
Feedback impact:
- Issue types addressed: [Bug report, feature request, usability concern, etc.]
- Typical resolution time: [Based on category and current backlog]
- Visibility: [Who sees and acts on this feedback]
- Follow-up process: [Whether and how you'll get updates]
- Anonymization: [What information is removed if submitted anonymously]
- Alternative channels: [Other ways to provide this type of feedback]
- Priority factors: [What gets this escalated or delayed]
- Recognition: [How contributions are acknowledged in system/update notes]
Actionable suggestion: "Submit feedback - your suggestion about export formatting matches a planned improvement"
```

**Video Tutorial Button Prompt**
```
Learning Resource Recommender:
Tutorial suitability:
- Skill match: [Whether your current level fits the target audience]
- Topic coverage: [Specific aspects demonstrated]
- Production quality: [Clarity, pacing, visual/audio quality]
- Length vs depth: [Appropriate balance for topic complexity]
- Prerequisites assumed: [What knowledge is expected]
- Practical application: [How directly techniques apply to work]
- Supplementary materials: [Available transcripts, slides, exercises]
- Alternative formats: [Text guide, interactive simulation, documentation]
- Currency: [How recently this was recorded/update]
Actionable suggestion: "Watch tutorial - demonstrates advanced evidence linking techniques relevant to your current case"
```

#### 9. System & Admin Buttons

**Refresh Button Prompt**
```
Data Currency Advisor:
Refresh implications:
- Data staleness: [How current vs. potentially available data]
- Update frequency: [How often source data refreshes normally]
- Change likelihood: [Probability of new information since last load]
- Performance cost: [Resources consumed by refresh operation]
- Cancellation availability: [Whether long refresh can be interrupted]
- Alternative: [Consider partial refresh or specific component refresh]
- Recommended interval: [Based on data volatility and work type]
- Indicator specifics: [Exactly what data gets refreshed]
Actionable suggestion: "Refresh data - last update was 4 minutes ago, new transactions likely available"
```

**Settings Button Prompt**
```
Personalization Impact:
Settings scope:
- Affected areas: [Which parts of interface or behavior change]
- Persistence: [Whether settings remain across sessions/logins]
- Scope: [Personal only vs affecting shared views/projects]
- Performance impact: [Any resource consumption changes]
- Reset options: [How to return to defaults if needed]
- Dependency effects: [What other features might behave differently]
- Recommended adjustments: [Based on your usage patterns or role]
- Similar configurations: [What peers with similar roles typically use]
- Risk assessment: [Potential downsides of specific changes]
Actionable suggestion: "Adjust notification settings - reduce email frequency while maintaining critical alerts"
```

**User Menu Button Prompt**
```
Account Status Indicator:
Menu contents significance:
- Profile completeness: [How much of your profile information is filled]
- Notification status: [Number and types of pending alerts]
- Security indicators: [MFA status, recent password change, active sessions]
- Availability: [Current working status, scheduled time off, etc.]
- Quick actions: [Common tasks accessible without full navigation]
- Recent activity: [Your most recent system interactions]
- Suggested actions: [Based on time of day, calendar, or pending work]
- Security recommendations: [Specific actions to enhance account protection]
Actionable suggestion: "View profile - consider updating your timezone settings for accurate timestamps"
```

**Logout Button Prompt**
```
Session Security Consideration:
Logout implications:
- Session termination: [What access and privileges end immediately]
- Persistent data: [What remains available after logout (cached data, etc.)]
- Re-authentication: [What will be needed to regain access]
- Active operations: [What ongoing processes get interrupted or preserved]
- Security benefits: [Specific risks mitigated by logging out]
- Convenience factors: [Trade-off between security and ease of resumption]
- Session duration: [How long current session has been active]
- Automatic alternatives: [Consider lock instead of logout for temporary absence]
- Next session: [What remembers about you for faster future login]
Actionable suggestion: "Log out - recommended after 2 hours of inactivity on shared workstation"
```

**Help/Support Button Prompt**
```
Assistance Access Guide:
Support options:
- Immediate help: [Live chat, phone availability with wait times]
- Self-service: [Documentation relevance to common issues]
- Community: [Peer-to-peer assistance availability]
- Escalation paths: [When and how to get expert intervention]
- Response expectations: [Typical times for different issue types]
- Preparation needed: [What information to have ready for faster help]
- Alternative timing: [When support might be more readily available]
- Issue categorization: [Help route self-assessment tool]
Actionable suggestion: "Contact support - technical specialists available for immediate assistance with investigation tools"
```

**Notification Bell Button Prompt**
```
Notification Management:
Current state:
- Unread count: [Exact number of notifications needing attention]
- Categories: [Breakdown by type: system alerts, investigation updates, etc.]
- Priority distribution: [High/medium/low importance split]
- Age range: [Oldest and newest unread notifications]
- Actionability: [How many require response vs informational only]
- Similar patterns: [This resembles your typical notification profile]
- Recommended action: [Process in batches vs immediate attention]
- Clearing strategy: [Suggested order for efficient handling]
- Future prevention: [Settings to reduce noise if overwhelmed]
Actionable suggestion: "View notifications - 5 unread including 2 investigation updates requiring your review"
```

#### 10. Specialized Investigation Buttons

**Hypothesis Button Prompt**
```
Hypothesis Formation Assistant:
Hypothesis quality indicators:
- Testability: [How easily this can be proven/refuted with evidence]
- Specificity: [How precise vs vague the statement is]
- Novelty: [How much this adds beyond current consensus]
- Explanatory power: [How many observations it accounts for]
- Parsimony: [Whether simpler alternatives exist]
- Falsifiability: [What evidence would disprove it]
- Domain consistency: [How well it aligns with known fraud patterns]
- Suggested refinements: [Ways to make hypothesis stronger]
- Evidence needed: [What specific data would confirm or refute]
Actionable suggestion: "Refine hypothesis - consider making more specific about transaction timing mechanism"
```

**Request Information Button Prompt**
```
Request Optimization Assistant:
Request effectiveness:
- Clarity score: [How precisely the need is articulated]
- Compliance likelihood: [Estimated chance of full cooperation]
- Burden assessment: [Impact on responding party]
- Legal sufficiency: [Whether meets requirements for intended use]
- Alternative approaches: [Less intrusive methods to get similar information]
- Cost-benefit: [Value of information versus effort/cost]
- Timing consideration: [Whether urgency affects likelihood of compliance]
- Escalation path: [What happens if request is denied or ignored]
- Response tracking: [How fulfillment will be monitored and reported]
Actionable suggestion: "Strengthen request - specify exact date range and format to reduce back-and-forth"
```

**Link Evidence Button Prompt**
```
Connection Value Assessor:
Link significance:
- Relationship type: [Nature of connection being proposed]
- Temporal proximity: [Time distance between linked items]
- Semantic similarity: [Conceptual overlap beyond surface level]
- Corroboration value: [How much this supports or contradicts existing theories]
- Chain potential: [Whether this creates or extends evidence chains]
- Redundancy check: [Whether similar connections already exist]
- Investigation impact: [How this changes overall narrative or timeline]
- Alternative interpretations: [Other ways to explain the apparent connection]
- Validation methods: [How to confirm the link is genuine rather than coincidental]
Actionable suggestion: "Create link - strong temporal and contextual connection supports sequence hypothesis"
```

**Compare Button Prompt**
```
Comparison Utility Analysis:
Comparison benefits:
- Difference highlight: [What specific variations will be emphasized]
- Similarity revelation: [What commonalities might be overlooked otherwise]
- Pattern detection: [Enable spotting of consistent anomalies]
- Baseline establishment: [Creating reference for what's normal]
- Anomaly scoring: [Quantifying degree of deviation]
- Context preservation: [Maintaining ability to see both items in original context]
- Tool recommendation: [Specific view mode or technique for this comparison type]
- Documentation value: [How results contribute to investigation record]
- Actionability: [How differences point to specific next steps]
Actionable suggestion: "Compare transactions - focus on amount patterns and timing relationships"
```

**Anonymize Button Prompt**
```
Privacy Protection Evaluator:
Anonymization effectiveness:
- Technique suitability: [Match between method and data type]
- Re-identification risk: [Estimated likelihood of reversing anonymization]
- Utility preservation: [How much analytical value remains after processing]
- Compliance verification: [Which regulations this satisfies]
- Irreversibility: [Whether process can be undone]
- Metadata retention: [What contextual information remains usable]
- Audit trail: [What documentation of the process is maintained]
- Alternative methods: [Different approaches with different trade-offs]
- Performance impact: [Computational resources required]
Actionable suggestion: "Apply anonymization - recommended technique preserves date patterns while removing identifiers"
```

**Validate Button Prompt**
```
Validation Scope Clarifier:
Validation coverage:
- Rules checked: [Specific validation rules being applied]
- Rules skipped: [Known limitations of this validation]
- Severity levels: [How issues are categorized (error/warning/info)]
- False positive rate: [Typical incidence of incorrect flags]
- False negative rate: [Likelihood of missing real problems]
- Remediation guidance: [How to fix each type of issue found]
- Prevention suggestions: [How to avoid similar issues in future]
- Baseline comparison: [How this compares to historical averages]
- Prioritization: [Which issues to address first based on impact]
Actionable suggestion: "Run validation - checks 12 regulatory compliance rules and 8 data quality checks"
```