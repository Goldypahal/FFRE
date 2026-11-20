"""
Benchmark evaluator orchestrating metric calculation, cluster-bootstrapped CIs,
threshold checking against targets.yaml, and slice breakdowns.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from ffire_bench.schema.models import Case, PredictionBundle, PredictionCase
from ffire_bench.scoring.metrics import (
    compute_t1_claim_metrics,
    compute_t2_error_detection_metrics,
    compute_t3_disposition_metrics
)
from ffire_bench.scoring.bootstrap import cluster_bootstrap_ci


def load_benchmark_targets(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load benchmark evaluation targets from YAML."""
    search_paths = []
    if config_path:
        search_paths.append(config_path)
    search_paths.extend([
        Path("configs/targets.yaml"),
        Path("benchmarks/config/targets.yaml"),
        Path(__file__).resolve().parents[2] / "configs" / "targets.yaml"
    ])

    for p in search_paths:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    return data
    return {}


def evaluate_threshold(val: float, rule: Dict[str, Any]) -> Dict[str, Any]:
    """Check a metric against a threshold rule, returning pass/fail status."""
    thresh = float(rule.get("threshold", 0.0))
    op = rule.get("operator", ">=")
    passed = False
    if op == ">=":
        passed = (val >= thresh)
    elif op == "<=":
        passed = (val <= thresh)
    elif op == ">":
        passed = (val > thresh)
    elif op == "<":
        passed = (val < thresh)
    elif op == "==":
        passed = (abs(val - thresh) < 1e-6)

    return {
        "value": val,
        "threshold": thresh,
        "operator": op,
        "label": rule.get("label", f"{op} {thresh}"),
        "status": "PASS" if passed else "FAIL"
    }


