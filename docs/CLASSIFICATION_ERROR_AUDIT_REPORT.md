# FFRE Auditable Root-Cause Analysis: 13 Held-Out Classification Errors

**Release Milestone**: RC3 Decision Quality Qualification  
**Corpus**: Independent Held-Out 100-Case Evaluation Corpus (`data/benchmarks/held_out_100_evaluation_report.json`)  
**Audit Records Produced**: 13 (8 False Positives, 5 False Negatives)  
**Audit Generator**: `scripts/audit_held_out_classification_errors.py`  

---

## 1. Executive Summary

Across the 100-case held-out statistical evaluation, FFRE achieved an **87.00% overall accuracy** (95% CI: 79.02%–92.24%), a **90.91% recall** (50/55 fraud cases detected), and an **F1 score of 0.8850**. Exactly 13 classification errors occurred:
- **8 False Positives** (HC-018 to HC-025): High-value enterprise B2B cloud vendor payments.
- **5 False Negatives** (HC-096 to HC-100): Unverified new customer accounts with missing KYC documentation.

This document provides a forensic audit trail for every error, attributing the failure to specific subsystems: missing telemetry, rule logic, retrieval, model reasoning, or threshold selection.

---

## 2. High-Level Failure Attribution Matrix

| Error Category | Cases | Primary Subsystem | Secondary Subsystem | Mechanism |
|:---|:---:|:---|:---|:---|
| **False Positives** | HC-018 to HC-025 (8 cases) | **Rule Logic** | **Threshold Selection** | Amount anomaly check (> $10k / > $20k) lacks profile awareness for corporate B2B clients; dual threshold overrides LLM 'ALLOW'. |
| **False Negatives** | HC-096 to HC-100 (5 cases) | **Rule Logic** | **Model Reasoning** | Absence of mandatory KYC CIP escalation rule in `rules.py`; unverified accounts with small amounts defaulted to 'ALLOW'. |

---

## 3. Auditable Records: False Positives (8 Cases)

