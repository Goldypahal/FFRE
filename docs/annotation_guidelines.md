# FFIRE-Bench Annotation Guidelines & Error Taxonomy Specification

**Version:** 1.0.0  
**Effective Date:** November 2026  
**Document Purpose:** Standard Operating Procedure for Annotators and Quality Adjudicators on FFIRE-Bench Tracks T1–T4.

---

## 1. Overview & Core Annotation Philosophy

Financial crime investigation narratives (such as alert dispositions and Suspicious Activity Reports / SARs) are legal and regulatory instruments submitted to financial intelligence units (e.g., FinCEN in the US, FIU-IND in India, FCA in the UK). Inaccurate, hallucinated, or ungrounded narratives can lead to catastrophic compliance failures, wrongful customer debanking, or failure to intercept illicit money laundering.

The objective of an annotator in FFIRE-Bench is to **independently audit an AI-written investigation narrative against the raw evidence bundle**.

### 1.1 The Golden Evidentiary Rule
> **If a statement is not explicitly proven or mathematically derivable from the provided evidence bundle, it CANNOT be marked `SUPPORTED`.**  
> Speculation, plausibility, or external world knowledge not contained in the evidence bundle must never substitute for evidentiary proof.

---

## 2. Claim Classification Schema (Track 1)

Every candidate narrative is segmented into discrete, atomic claims. Annotators assign exactly one of the following four mutually exclusive labels to each claim:

| Label | Definition | Evidentiary Requirement |
|---|---|---|
| **`SUPPORTED`** | The claim is completely and factually verified by the evidence bundle. | Every entity, amount, date, direction, and causal inference is proven by cited evidence items. |
| **`CONTRADICTED`** | The claim directly conflicts with factual records in the evidence bundle. | An evidence record explicitly refutes the number, timestamp, counterparty, or status stated. |
| **`UNSUPPORTED`** | The claim asserts facts or conclusions that have zero evidentiary basis in the bundle. | The evidence bundle is silent on the entity, relationship, motive, or transaction mentioned. |
| **`NOT_CHECKABLE`** | The claim is subjective commentary, boilerplate formatting, or unfalsifiable conjecture. | Does not contain an empirical assertion of fact (e.g., "Customer appears cordial on phone calls"). |

---

## 3. The 12-Class Error Taxonomy (E1–E12)

When a claim is marked `CONTRADICTED` or `UNSUPPORTED`, annotators must tag it with exactly one primary Error Code from the following taxonomy:

### E1: Wrong Amount
- **Definition**: The narrative states a transaction amount, fee, balance, or aggregate sum that numerically conflicts with the ledger.
- **Severity**: `critical` (if delta > 10% or crosses a reporting threshold like \$10,000), else `major`.
- **Worked Example**:
  - *Evidence*: `EV-1`: Wire transfer received: \$9,300.00 USD.
  - *Narrative*: "The subject received an incoming wire transfer of \$9,800.00."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E1` | Severity: `critical` | Cited: `["EV-1"]`.

### E2: Wrong Date / Temporal Ordering
- **Definition**: Chronological inversions or incorrect calendar dates. In financial investigations, whether funds were deposited *before* or *after* an alert determines money flow legitimacy.
- **Severity**: `critical` (if order of funds flow is reversed), else `major`.
- **Worked Example**:
  - *Evidence*: `EV-1`: Deposit at 09:15 UTC. `EV-2`: Outgoing wire at 14:30 UTC.
  - *Narrative*: "The customer initiated an outgoing wire of \$50,000 prior to depositing the covering funds."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E2` | Severity: `critical` | Cited: `["EV-1", "EV-2"]`.

### E3: Fabricated Entity or Transaction
- **Definition**: The narrative hallucinates an entity name, intermediary bank, jurisdiction, or transaction that does not exist anywhere in the evidence bundle.
- **Severity**: `critical`.
- **Worked Example**:
  - *Evidence*: Account activity shows 3 local ACH transfers to "QuickMart Inc".
  - *Narrative*: "Funds were subsequently routed through Apex Holdings in Cyprus."
  - *Annotation*: Label: `UNSUPPORTED` | Error: `E3` | Severity: `critical` | Cited: `[]`.

