# FFIRE - Fully Detailed User Flows Specification

This document maps out the complete, step-by-step journeys for every persona in the FFIRE platform, using the exact state transition flow mandated by the product requirements.

---

## 1. Flow: Analyst End-to-End Investigation
**Persona**: Fraud Analyst

Start
↓
Navigate to `/login`
↓
Enter Email & Password
↓
Click `Login`
↓
Call API `POST /api/v1/auth/login`
↓
Response: 200 OK (MFA Required)
↓
Route to `/login/mfa`
↓
Enter 6-digit OTP
↓
Click `Verify`
↓
Call API `POST /api/v1/auth/mfa/verify`
↓
Response: 200 OK (JWT Token)
↓
Route to `/dashboard`
↓
View `Assigned Cases` Widget
↓
Click `Search Transaction` Input
↓
Type "TXN-9942"
↓
Auto-suggestions load
↓
Click Result "TXN-9942"
↓
Route to `/transactions/TXN-9942`
↓
Click `Start Investigation` Button
↓
Open Modal: Ask for Priority
↓
Select "High Priority"
↓
Click `Confirm`
↓
Call API `POST /api/v1/investigations`
↓
Route to `/investigations/INV-1029/live`
↓
Subscribe to WebSocket `/ws/investigations/INV-1029/stream`
↓
View Stream: Customer Retrieval
↓
View Stream: Merchant Retrieval
↓
View Stream: Device Retrieval
↓
View Stream: Location
↓
View Stream: Velocity
↓
View Stream: Knowledge Base
↓
View Stream: Risk Analysis
↓
View Stream: Validator
↓
View Stream: Report Generation
↓
WebSocket Close (Graph Completed)
↓
Route to `/investigations/INV-1029/summary`
↓
Read Risk Score (94%) & AI Recommendation
↓
Click `Evidence` Tab
↓
Expand `Device Intelligence` Section
↓
Read OS Mismatch warning
↓
Click `Graph` Tab
↓
Click "Location Validator" Node
↓
Read exact JSON payload in Right Drawer
↓
Click `Summary` Tab
↓
Click `Mark as Fraud` Button
↓
Open Confirmation Modal
↓
Type Note: "Confirmed device and IP mismatch"
↓
Click `Confirm`
↓
Call API `PATCH /api/v1/investigations/INV-1029/status`
↓
Show Toast: "Investigation closed as Fraud"
↓
Route to `/dashboard`
↓
End

---

## 2. Flow: Senior Analyst Escalation & Override
**Persona**: Senior Fraud Analyst

Start
↓
Navigate to `/dashboard`
↓
Click `Investigations` in Sidebar
↓
Route to `/investigations/queue`
↓
Click `Filters` Dropdown
↓
Select Status: `Escalated`
↓
Table updates via API `GET /investigations?status=ESCALATED`
↓
Click Row `INV-8821`
↓
Route to `/investigations/INV-8821/summary`
↓
Read Junior Analyst Notes in Activity Feed
↓
Click `Evidence` Tab
↓
Click `Historical Cases` Sidebar Link
↓
Call API `GET /api/v1/investigations/INV-8821/evidence/historical`
↓
View Similar Cases (100% match found)
↓
Click Past Case `INV-7710`
↓
Open New Tab `/investigations/INV-7710/summary`
↓
Determine false positive based on history
↓
Return to original Tab
↓
Click `Summary` Tab
↓
Click `Mark as Genuine` Button
↓
Open Confirmation Modal
↓
Select Override Reason: `False Positive (Historical Match)`
↓
Type Note: "Identical to approved case INV-7710"
↓
Click `Confirm`
↓
Call API `PATCH /api/v1/investigations/INV-8821/status`
↓
Show Toast: "Case overridden and marked Genuine"
↓
Click `Assign` Quick Action Button
↓
Open Reassign Modal
↓
Select Original Junior Analyst
↓
Click `Reassign`
↓
Call API `PATCH /api/v1/investigations/INV-8821/assignee`
↓
Show Toast: "Case reassigned for review"
↓
End

---

## 3. Flow: Compliance Officer Audit & Export
**Persona**: Compliance Officer

Start
↓
Navigate to `/dashboard`
↓
Click `Audit Logs` in Sidebar
↓
Route to `/audit/logs`
↓
View raw log stream
↓
Click `Advanced Query` Button
↓
Select Target Resource: `INV-1029`
↓
Click `Search`
↓
Call API `GET /api/v1/audit/logs?target=INV-1029`
↓
View all Analyst and AI actions on this case
↓
Expand row `INVESTIGATION_CREATED`
↓
Inspect JSON Payload in Modal
↓
Close Modal
↓
Navigate to Search Bar
↓
Search `INV-1029`
↓
Route to `/investigations/INV-1029/summary`
↓
Click `Report` Tab
↓
Route to `/investigations/INV-1029/report`
↓
Check box: `Include Raw Logs`
↓
Check box: `Include Graph Execution JSON`
↓
Click `Download PDF` Button
↓
Call API `POST /api/v1/investigations/INV-1029/export`
↓
Loading State: Button Spinner
↓
Response: 200 OK (application/pdf stream)
↓
Browser triggers file download (`INV-1029_Audit.pdf`)
↓
End

---

## 4. Flow: Administrator Configuration
**Persona**: Administrator

Start
↓
Navigate to `/dashboard`
↓
Click `Administration` in Sidebar
↓
Route to `/admin/overview`
↓
Click `Thresholds` Panel
↓
Route to `/admin/config/thresholds`
↓
Drag `Auto-Approve Genuine` Slider from 95% to 90%
↓
Click `Save Configuration`
↓
Call API `PATCH /api/v1/admin/config/thresholds`
↓
Show Toast: "Thresholds updated successfully"
↓
Click `Notifications Bell` in Top Nav
↓
View Notification: "GeoIP Webhook Failed"
↓
Click Notification
↓
Route to `/admin/webhooks/logs`
↓
Expand failed webhook row
↓
Click `View Payload`
↓
Inspect failure reason
↓
Close Modal
↓
Click `Retry Webhook` Button
↓
Call API `POST /api/v1/admin/webhooks/retry/{id}`
↓
Status Badge updates from Red `Failed` to Green `Success`
↓
End

---
**End of Detailed User Flows**
