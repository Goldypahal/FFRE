import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.evaluate_held_out_100_cases import load_evaluation_targets, evaluate_all_metrics

json_path = REPO_ROOT / 'data' / 'benchmarks' / 'held_out_100_evaluation_report.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

targets = load_evaluation_targets()
evals = evaluate_all_metrics(data['metrics'], targets)
passed_count = sum(1 for e in evals.values() if e['status'] == 'PASS')
total_evals = len(evals)
overall_status = 'PASS' if passed_count == total_evals else 'FAIL'

data['overall_status'] = overall_status
data['targets_passed'] = passed_count
data['targets_total'] = total_evals
data['evaluations'] = evals

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

md_path = REPO_ROOT / 'data' / 'benchmarks' / 'held_out_100_evaluation_report.md'
m = data['metrics']
cm = data['confusion_matrix']
sample_size = data['sample_size']

with open(md_path, 'w', encoding='utf-8') as f:
    f.write('# FFRE Held-Out 100-Case Statistical Decision Evaluation Report\n\n')
    f.write('**Evaluation Type**: Independent Held-Out Corpus\n')
    f.write(f'**Sample Size**: {sample_size} cases across 6 archetypes\n')
    f.write('**Date**: November 2026 (Updated with dynamic threshold evaluation)\n\n')
    f.write(f'### Overall Benchmark Status: **{overall_status}** ({passed_count}/{total_evals} Targets Met)\n\n')
    f.write('> [!WARNING]\n')
    f.write(f'> **Credibility Notice**: Earlier iterations hard-coded "PASS" across all rows. Dynamic evaluation against `configs/targets.yaml` confirms {total_evals - passed_count} target violations requiring optimization.\n\n')
    f.write('## 1. Confusion Matrix\n\n')
    f.write('| | Predicted Fraud | Predicted Legitimate |\n')
    f.write('|---|:---:|:---:|\n')
    f.write(f'| **Actual Fraud** | **TP = {cm["true_positives"]}** | **FN = {cm["false_negatives"]}** |\n')
    f.write(f'| **Actual Legitimate** | **FP = {cm["false_positives"]}** | **TN = {cm["true_negatives"]}** |\n\n')
    f.write('## 2. Statistical Metrics & 95% Confidence Intervals\n\n')
    f.write('| Metric | Point Estimate | 95% Confidence Interval (Wilson Score) | Configured Target | Benchmark Status |\n')
    f.write('|---|:---:|:---:|:---:|:---:|\n')
    f.write(f'| **Accuracy** | {m["accuracy_pct"]:.2f}% | [{m["accuracy_95_ci"][0]}%, {m["accuracy_95_ci"][1]}%] | {evals["accuracy"]["target_label"]} | **{evals["accuracy"]["status"]}** |\n')
    f.write(f'| **Precision** | {m["precision_pct"]:.2f}% | [{m["precision_95_ci"][0]}%, {m["precision_95_ci"][1]}%] | {evals["precision"]["target_label"]} | **{evals["precision"]["status"]}** |\n')
    f.write(f'| **Recall (Sensitivity)** | {m["recall_pct"]:.2f}% | [{m["recall_95_ci"][0]}%, {m["recall_95_ci"][1]}%] | {evals["recall"]["target_label"]} | **{evals["recall"]["status"]}** |\n')
    f.write(f'| **Specificity** | {m["specificity_pct"]:.2f}% | N/A | {evals["specificity"]["target_label"]} | **{evals["specificity"]["status"]}** |\n')
    f.write(f'| **F1 Score** | {m["f1_score"]:.4f} | N/A | {evals["f1_score"]["target_label"]} | **{evals["f1_score"]["status"]}** |\n')
    f.write(f'| **False-Positive Rate** | {m["false_positive_rate_pct"]:.2f}% | N/A | {evals["false_positive_rate"]["target_label"]} | **{evals["false_positive_rate"]["status"]}** |\n')
    f.write(f'| **False-Negative Rate** | {m["false_negative_rate_pct"]:.2f}% | N/A | {evals["false_negative_rate"]["target_label"]} | **{evals["false_negative_rate"]["status"]}** |\n')
    f.write(f'| **Brier Calibration Score** | {m["brier_score"]} | N/A | {evals["brier_score"]["target_label"]} | **{evals["brier_score"]["status"]}** |\n')
    f.write(f'| **Evidence Grounding** | {m["evidence_grounding_accuracy_pct"]:.1f}% | N/A | {evals["evidence_grounding"]["target_label"]} | **{evals["evidence_grounding"]["status"]}** |\n')
    f.write(f'| **KYC Escalation Rate** | {m["insufficient_kyc_escalation_pct"]:.1f}% | N/A | {evals["kyc_escalation_rate"]["target_label"]} | **{evals["kyc_escalation_rate"]["status"]}** |\n\n')
    f.write('## 3. Archetype Distribution\n\n')
    f.write('- **Legitimate Retail & Corporate**: 40 cases (40%)\n')
    f.write('- **Velocity Burst Attacks**: 20 cases (20%)\n')
    f.write('- **Account Takeover & Unfamiliar Device**: 15 cases (15%)\n')
    f.write('- **Impossible Travel / Location Delta**: 10 cases (10%)\n')
    f.write('- **Contradictory Evidence Boundary Cases**: 10 cases (10%)\n')
    f.write('- **Insufficient Evidence / Missing KYC**: 5 cases (5%)\n')

print('Reports successfully regenerated with computed statuses!')
