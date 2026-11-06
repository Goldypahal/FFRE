#!/usr/bin/env python3
"""
FFIRE Model Risk Management Validation Kit (SR 26-2 / SR 11-7 / OCC 2011-12 Aligned).
Differentiating Feature #3 from Enterprise Readiness Report.

Derives every reported metric from per-observation holdout prediction arrays and
derives the qualification status from recorded evidence (data provenance, threshold
results, external validation). It never substitutes default metric values: if the
evidence is missing it refuses to generate the pack.
"""

import os
import sys
import json
import math
import datetime
from typing import Dict, Any, Tuple, List, Sequence, Optional
import numpy as np

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for _p in (BACKEND_DIR, REPO_DIR):  # ml.dataset imports via the backend.* package path
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ml.registry import ModelRegistry

DEFAULT_DOC_PATH = os.path.join(REPO_DIR, "docs", "MODEL_RISK_VALIDATION_PACK.md")
TRAINING_REPORT_PATH = os.path.join(BACKEND_DIR, "ml", "training_report.json")


def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes exact two-sided Wilson score 95% confidence interval for a binomial proportion."""
    if total == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence standard normal quantile
    p_hat = successes / total
    denominator = 1 + (z ** 2) / total
    center = (p_hat + (z ** 2) / (2 * total)) / denominator
    margin = (z * math.sqrt((p_hat * (1 - p_hat) / total) + (z ** 2) / (4 * (total ** 2)))) / denominator
    return max(0.0, round(center - margin, 4)), min(1.0, round(center + margin, 4))


def compute_hanley_mcneil_ci(auc: float, n_pos: int, n_neg: int) -> Tuple[float, float]:
    """
    Computes Hanley-McNeil asymptotic 95% confidence interval for ROC-AUC.
    Uses negative-exponential stochastic concordance variances:
    Q1 = AUC / (2.0 - AUC)
    Q2 = (2.0 * (AUC ** 2)) / (1.0 + AUC)
    var = (AUC * (1 - AUC) + (n_pos - 1)*(Q1 - AUC^2) + (n_neg - 1)*(Q2 - AUC^2)) / (n_pos * n_neg)
    """
    if n_pos == 0 or n_neg == 0:
        return 0.0, 1.0
    q1 = auc / (2.0 - auc)
    q2 = (2.0 * (auc ** 2)) / (1.0 + auc)
    var = (auc * (1.0 - auc) + (n_pos - 1) * (q1 - (auc ** 2)) + (n_neg - 1) * (q2 - (auc ** 2))) / (n_pos * n_neg)
    se = math.sqrt(max(0.0, var))
    z = 1.95996
    return max(0.0, round(auc - z * se, 4)), min(1.0, round(auc + z * se, 4))


# Backward compatibility alias
compute_delong_ci = compute_hanley_mcneil_ci


def compute_pr_auc_se(pr_auc: float, n_pos: int) -> Tuple[float, float, float]:
    """
    Computes asymptotic standard error and 95% Wald confidence interval for PR-AUC.
    Standard error estimator under asymptotic normality:
    SE = sqrt(PR_AUC * (1 - PR_AUC) / n_pos)
    """
    if n_pos <= 0:
        return 0.0, 0.0, 1.0
    se = math.sqrt(max(0.0, (pr_auc * (1.0 - pr_auc)) / n_pos))
    z = 1.95996
    ci_low = max(0.0, round(pr_auc - z * se, 4))
    ci_high = min(1.0, round(pr_auc + z * se, 4))
    return round(se, 4), ci_low, ci_high


def compute_calibration_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> Tuple[float, float, List[Dict[str, Any]]]:
    """
    Dynamically computes Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
    from empirical probabilities across probability bins.
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, []

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    bin_details = []

    for i in range(n_bins):
        b_low = bins[i]
        b_high = bins[i + 1]
        in_bin = (y_prob >= b_low) & (y_prob < b_high if i < n_bins - 1 else y_prob <= b_high)
        b_size = int(np.sum(in_bin))

        if b_size > 0:
            b_acc = float(np.mean(y_true[in_bin]))
            b_conf = float(np.mean(y_prob[in_bin]))
            gap = abs(b_acc - b_conf)
            ece += (b_size / n) * gap
            mce = max(mce, gap)
            bin_details.append({
                "bin_index": i,
                "range": f"[{b_low:.1f}, {b_high:.1f}]",
                "count": b_size,
                "accuracy": round(b_acc, 4),
                "confidence": round(b_conf, 4),
                "calibration_gap": round(gap, 4)
            })

    return round(float(ece), 4), round(float(mce), 4), bin_details