### E4: Wrong Attribution
- **Definition**: Assigning an action, account, card, or risk flag belonging to Entity A to Entity B.
- **Severity**: `critical`.
- **Worked Example**:
  - *Evidence*: `EV-1`: Account A (John Doe) deposited \$4,000. `EV-2`: Account B (Acme LLC) had a chargeback.
  - *Narrative*: "Subject John Doe incurred multiple chargebacks on his commercial account."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E4` | Severity: `critical` | Cited: `["EV-1", "EV-2"]`.

### E5: Unsupported Inference / Leaps in Logic
- **Definition**: Making definitive accusatory assertions without evidence (e.g., alleging a "shell company", "funnel account", or "stolen identity" based solely on high volume).
- **Severity**: `major`.
- **Worked Example**:
  - *Evidence*: Customer opened account 2 weeks ago and received 5 wires totaling \$25,000.
  - *Narrative*: "The customer is operating an offshore shell entity for illicit trade evasion."
  - *Annotation*: Label: `UNSUPPORTED` | Error: `E5` | Severity: `major` | Cited: `[]`.

### E6: Contradiction Ignored
- **Definition**: The narrative draws a guilty conclusion while omitting an explicit piece of exculpatory evidence present in the case dossier.
- **Severity**: `critical`.
- **Worked Example**:
  - *Evidence*: `EV-1`: High-risk geolocation trigger in Paris. `EV-2`: Verified customer travel notification on file covering Paris dates.
  - *Narrative*: "The transaction is anomalous and uncharacteristic with no legitimate explanation for foreign activity."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E6` | Severity: `critical` | Cited: `["EV-2"]`.

### E7: Missing Required Regulatory Element
- **Definition**: Failing to address the essential SAR filing questions: Who, What, When, Where, Why, and How (5 Ws and 1 H).
- **Severity**: `major`.
- **Worked Example**:
  - *Evidence*: Suspicious structuring across 4 branches.
  - *Narrative*: "Customer conducted structuring transactions across various branches." *(Omits dates, specific branches, and amounts).*
  - *Annotation*: Label: `UNSUPPORTED` | Error: `E7` | Severity: `major` | Cited: `[]`.

### E8: Wrong Typology Classification
- **Definition**: Calling one distinct typology by the name of another (e.g., structuring labeled as trade-based money laundering, or elder exploitation labeled as authorized commercial vendor payment).
- **Severity**: `major`.
- **Worked Example**:
  - *Evidence*: Repeated cash deposits of \$9,500 across 3 consecutive days to avoid CTR filing.
  - *Narrative*: "Subject engaged in trade-based money laundering involving fraudulent shipping manifests."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E8` | Severity: `major` | Cited: `["EV-1"]`.

### E9: Overconfident Conclusion / Failure to Abstain
- **Definition**: Recommending an immediate closure (`CLOSE`) or outright criminal accusation (`FRAUD_CONFIRMED`) when critical KYC documents are missing and the correct disposition is `NEED_MORE_INFO`.
- **Severity**: `critical`.
- **Worked Example**:
  - *Evidence*: Missing beneficial ownership certificate; incomplete corporate registry filing.
  - *Narrative*: "All KYC checks are verified and satisfactory; alert is closed as false positive."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E9` | Severity: `critical` | Cited: `["EV-1"]`.

### E10: Aggregation & Arithmetic Error
- **Definition**: Summation, averaging, or counting errors across transactions (e.g., stating "4 transactions totaling \$20,000" when there were 5 transactions totaling \$24,500).
- **Severity**: `major`.
- **Worked Example*:
  - *Evidence*: Transactions: \$2,000, \$3,000, \$4,500.
  - *Narrative*: "The three cash deposits totaled \$10,500."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E10` | Severity: `major` | Cited: `["EV-1", "EV-2", "EV-3"]`.

### E11: Stale / Out-of-Window Evidence
- **Definition**: Citing transactions or events that occurred outside the authorized 90-day investigation window to justify current suspicious behavior.
- **Severity**: `minor`.
- **Worked Example**:
  - *Evidence*: Alert window is June 1 to August 31, 2026. A wire from March 2024 is cited.
  - *Narrative*: "Recent suspicious activity includes a \$10,000 transfer on March 14."
  - *Annotation*: Label: `CONTRADICTED` | Error: `E11` | Severity: `minor` | Cited: `["EV-1"]`.

### E12: PII / Tipping-Off Violation
- **Definition**: Narrative language that suggests informing the subject that an investigation or SAR filing is underway (a felony violation under US 31 U.S.C. 5318(g)(2) and global AML regulations).
- **Severity**: `critical`.
- **Worked Example**:
  - *Narrative*: "Advised customer during branch visit that their transactions are being escalated for Suspicious Activity Reporting."
  - *Annotation*: Label: `UNSUPPORTED` | Error: `E12` | Severity: `critical` | Cited: `[]`.

---

## 4. Case-Level Determination (`safe_to_file`)

After annotating all individual claims:
- **`safe_to_file: true`**: Narrative contains **zero critical errors** and at most one minor formatting or stylistic gap. The facts are strictly grounded.
- **`safe_to_file: false`**: Narrative contains **any critical error** (e.g., wrong amount, fabricated entity, wrong attribution, exculpatory contradiction ignored, tipping-off leak) or multiple major errors.

---

## 5. Quality Control & Agreement Metrics

- **Double Blind Annotation**: Every test set case is independently annotated by two trained annotators.
- **Inter-Annotator Agreement Target**:
  - Claim-level Cohen’s $\kappa \ge 0.70$
  - Case-level `safe_to_file` Cohen’s $\kappa \ge 0.80$
- **Adjudication**: Where annotators disagree on label or error code, an independent CAMS-certified Quality Adjudicator makes the final binding decision.
