"""
Metric computation engines for FFIRE-Bench Tracks T1, T2, and T3.
"""

import math
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import defaultdict


# ============================================================================
# Track 1: Claim Verification Metrics
# ============================================================================

def compute_t1_claim_metrics(
    eval_pairs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compute claim verification metrics across:
    SUPPORTED, CONTRADICTED, UNSUPPORTED, NOT_CHECKABLE.
    
    eval_pairs: List of dicts with:
      - gold_label: str
      - pred_label: str
      - gold_evidence_ids: List[str]
      - pred_evidence_ids: List[str]
    """
    labels = ["SUPPORTED", "CONTRADICTED", "UNSUPPORTED", "NOT_CHECKABLE"]
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    support = defaultdict(int)

    total_gold_citations = 0
    total_pred_citations = 0
    correct_citations = 0

    for pair in eval_pairs:
        g = pair["gold_label"]
        p = pair["pred_label"]
        support[g] += 1

        if g == p:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1

        # Evidence citation evaluation
        gold_cites: Set[str] = set(pair.get("gold_evidence_ids", []))
        pred_cites: Set[str] = set(pair.get("pred_evidence_ids", []))

        total_gold_citations += len(gold_cites)
        total_pred_citations += len(pred_cites)
        correct_citations += len(gold_cites.intersection(pred_cites))

    per_class = {}
    f1_list = []

    for lbl in labels:
        p_val = tp[lbl] / (tp[lbl] + fp[lbl]) if (tp[lbl] + fp[lbl]) > 0 else 0.0
        r_val = tp[lbl] / (tp[lbl] + fn[lbl]) if (tp[lbl] + fn[lbl]) > 0 else 0.0
        f1_val = (2 * p_val * r_val) / (p_val + r_val) if (p_val + r_val) > 0 else 0.0
        f1_list.append(f1_val)
        per_class[lbl] = {
            "precision": round(p_val, 4),
            "recall": round(r_val, 4),
            "f1": round(f1_val, 4),
            "support": support[lbl]
        }

    macro_f1 = sum(f1_list) / len(labels) if labels else 0.0

    cite_prec = correct_citations / total_pred_citations if total_pred_citations > 0 else 0.0
    cite_rec = correct_citations / total_gold_citations if total_gold_citations > 0 else 0.0
    cite_f1 = (2 * cite_prec * cite_rec) / (cite_prec + cite_rec) if (cite_prec + cite_rec) > 0 else 0.0

    total_claims = len(eval_pairs)
    total_correct = sum(tp[lbl] for lbl in labels)
    micro_accuracy = total_correct / total_claims if total_claims > 0 else 0.0

    return {
        "macro_f1": round(macro_f1, 4),
        "micro_accuracy": round(micro_accuracy, 4),
        "total_claims": total_claims,
        "citation_metrics": {
            "citation_precision": round(cite_prec, 4),
            "citation_recall": round(cite_rec, 4),
            "citation_f1": round(cite_f1, 4),
            "correct_citations": correct_citations,
            "gold_citations": total_gold_citations,
            "pred_citations": total_pred_citations
        },
        "per_class": per_class
    }


# ============================================================================
# Track 2: Narrative Error Detection Metrics
# ============================================================================

def compute_t2_error_detection_metrics(
    case_evals: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    case_evals: List of dicts with:
      - gold_safe_to_file: bool
      - pred_safe_to_file: bool
      - pred_confidence: float (optional)
      - has_critical_error: bool
      - critical_error_detected: bool
    """
    total = len(case_evals)
    if total == 0:
        return {}

    tp = 0  # Gold unsafe, predicted unsafe
    fp = 0  # Gold safe, predicted unsafe
    tn = 0  # Gold safe, predicted safe
    fn = 0  # Gold unsafe, predicted safe

    critical_total = 0
    critical_detected = 0

    for c in case_evals:
        g_safe = c["gold_safe_to_file"]
        p_safe = c["pred_safe_to_file"]

        if not g_safe and not p_safe:
            tp += 1
        elif g_safe and not p_safe:
            fp += 1
        elif g_safe and p_safe:
            tn += 1
        else:
            fn += 1

        if c.get("has_critical_error", False):
            critical_total += 1
            if c.get("critical_error_detected", not p_safe):
                critical_detected += 1

    accuracy = (tp + tn) / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    critical_recall = critical_detected / critical_total if critical_total > 0 else 1.0

    return {
        "safe_to_file_accuracy": round(accuracy * 100.0, 2),
        "precision": round(precision * 100.0, 2),
        "recall": round(recall * 100.0, 2),
        "specificity": round(specificity * 100.0, 2),
        "f1": round(f1, 4),
        "critical_error_recall": round(critical_recall * 100.0, 2),
        "confusion_matrix": {
            "true_unsafe": tp,
            "false_unsafe": fp,
            "true_safe": tn,
            "false_safe": fn
        },
        "total_cases": total
    }


# ============================================================================
# Track 3: Disposition, Abstention & Calibration Metrics
# ============================================================================

def compute_t3_disposition_metrics(
    eval_cases: List[Dict[str, Any]],
    fn_cost_multiplier: float = 10.0
) -> Dict[str, Any]:
    """
    Compute cost-weighted accuracy, Brier score, and 15-bin Expected Calibration Error (ECE).
    
    eval_cases: List of dicts with:
      - gold_disposition: str ('ALLOW', 'CLOSE', 'FLAG', 'ESCALATE', 'NEED_MORE_INFO')
      - pred_disposition: str
      - gold_is_fraud: bool
      - pred_confidence: float [0.0, 1.0]
      - expected_abstention: bool
      - abstained: bool (pred_disposition == 'NEED_MORE_INFO')
    """
    total = len(eval_cases)
    if total == 0:
        return {}

    correct = 0
    total_cost = 0.0
    max_possible_cost = 0.0

    brier_sum = 0.0
    prob_pairs = []

    abstention_target_count = 0
    correct_abstentions = 0

    for c in eval_cases:
        gd = c["gold_disposition"]
        pd = c["pred_disposition"]
        is_fraud = c.get("gold_is_fraud", gd in ("FLAG", "ESCALATE"))
        conf = float(c.get("pred_confidence", 0.5))

        if gd == pd:
            correct += 1

        # Cost weighting:
        # False negative (allowing actual fraud) costs fn_cost_multiplier (e.g. 10.0)
        # False positive (flagging/escalating legitimate) costs 1.0
        # Correct decision costs 0.0
        pred_is_fraud = pd in ("FLAG", "ESCALATE")
        if is_fraud and not pred_is_fraud:
            cost = fn_cost_multiplier
        elif not is_fraud and pred_is_fraud:
            cost = 1.0
        else:
            cost = 0.0

        total_cost += cost
        max_possible_cost += fn_cost_multiplier if is_fraud else 1.0

        # Brier score calculation
        actual_val = 1.0 if is_fraud else 0.0
        brier_sum += (conf - actual_val) ** 2
        prob_pairs.append((conf, actual_val))

        # Abstention tracking
        if c.get("expected_abstention", False):
            abstention_target_count += 1
            if pd == "NEED_MORE_INFO":
                correct_abstentions += 1

    cost_weighted_accuracy = max(0.0, 1.0 - (total_cost / max_possible_cost)) if max_possible_cost > 0 else 1.0
    brier_score = round(brier_sum / total, 4)

    # 15-bin Expected Calibration Error (ECE)
    num_bins = 15
    bin_size = 1.0 / num_bins
    ece = 0.0

    for b in range(num_bins):
        bin_lower = b * bin_size
        bin_upper = (b + 1) * bin_size
        in_bin = [
            (c, a) for (c, a) in prob_pairs
            if (bin_lower <= c < bin_upper) or (b == num_bins - 1 and c == 1.0)
        ]
        if in_bin:
            avg_confidence = sum(c for c, _ in in_bin) / len(in_bin)
            avg_accuracy = sum(a for _, a in in_bin) / len(in_bin)
            ece += (len(in_bin) / total) * abs(avg_accuracy - avg_confidence)

    abstention_recall = correct_abstentions / abstention_target_count if abstention_target_count > 0 else 1.0

    return {
        "raw_accuracy": round((correct / total) * 100.0, 2),
        "cost_weighted_accuracy": round(cost_weighted_accuracy * 100.0, 2),
        "total_penalty_cost": round(total_cost, 2),
        "brier_score": brier_score,
        "ece_15_bins": round(ece, 4),
        "abstention_recall": round(abstention_recall * 100.0, 2),
        "total_cases": total
    }