class BenchmarkEvaluator:
    def __init__(self, targets: Optional[Dict[str, Any]] = None):
        self.targets = targets or load_benchmark_targets()

    def evaluate(
        self,
        gold_cases: List[Case],
        predictions: PredictionBundle,
        num_resamples: int = 500
    ) -> Dict[str, Any]:
        """
        Evaluate model predictions against gold-standard cases.
        """
        gold_map = {c.case_id: c for c in gold_cases}
        pred_map = {p.case_id: p for p in predictions.predictions}

        track = predictions.track.value if hasattr(predictions.track, "value") else str(predictions.track)
        model_name = predictions.model_name

        # Prepare evaluation pairs
        t1_pairs = []
        t2_cases = []
        t3_cases = []

        # Slice data accumulators
        typology_cases = {}
        difficulty_cases = {}
        error_code_claims = {}
        source_cases = {}

        for case_id, gold_c in gold_map.items():
            pred_c = pred_map.get(case_id)
            if not pred_c:
                continue

            typ = gold_c.typology
            diff = gold_c.difficulty.value if hasattr(gold_c.difficulty, "value") else str(gold_c.difficulty)
            src = gold_c.provenance.narrative_source

            if typ not in typology_cases:
                typology_cases[typ] = []
            if diff not in difficulty_cases:
                difficulty_cases[diff] = []
            if src not in source_cases:
                source_cases[src] = []

            # T1 Claim pairing
            pred_claim_map = {cl.claim_id: cl for cl in pred_c.claims}
            for gold_cl in gold_c.claims:
                p_cl = pred_claim_map.get(gold_cl.claim_id)
                p_lbl = p_cl.predicted_label.value if (p_cl and hasattr(p_cl.predicted_label, "value")) else (p_cl.predicted_label if p_cl else "UNSUPPORTED")
                p_cites = p_cl.cited_evidence_ids if p_cl else []

                g_lbl = gold_cl.label.value if hasattr(gold_cl.label, "value") else str(gold_cl.label)
                pair = {
                    "case_id": case_id,
                    "cluster_id": gold_c.cluster_id,
                    "claim_id": gold_cl.claim_id,
                    "gold_label": g_lbl,
                    "pred_label": p_lbl,
                    "gold_evidence_ids": gold_cl.gold_evidence_ids,
                    "pred_evidence_ids": p_cites,
                    "typology": typ,
                    "difficulty": diff,
                    "narrative_source": src,
                    "error_code": gold_cl.error_code.value if (gold_cl.error_code and hasattr(gold_cl.error_code, "value")) else str(gold_cl.error_code or "NONE")
                }
                t1_pairs.append(pair)

                err = pair["error_code"]
                if err != "NONE":
                    if err not in error_code_claims:
                        error_code_claims[err] = []
                    error_code_claims[err].append(pair)

            # T2 Error detection pairing
            has_crit = any(
                cl.severity and (cl.severity == "critical" or getattr(cl.severity, "value", "") == "critical")
                for cl in gold_c.claims
            )
            t2_entry = {
                "case_id": case_id,
                "cluster_id": gold_c.cluster_id,
                "gold_safe_to_file": gold_c.case_label.safe_to_file,
                "pred_safe_to_file": pred_c.predicted_safe_to_file if pred_c.predicted_safe_to_file is not None else True,
                "pred_confidence": pred_c.predicted_confidence if pred_c.predicted_confidence is not None else 1.0,
                "has_critical_error": has_crit,
                "typology": typ,
                "difficulty": diff,
                "narrative_source": src
            }
            t2_cases.append(t2_entry)
            typology_cases[typ].append(t2_entry)
            difficulty_cases[diff].append(t2_entry)
            source_cases[src].append(t2_entry)

            # T3 Disposition pairing
            g_disp = gold_c.case_label.disposition.value if hasattr(gold_c.case_label.disposition, "value") else str(gold_c.case_label.disposition)
            p_disp = pred_c.predicted_disposition.value if (pred_c.predicted_disposition and hasattr(pred_c.predicted_disposition, "value")) else (pred_c.predicted_disposition if pred_c.predicted_disposition else "ALLOW")
            t3_entry = {
                "case_id": case_id,
                "cluster_id": gold_c.cluster_id,
                "gold_disposition": g_disp,
                "pred_disposition": p_disp,
                "gold_is_fraud": g_disp in ("FLAG", "ESCALATE"),
                "pred_confidence": pred_c.predicted_confidence if pred_c.predicted_confidence is not None else 1.0,
                "expected_abstention": gold_c.case_label.expected_abstention
            }
            t3_cases.append(t3_entry)

        # Compute Core Track Metrics
        results = {
            "model_name": model_name,
            "track": track,
            "benchmark_version": "0.1.0",
            "evaluated_cases_count": len(t2_cases),
            "evaluated_claims_count": len(t1_pairs),
        }

        # Track 1
        t1_metrics = compute_t1_claim_metrics(t1_pairs) if t1_pairs else {}
        # Track 2
        t2_metrics = compute_t2_error_detection_metrics(t2_cases) if t2_cases else {}
        # Track 3
        t3_metrics = compute_t3_disposition_metrics(t3_cases) if t3_cases else {}

        # Bootstrap Confidence Intervals (95%)
        ci_results = {}
        if t1_pairs:
            def t1_macro_wrapper(sample):
                return compute_t1_claim_metrics(sample)["macro_f1"]
            pt, low, high = cluster_bootstrap_ci(t1_pairs, t1_macro_wrapper, cluster_key="cluster_id", num_resamples=num_resamples)
            ci_results["t1_macro_f1_95ci"] = [low, high]

        if t2_cases:
            def t2_acc_wrapper(sample):
                return compute_t2_error_detection_metrics(sample)["safe_to_file_accuracy"]
            pt, low, high = cluster_bootstrap_ci(t2_cases, t2_acc_wrapper, cluster_key="cluster_id", num_resamples=num_resamples)
            ci_results["t2_safe_to_file_acc_95ci"] = [low, high]

        results["metrics"] = {
            "t1": t1_metrics,
            "t2": t2_metrics,
            "t3": t3_metrics,
            "confidence_intervals": ci_results
        }

        # Target Threshold Checking (Dynamic PASS/FAIL)
        track_targets = self.targets.get("tracks", {}).get(f"t{track[-1].lower()}_{'claim_verification' if track == 'T1' else ('narrative_error_detection' if track == 'T2' else 'disposition_abstention')}", {})
        evaluations = {}

        if track == "T1" and t1_metrics:
            if "macro_f1" in track_targets:
                evaluations["macro_f1"] = evaluate_threshold(t1_metrics["macro_f1"], track_targets["macro_f1"])
            if "citation_f1" in track_targets:
                evaluations["citation_f1"] = evaluate_threshold(t1_metrics["citation_metrics"]["citation_f1"], track_targets["citation_f1"])
        elif track == "T2" and t2_metrics:
            if "safe_to_file_accuracy" in track_targets:
                evaluations["safe_to_file_accuracy"] = evaluate_threshold(t2_metrics["safe_to_file_accuracy"], track_targets["safe_to_file_accuracy"])
            if "critical_error_recall" in track_targets:
                evaluations["critical_error_recall"] = evaluate_threshold(t2_metrics["critical_error_recall"], track_targets["critical_error_recall"])
        elif track == "T3" and t3_metrics:
            if "cost_weighted_accuracy" in track_targets:
                evaluations["cost_weighted_accuracy"] = evaluate_threshold(t3_metrics["cost_weighted_accuracy"], track_targets["cost_weighted_accuracy"])
            if "brier_score" in track_targets:
                evaluations["brier_score"] = evaluate_threshold(t3_metrics["brier_score"], track_targets["brier_score"])
            if "ece_15_bins" in track_targets:
                evaluations["ece_15_bins"] = evaluate_threshold(t3_metrics["ece_15_bins"], track_targets["ece_15_bins"])

        passed_evals = sum(1 for e in evaluations.values() if e["status"] == "PASS")
        total_evals = len(evaluations)
        overall_status = "PASS" if (total_evals > 0 and passed_evals == total_evals) else "FAIL"

        results["evaluations"] = evaluations
        results["overall_status"] = overall_status
        results["targets_passed"] = passed_evals
        results["targets_total"] = total_evals

        # Slice Breakdowns
        results["slices"] = {
            "by_typology": {
                typ: compute_t2_error_detection_metrics(cases)["safe_to_file_accuracy"]
                for typ, cases in typology_cases.items() if cases
            },
            "by_difficulty": {
                diff: compute_t2_error_detection_metrics(cases)["safe_to_file_accuracy"]
                for diff, cases in difficulty_cases.items() if cases
            },
            "by_narrative_source": {
                src: compute_t2_error_detection_metrics(cases)["safe_to_file_accuracy"]
                for src, cases in source_cases.items() if cases
            },
            "by_error_code": {
                err: round(sum(1 for p in pairs if p["gold_label"] == p["pred_label"]) / len(pairs) * 100.0, 2)
                for err, pairs in error_code_claims.items() if pairs
            }
        }

        return results