### Case `HC-018`: LEGITIMATE_CORPORATE_B2B ($10,000.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #3 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.75 | **Predicted Risk Score**: 0.750
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 0.75 | Reasons: CTR reporting threshold transfer ($10,000.00 >= $10,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($10,000.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.55 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (0.750). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-019`: LEGITIMATE_CORPORATE_B2B ($12,500.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #4 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.75 | **Predicted Risk Score**: 0.750
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 0.75 | Reasons: CTR reporting threshold transfer ($12,500.00 >= $10,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($12,500.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.55 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (0.750). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-020`: LEGITIMATE_CORPORATE_B2B ($15,000.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #5 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.75 | **Predicted Risk Score**: 0.750
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 0.75 | Reasons: CTR reporting threshold transfer ($15,000.00 >= $10,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($15,000.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.55 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (0.750). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-021`: LEGITIMATE_CORPORATE_B2B ($17,500.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #6 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.75 | **Predicted Risk Score**: 0.750
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 0.75 | Reasons: CTR reporting threshold transfer ($17,500.00 >= $10,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($17,500.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.55 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (0.750). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-022`: LEGITIMATE_CORPORATE_B2B ($20,000.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #7 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.67 | **Predicted Risk Score**: 1.000
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 1.0 | Reasons: High-value transaction anomaly ($20,000.00 >= $20,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($20,000.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.85 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (1.000). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-023`: LEGITIMATE_CORPORATE_B2B ($22,500.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #8 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.67 | **Predicted Risk Score**: 1.000
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 1.0 | Reasons: High-value transaction anomaly ($22,500.00 >= $20,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($22,500.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.85 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (1.000). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-024`: LEGITIMATE_CORPORATE_B2B ($25,000.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #9 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.67 | **Predicted Risk Score**: 1.000
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 1.0 | Reasons: High-value transaction anomaly ($25,000.00 >= $20,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($25,000.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.85 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (1.000). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

### Case `HC-025`: LEGITIMATE_CORPORATE_B2B ($27,500.00)
- **Scenario**: ENTERPRISE_COMMERCIAL purchasing from Authorized Cloud Supplier #10 via Windows Server 2022.
- **Ground Truth**: `ALLOW` (Fraud = `False`)
- **System Decision**: `ALLOW` | **Confidence**: 0.67 | **Predicted Risk Score**: 1.000
- **Classification Outcome**: Marked as Fraud (`predicted_fraud = True`) due to risk score >= 0.50.
- **Executed Rules**: Score: 1.0 | Reasons: High-value transaction anomaly ($27,500.00 >= $20,000.00)., New device detected.
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Threshold Selection**
  * *Why did it trigger fraud?* The transaction amount ($27,500.00) crossed the retail high-value/CTR threshold in rules.py (triggering +0.85 penalty). Because rules.py does not condition amount anomaly thresholds on customer profile ('ENTERPRISE_COMMERCIAL' corporate B2B vendor payments), the rule engine assigned an uncalibrated high risk score (1.000). While the LLM reasoner correctly identified legitimate commercial intent and outputted decision='ALLOW', the evaluation metric's decision boundary flagged it as fraud because predicted_risk_score >= 0.50.
  * *Remediation*: Add `account_type == 'ENTERPRISE'` baseline check to `rules.py` and align binary decision boundary with agent textual decision.

---

## 4. Auditable Records: False Negatives (5 Cases)

### Case `HC-096`: INSUFFICIENT_EVIDENCE_KYC ($150.00)
- **Scenario**: NEW_UNVERIFIED_ACCOUNT with `kyc_status='UNVERIFIED'` transferring $150.00 via PeerTransfer #1.
- **Ground Truth**: `ESCALATE` (Fraud/Escalate = `True`)
- **System Decision**: `ALLOW` | **Confidence**: 0.77 | **Predicted Risk Score**: 0.171
- **Classification Outcome**: Marked as Non-Fraud (`predicted_fraud = False`).
- **Executed Rules**: Score: 0.2 | Reasons: Merchant has high historical fraud rate (20.0%).
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Missing Telemetry Failsafe**
  * *Why did it miss fraud?* Customer profile has kyc_status='UNVERIFIED' and risk_tier='UNVERIFIED'. The rule engine in rules.py lacks an explicit CIP/KYC check to penalize unverified accounts or fail closed. Because the amount ($150.00) is low and velocity is 1, the rule engine scored it only 0.200. The system allowed the transaction with low risk score (0.171) instead of escalating for manual human KYC verification (ground truth: ESCALATE).
  * *Remediation*: Implement mandatory CIP rule: if `kyc_status == 'UNVERIFIED'`, force `rule_score += 0.85` and trigger mandatory escalation to `human_review`.

### Case `HC-097`: INSUFFICIENT_EVIDENCE_KYC ($230.00)
- **Scenario**: NEW_UNVERIFIED_ACCOUNT with `kyc_status='UNVERIFIED'` transferring $230.00 via PeerTransfer #2.
- **Ground Truth**: `ESCALATE` (Fraud/Escalate = `True`)
- **System Decision**: `ALLOW` | **Confidence**: 0.77 | **Predicted Risk Score**: 0.171
- **Classification Outcome**: Marked as Non-Fraud (`predicted_fraud = False`).
- **Executed Rules**: Score: 0.2 | Reasons: Merchant has high historical fraud rate (20.0%).
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Missing Telemetry Failsafe**
  * *Why did it miss fraud?* Customer profile has kyc_status='UNVERIFIED' and risk_tier='UNVERIFIED'. The rule engine in rules.py lacks an explicit CIP/KYC check to penalize unverified accounts or fail closed. Because the amount ($230.00) is low and velocity is 1, the rule engine scored it only 0.200. The system allowed the transaction with low risk score (0.171) instead of escalating for manual human KYC verification (ground truth: ESCALATE).
  * *Remediation*: Implement mandatory CIP rule: if `kyc_status == 'UNVERIFIED'`, force `rule_score += 0.85` and trigger mandatory escalation to `human_review`.

### Case `HC-098`: INSUFFICIENT_EVIDENCE_KYC ($310.00)
- **Scenario**: NEW_UNVERIFIED_ACCOUNT with `kyc_status='UNVERIFIED'` transferring $310.00 via PeerTransfer #3.
- **Ground Truth**: `ESCALATE` (Fraud/Escalate = `True`)
- **System Decision**: `ALLOW` | **Confidence**: 0.77 | **Predicted Risk Score**: 0.171
- **Classification Outcome**: Marked as Non-Fraud (`predicted_fraud = False`).
- **Executed Rules**: Score: 0.2 | Reasons: Merchant has high historical fraud rate (20.0%).
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Missing Telemetry Failsafe**
  * *Why did it miss fraud?* Customer profile has kyc_status='UNVERIFIED' and risk_tier='UNVERIFIED'. The rule engine in rules.py lacks an explicit CIP/KYC check to penalize unverified accounts or fail closed. Because the amount ($310.00) is low and velocity is 1, the rule engine scored it only 0.200. The system allowed the transaction with low risk score (0.171) instead of escalating for manual human KYC verification (ground truth: ESCALATE).
  * *Remediation*: Implement mandatory CIP rule: if `kyc_status == 'UNVERIFIED'`, force `rule_score += 0.85` and trigger mandatory escalation to `human_review`.

### Case `HC-099`: INSUFFICIENT_EVIDENCE_KYC ($390.00)
- **Scenario**: NEW_UNVERIFIED_ACCOUNT with `kyc_status='UNVERIFIED'` transferring $390.00 via PeerTransfer #4.
- **Ground Truth**: `ESCALATE` (Fraud/Escalate = `True`)
- **System Decision**: `ALLOW` | **Confidence**: 0.77 | **Predicted Risk Score**: 0.171
- **Classification Outcome**: Marked as Non-Fraud (`predicted_fraud = False`).
- **Executed Rules**: Score: 0.2 | Reasons: Merchant has high historical fraud rate (20.0%).
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Missing Telemetry Failsafe**
  * *Why did it miss fraud?* Customer profile has kyc_status='UNVERIFIED' and risk_tier='UNVERIFIED'. The rule engine in rules.py lacks an explicit CIP/KYC check to penalize unverified accounts or fail closed. Because the amount ($390.00) is low and velocity is 1, the rule engine scored it only 0.200. The system allowed the transaction with low risk score (0.171) instead of escalating for manual human KYC verification (ground truth: ESCALATE).
  * *Remediation*: Implement mandatory CIP rule: if `kyc_status == 'UNVERIFIED'`, force `rule_score += 0.85` and trigger mandatory escalation to `human_review`.

### Case `HC-100`: INSUFFICIENT_EVIDENCE_KYC ($470.00)
- **Scenario**: NEW_UNVERIFIED_ACCOUNT with `kyc_status='UNVERIFIED'` transferring $470.00 via PeerTransfer #5.
- **Ground Truth**: `ESCALATE` (Fraud/Escalate = `True`)
- **System Decision**: `ALLOW` | **Confidence**: 0.77 | **Predicted Risk Score**: 0.171
- **Classification Outcome**: Marked as Non-Fraud (`predicted_fraud = False`).
- **Executed Rules**: Score: 0.2 | Reasons: Merchant has high historical fraud rate (20.0%).
- **Workflow Nodes Executed**: `planner -> retrieve_customer -> retrieve_device -> retrieve_location -> retrieve_merchant -> retrieve_transaction...`
- **Attribution**: **Rule Logic + Missing Telemetry Failsafe**
  * *Why did it miss fraud?* Customer profile has kyc_status='UNVERIFIED' and risk_tier='UNVERIFIED'. The rule engine in rules.py lacks an explicit CIP/KYC check to penalize unverified accounts or fail closed. Because the amount ($470.00) is low and velocity is 1, the rule engine scored it only 0.200. The system allowed the transaction with low risk score (0.171) instead of escalating for manual human KYC verification (ground truth: ESCALATE).
  * *Remediation*: Implement mandatory CIP rule: if `kyc_status == 'UNVERIFIED'`, force `rule_score += 0.85` and trigger mandatory escalation to `human_review`.

---

## 5. Subsystem Attribution Breakdown

| Subsystem | Contributing to FPs? | Contributing to FNs? | Remediation Detail |
|:---|:---:|:---:|:---|
| **Missing Telemetry** | No | Yes | Missing CIP/KYC verification signals did not fail closed to manual review. |
| **Rule Logic** | Yes | Yes | Retail-only amount thresholds penalized commercial clients; missing KYC escalation rule. |
| **Retrieval** | No | No | Evidence retrieval correctly extracted all DB records without omission. |
| **Model Reasoning** | No | Yes | Reasoner fallback tolerated unverified customer profile on low amounts. |
| **Threshold Selection** | Yes | No | Evaluator used `score >= 0.50` which overrode the agent's correct textual `ALLOW`. |

---

## 6. Actionable Fixes for RC3 Decision Quality

1. **Enterprise Baseline Rule Calibration** (`backend/rules.py`):
   - Check `state.get('customer_evidence', {}).get('account_type')` or `risk_tier` before applying consumer CTR amount thresholds.
   - For enterprise accounts, raise high-value threshold to $100,000.
2. **Mandatory CIP / Unverified KYC Rule** (`backend/rules.py`):
   - If `kyc_status in ('UNVERIFIED', 'INSUFFICIENT')`, trigger `CIP_UNVERIFIED_ACCOUNT` rule (+0.80) and set `decision = 'ESCALATE'`.
3. **Decision & Threshold Unification** (`scripts/evaluate_held_out_100_cases.py`):
   - Ground binary fraud classification strictly on system verdict (`decision in ('FLAG', 'ESCALATE')`), eliminating synthetic FP splits where the model decided `ALLOW`.