def compute_population_stability_index(
    expected_scores: Sequence[float],
    actual_scores: Sequence[float],
    n_bins: int = 10
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Computes true Population Stability Index (PSI) across score deciles
    from authentic empirical score distributions.
    PSI = sum((Actual_k - Expected_k) * ln(Actual_k / Expected_k))
    """
    expected = np.asarray(expected_scores, dtype=np.float64)
    actual = np.asarray(actual_scores, dtype=np.float64)

    quantiles = np.linspace(0, 100, n_bins + 1)
    bin_edges = np.percentile(expected, quantiles)
    bin_edges[0] -= 1e-5
    bin_edges[-1] += 1e-5

    exp_counts, _ = np.histogram(expected, bins=bin_edges)
    act_counts, _ = np.histogram(actual, bins=bin_edges)

    exp_pct = exp_counts / max(1, len(expected))
    act_pct = act_counts / max(1, len(actual))

    eps = 1e-4
    psi_total = 0.0
    breakdown = []

    for k in range(len(exp_pct)):
        e = exp_pct[k]
        a = act_pct[k]
        e_adj = max(e, eps)
        a_adj = max(a, eps)
        sub_psi = (a_adj - e_adj) * math.log(a_adj / e_adj)
        psi_total += sub_psi
        breakdown.append({
            "bin": k + 1,
            "expected_pct": round(float(e * 100), 2),
            "actual_pct": round(float(a * 100), 2),
            "sub_psi": round(float(sub_psi), 5)
        })

    return round(float(psi_total), 4), breakdown


def compute_paired_mcnemar_test(
    y_true: Sequence[int],
    y_pred1: Sequence[int],
    y_pred2: Sequence[int]
) -> Tuple[float, float, int, int]:
    """
    Computes true per-observation paired McNemar test with Edwards continuity correction.
    b: cases where Model 1 (Champion) is correct and Model 2 (Challenger) is incorrect
    c: cases where Model 2 (Challenger) is correct and Model 1 (Champion) is incorrect
    """
    yt = np.asarray(y_true, dtype=np.int32)
    p1 = np.asarray(y_pred1, dtype=np.int32)
    p2 = np.asarray(y_pred2, dtype=np.int32)

    m1_correct = (p1 == yt)
    m2_correct = (p2 == yt)

    b = int(np.sum(m1_correct & (~m2_correct)))
    c = int(np.sum((~m1_correct) & m2_correct))

    total_discordant = b + c
    if total_discordant == 0:
        return 0.0, 1.0, b, c

    chi2 = ((abs(b - c) - 1.0) ** 2) / total_discordant
    p_val = math.erfc(math.sqrt(max(0.0, chi2) / 2.0))
    return round(float(chi2), 2), round(float(p_val), 4), b, c


class ValidationEvidenceError(RuntimeError):
    """Raised when per-observation evidence needed for a metric is unavailable."""


# Acceptance thresholds: (metric key, comparator, threshold, display label)
ACCEPTANCE_THRESHOLDS = [
    ("precision", ">=", 0.85, "Precision"),
    ("recall", ">=", 0.80, "Recall"),
    ("roc_auc", ">=", 0.90, "ROC-AUC"),
    ("pr_auc", ">=", 0.85, "PR-AUC"),
    ("brier_score", "<=", 0.05, "Brier Score"),
    ("ece", "<=", 0.025, "ECE (10 bins)"),
]

STATUS_QUALIFIED = "EMPIRICALLY QUALIFIED"
STATUS_SYNTHETIC_CANDIDATE = "INTERNAL SYNTHETIC-DATA BENCHMARK CANDIDATE - NOT EMPIRICALLY QUALIFIED"
STATUS_FAILED = "NOT QUALIFIED - ACCEPTANCE THRESHOLDS NOT MET"
STATUS_UNVERIFIED = "NOT QUALIFIED - DATA PROVENANCE UNVERIFIED"


def compute_binary_metrics(y_true: Sequence[int], y_pred: Sequence[int], y_prob: Sequence[float]) -> Dict[str, Any]:
    """Derive every reported metric from per-observation arrays. No stored or default values."""
    from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

    yt = np.asarray(y_true, dtype=np.int32)
    yp = np.asarray(y_pred, dtype=np.int32)
    pr = np.asarray(y_prob, dtype=np.float64)
    if not (len(yt) == len(yp) == len(pr)) or len(yt) == 0:
        raise ValidationEvidenceError(
            f"Prediction arrays are empty or misaligned (y_true={len(yt)}, preds={len(yp)}, probs={len(pr)})"
        )

    tp = int(np.sum((yt == 1) & (yp == 1)))
    fp = int(np.sum((yt == 0) & (yp == 1)))
    tn = int(np.sum((yt == 0) & (yp == 0)))
    fn = int(np.sum((yt == 1) & (yp == 0)))
    both_classes = len(np.unique(yt)) == 2
    ece, mce, cal_bins = compute_calibration_metrics(yt, pr, n_bins=10)

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "n": int(len(yt)), "n_pos": tp + fn, "n_neg": tn + fp, "n_pred_pos": tp + fp,
        # None (not a default) when the metric is undefined for these arrays.
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "recall": tp / (tp + fn) if (tp + fn) else None,
        "roc_auc": float(roc_auc_score(yt, pr)) if both_classes else None,
        "pr_auc": float(average_precision_score(yt, pr)) if both_classes else None,
        "brier_score": float(brier_score_loss(yt, pr)),
        "ece": ece,
        "mce": mce,
        "calibration_bins": cal_bins,
    }


def evaluate_thresholds(metrics: Dict[str, Any]) -> Dict[str, str]:
    verdicts = {}
    for key, op, thr, _ in ACCEPTANCE_THRESHOLDS:
        val = metrics.get(key)
        if val is None:
            verdicts[key] = "UNDEFINED"
        elif (val >= thr) if op == ">=" else (val <= thr):
            verdicts[key] = "MEETS THRESHOLD"
        else:
            verdicts[key] = "FAILS THRESHOLD"
    return verdicts


def determine_qualification_status(
    provenance: Optional[Dict[str, Any]],
    verdicts: Dict[str, str],
    champion: Dict[str, Any],
    mcnemar_discordant: int,
    external_validation: Optional[Dict[str, Any]] = None,
) -> Tuple[str, List[str]]:
    """
    Derive the qualification status and the reasons for it from evidence.
    EMPIRICALLY QUALIFIED requires a passing, independent external validation on
    non-simulated data; internal metrics on generated data can never earn it.
    """
    reasons: List[str] = []

    if any(v != "MEETS THRESHOLD" for v in verdicts.values()):
        failed = [k for k, v in verdicts.items() if v != "MEETS THRESHOLD"]
        reasons.append(f"Champion does not meet acceptance thresholds for: {', '.join(failed)}.")
        status = STATUS_FAILED
    elif not provenance or provenance.get("contains_real_world_data") is None:
        reasons.append("Holdout data provenance could not be determined.")
        status = STATUS_UNVERIFIED
    else:
        status = STATUS_SYNTHETIC_CANDIDATE

    if provenance:
        frac = provenance.get("generated_synthetic_fraction")
        if frac is not None:
            reasons.append(
                f"{frac * 100:.1f}% of the holdout was produced by the in-repo synthetic generator "
                f"(`generate_synthetic_aml_stream`); the remainder is AMLSim-style simulated data."
            )
        if provenance.get("contains_real_world_data") is False:
            reasons.append("No real-world transaction data is present in the evaluation partition.")

    if champion.get("fp") == 0 and champion.get("fn") == 0 and champion.get("roc_auc") == 1.0:
        reasons.append(
            "Perfect separation (zero errors, ROC-AUC = 1.0) reflects how the synthetic generator draws "
            "fraud and benign samples from distinct feature distributions; it is not evidence of "
            "real-world discrimination performance."
        )
    if mcnemar_discordant == 0:
        reasons.append(
            "Champion and challenger made identical classifications on every holdout case, so the paired "
            "McNemar test is uninformative and provides no evidence that the champion is superior."
        )

    ext = external_validation or {}
    ext_ok = (
        status == STATUS_SYNTHETIC_CANDIDATE
        and ext.get("passed") is True
        and ext.get("independent") is True
        and ext.get("contains_real_world_data") is True
    )
    if ext_ok:
        status = STATUS_QUALIFIED
        reasons.append(f"Independent external validation passed: {ext.get('reference', 'see external_validation record')}.")
    elif status == STATUS_SYNTHETIC_CANDIDATE:
        reasons.append(
            "No independent external validation on real-world data is recorded; empirical qualification "
            "cannot be claimed until one is performed."
        )
    return status, reasons


def _reconstruct_holdout_provenance(y_true: np.ndarray) -> Optional[Dict[str, Any]]:
    """Rebuild the deterministic split to recover holdout provenance for older reports."""
    try:
        from ml.dataset import load_amlsim_tabular_dataset, summarize_provenance
        ds = load_amlsim_tabular_dataset(seed=42)
        _, test_ds = ds.split(test_size=0.25, seed=42)
        if len(test_ds.y) != len(y_true) or not np.array_equal(test_ds.y, y_true):
            return None  # Cannot prove the reconstructed split is the evaluated one.
        return summarize_provenance(test_ds.case_ids)
    except Exception:
        return None


def _load_holdout_evidence(training_report: Dict[str, Any], registry, prod_model_meta, staging_models) -> Dict[str, Any]:
    holdout = training_report.get("holdout_evaluation", {})
    ev = {
        "y_true": np.asarray(holdout.get("y_true", [])),
        "champ_preds": np.asarray(holdout.get("champion_predictions", [])),
        "champ_probs": np.asarray(holdout.get("champion_probabilities", [])),
        "chall_preds": np.asarray(holdout.get("challenger_predictions", [])),
        "chall_probs": np.asarray(holdout.get("challenger_probabilities", [])),
        "train_scores": np.asarray(holdout.get("train_scores", [])),
        "test_scores": np.asarray(holdout.get("test_scores", [])),
        "source": "persisted training report (backend/ml/training_report.json)",
    }
    if len(ev["y_true"]) > 0:
        return ev

    # Recompute live on the deterministic test split; fail if artifacts are missing.
    from ml.dataset import load_amlsim_tabular_dataset
    import joblib
    ds = load_amlsim_tabular_dataset(seed=42)
    train_ds, test_ds = ds.split(test_size=0.25, seed=42)
    prod_path = registry.resolve_artifact_path(prod_model_meta.get("artifact_path", "lightgbm_fraud_detector_v1.joblib"))
    base_meta = staging_models[0] if staging_models else {}
    base_path = registry.resolve_artifact_path(base_meta.get("artifact_path", "baseline_logistic_regression_v1.joblib"))
    if not (os.path.exists(prod_path) and os.path.exists(base_path)):
        raise ValidationEvidenceError(
            "No persisted holdout arrays and model artifacts are missing; refusing to report metrics without evidence."
        )
    prod_m = joblib.load(prod_path)
    base_m = joblib.load(base_path)
    champ_probs = prod_m.predict_proba(test_ds.X)[:, 1]
    chall_probs = base_m.predict_proba(test_ds.X)[:, 1]
    return {
        "y_true": test_ds.y,
        "champ_preds": (champ_probs >= 0.50).astype(int),
        "champ_probs": champ_probs,
        "chall_preds": (chall_probs >= 0.50).astype(int),
        "chall_probs": chall_probs,
        "train_scores": prod_m.predict_proba(train_ds.X)[:, 1],
        "test_scores": champ_probs,
        "source": "live recomputation on deterministic test split (seed=42)",
    }


def _fmt_pct(v: Optional[float]) -> str:
    return "undefined" if v is None else f"{v * 100:.1f}%"


def _fmt_num(v: Optional[float], digits: int = 3) -> str:
    return "undefined" if v is None else f"{v:.{digits}f}"


def generate_validation_pack(output_path: str = DEFAULT_DOC_PATH, training_report_path: str = TRAINING_REPORT_PATH) -> str:
    registry = ModelRegistry()
    manifest = registry._load_manifest()
    prod_id = manifest.get("active_production_model_id", "lightgbm_fraud_detector_v1")
    models = manifest.get("models", {})
    prod_model_meta = models.get(prod_id, {})
    staging_models = [m for k, m in models.items() if k != prod_id]

    training_report: Dict[str, Any] = {}
    if os.path.exists(training_report_path):
        with open(training_report_path, "r", encoding="utf-8") as f:
            training_report = json.load(f)

    ev = _load_holdout_evidence(training_report, registry, prod_model_meta, staging_models)
    y_true = ev["y_true"]

    champ = compute_binary_metrics(y_true, ev["champ_preds"], ev["champ_probs"])
    chall = compute_binary_metrics(y_true, ev["chall_preds"], ev["chall_probs"])
    verdicts = evaluate_thresholds(champ)

    mcnemar_chi2, mcnemar_p, b_cases, c_cases = compute_paired_mcnemar_test(y_true, ev["champ_preds"], ev["chall_preds"])
    p_display = "< 0.0001" if mcnemar_p < 0.0001 else f"= {mcnemar_p:.4f}"
    if b_cases + c_cases == 0:
        mcnemar_verdict = ("Uninformative: the two models made identical classifications on every case. "
                           "This is not evidence that the champion outperforms the challenger.")
    elif mcnemar_p < 0.05:
        better = "champion" if b_cases > c_cases else "challenger"
        mcnemar_verdict = f"Significant difference at alpha = 0.05 favouring the {better}."
    else:
        mcnemar_verdict = "No statistically significant difference at alpha = 0.05."

    ds_meta = training_report.get("dataset", {})
    provenance = ds_meta.get("holdout_provenance") or _reconstruct_holdout_provenance(y_true)
    full_provenance = ds_meta.get("provenance")

    status, reasons = determine_qualification_status(
        provenance, verdicts, champ, b_cases + c_cases, training_report.get("external_validation")
    )

    # Confidence intervals from actual counts
    prec_ci = wilson_score_interval(champ["tp"], champ["n_pred_pos"]) if champ["n_pred_pos"] else None
    rec_ci = wilson_score_interval(champ["tp"], champ["n_pos"]) if champ["n_pos"] else None
    auc_ci = compute_hanley_mcneil_ci(champ["roc_auc"], champ["n_pos"], champ["n_neg"]) if champ["roc_auc"] is not None else None
    pr_se = compute_pr_auc_se(champ["pr_auc"], champ["n_pos"]) if champ["pr_auc"] is not None else None

    def ci_str(ci, label):
        if ci is None:
            return "undefined"
        note = " (degenerate: zero width at a boundary estimate)" if ci[0] == ci[1] else ""
        return f"[{ci[0]:.3f}, {ci[1]:.3f}] {label}{note}"

    ci_cells = {
        "precision": ci_str(prec_ci, f"Wilson, n={champ['n_pred_pos']}"),
        "recall": ci_str(rec_ci, f"Wilson, n={champ['n_pos']}"),
        "roc_auc": ci_str(auc_ci, "Hanley-McNeil"),
        "pr_auc": ci_str(pr_se[1:] if pr_se else None, "Wald"),
        "brier_score": "N/A",
        "ece": f"MCE = {champ['mce']:.4f}",
    }

    rows = []
    for key, op, thr, label in ACCEPTANCE_THRESHOLDS:
        pct = key in ("precision", "recall")
        digits = 4 if key in ("brier_score", "ece") else 3
        fmt = _fmt_pct if pct else (lambda v, d=digits: _fmt_num(v, d))
        thr_s = f"{op} {thr * 100:.1f}%" if pct else f"{op} {thr}"
        rows.append(f"| **{label}** | **{fmt(champ[key])}** | {ci_cells[key]} | {fmt(chall[key])} | {thr_s} | {verdicts[key]} |")
    metrics_table = "\n".join(rows)

    # PSI: train vs. holdout scores from the same random split
    if len(ev["train_scores"]) and len(ev["test_scores"]):
        psi_metric, _ = compute_population_stability_index(ev["train_scores"], ev["test_scores"], n_bins=10)
        psi_band = "stable (< 0.10)" if psi_metric < 0.10 else ("moderate shift (0.10-0.25)" if psi_metric < 0.25 else "significant shift (> 0.25)")
        psi_section = (
            f"   - PSI between training scores ($N={len(ev['train_scores'])}$) and holdout scores "
            f"($N={len(ev['test_scores'])}$): **`{psi_metric}`** - {psi_band}.\n"
            f"   - Scope: both partitions come from one random split of the same dataset, so this checks split "
            f"consistency only. It is not evidence of stability against production traffic, which requires "
            f"monitoring live score distributions."
        )
    else:
        psi_section = "   - Not computed: no training/holdout score arrays are available."

    stress = training_report.get("stress_tests")
    if stress:
        stress_rows = "\n".join(
            f"| {s.get('scenario')} | {s.get('perturbation')} | {s.get('f1_delta')} | {s.get('ece_delta')} | {s.get('status')} |"
            for s in stress
        )
        stress_section = ("| Scenario | Perturbation | F1 Change | ECE Change | Status |\n"
                          "| :--- | :--- | :--- | :--- | :--- |\n" + stress_rows)
    else:
        stress_section = (
            "**Not performed.** No stress-test results are recorded in the training report. Earlier versions of "
            "this document listed stress-test figures that were not produced by any executed test; they have "
            "been removed."
        )

    def prov_lines(p: Optional[Dict[str, Any]], label: str) -> str:
        if not p:
            return f"- **{label}:** provenance unavailable"
        srcs = ", ".join(f"{k}: {v}" for k, v in p.get("by_source", {}).items())
        frac = p.get("generated_synthetic_fraction")
        frac_s = "unknown" if frac is None else f"{frac * 100:.1f}%"
        return (f"- **{label}:** N = {p.get('total')} ({srcs}); generated-synthetic share = {frac_s}; "
                f"real-world data present = {p.get('contains_real_world_data')}")

    reasons_md = "\n".join(f"- {r}" for r in reasons)
    now = datetime.datetime.now(datetime.timezone.utc)

    report = f"""# Model Risk Management (MRM) Validation Pack
**Document ID:** MRM-VAL-FFIRE-{now.strftime('%Y%m%d')}
**Reference Frameworks:** Federal Reserve SR 11-7 & OCC Bulletin 2011-12 (structure only; this document is not an independent validation)
**System:** Financial Fraud Investigation Reasoning Engine (FFIRE)
**Date of Generation:** {now.isoformat()}
**Validation Status:** {status}
**Evidence Source:** {ev['source']}

> [!WARNING]
> **Why this status:**
{chr(10).join('> ' + line for line in reasons_md.splitlines())}

---

## 1. Model Inventory Entry
- **Model Name:** Calibrated LightGBM GBDT Fraud Classifier
- **Model Identifier:** `{prod_id}`
- **Model Version:** `{prod_model_meta.get('version', 'UNRECORDED')}`
- **Lifecycle Stage (registry):** `{prod_model_meta.get('stage', 'UNRECORDED')}`
- **Production Artifact Digest (SHA-256):** `{prod_model_meta.get('sha256', 'UNAVAILABLE')}`
- **Intended Use:** Post-transaction fraud investigation decision support and human-in-the-loop triage ranking.
- **Out-of-Scope Use:** Autonomous inline payment interdiction; automated regulatory filing.

---

## 2. Data Provenance
{prov_lines(full_provenance, 'Full dataset')}
{prov_lines(provenance, 'Holdout partition')}

All current data sources are simulated: the in-repo generator draws fraud and benign samples from deliberately
different feature distributions (KYC status, risk tier, velocity, graph signals), and the remaining cases are
AMLSim-style simulated scenarios. Metrics below therefore measure how well the model recovers the generator's
rules, not real-world fraud detection performance.

---

## 3. Conceptual Soundness
FFIRE combines gradient boosted decision trees with Platt sigmoid calibration
(`CalibratedClassifierCV(method="sigmoid", cv=3)`):
$$\\hat{{P}}(Y=1 | X) = \\frac{{1}}{{1 + \\exp(A \\cdot f(X) + B)}}$$
The production model consumes {len(prod_model_meta.get('feature_names', []))} engineered features (velocity, amount ratios,
graph topology, structuring heuristics, and entity context).

---

## 4. Holdout Performance (internal, synthetic-data benchmark)
Every value below is computed from per-observation prediction arrays ($N = {champ['n']}$, positives = {champ['n_pos']},
negatives = {champ['n_neg']}). No stored or default metric values are used.

### Champion Confusion Matrix
- **TP:** {champ['tp']} | **FP:** {champ['fp']} | **TN:** {champ['tn']} | **FN:** {champ['fn']}

| Metric | Champion (`{prod_id}`) | 95% CI | Challenger (Logistic Regression) | Threshold | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
{metrics_table}

Meeting these thresholds on this holdout is a necessary internal check, not a qualification.

### Champion vs. Challenger (paired McNemar, Edwards continuity correction)
- Champion correct / challenger wrong ($b$): **{b_cases}**
- Challenger correct / champion wrong ($c$): **{c_cases}**
- $\\chi^2 = {mcnemar_chi2}$, $p {p_display}$
- **Interpretation:** {mcnemar_verdict}

---

## 5. Sensitivity Analysis & Stress Testing
{stress_section}

---

## 6. Monitoring & Governance Controls
1. **Population Stability Index (PSI):**
{psi_section}
2. **Artifact Integrity:** the registry recomputes each artifact's SHA-256 and compares it with the manifest before
   loading it with joblib. This detects tampering with the artifact file; it does not make untrusted pickles safe.
3. **Audit Trail:** model scores and top feature attributions are written to the SHA-256 chained audit log.

---

## 7. Required Before Empirical Qualification
1. Independent validation on real (or contractually representative) labelled transaction data.
2. Out-of-time evaluation rather than a single random split.
3. Executed stress tests with recorded results.
4. A challenger evaluation in which the models actually disagree, so that superiority can be tested.

---
*Generated by `scripts/generate_model_validation_kit.py`. Status and every metric are derived from recorded evidence.*
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"[*] MRM Validation Pack generated at: {output_path} (status: {status})")
    return report


if __name__ == "__main__":
    try:
        generate_validation_pack()
    except ValidationEvidenceError as exc:
        print(f"[!] Validation pack NOT generated: {exc}", file=sys.stderr)
        sys.exit(2)
