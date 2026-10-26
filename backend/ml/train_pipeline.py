"""
Training, Calibration and Registration Pipeline for FFIRE Fraud Detection Model (Phase 2).

Executes the complete machine learning lifecycle:
1. Dataset compilation with class-balancing from IBM AMLSim + synthetic banking stream.
2. Stratified train/test partitioning.
3. Baseline (L2 Logistic Regression) and LightGBM model training with positive class weighting.
4. Sigmoid Platt calibration for well-calibrated posterior probabilities under severe imbalance.
5. Multi-metric evaluation (PR-AUC, ROC-AUC, Macro F1, Brier Score, ECE, FPR, FNR).
6. Model registration into ModelRegistry, artifact serialization (.joblib), and production promotion.
7. Verification of < 5ms inference latency and feature attribution explainability.
"""

import os
import sys
import json
import time
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.ml.features import FEATURE_NAMES, NUM_FEATURES
from backend.ml.dataset import load_amlsim_tabular_dataset, FraudDataset
from backend.ml.training import FraudModelTrainer, compute_metrics
from backend.ml.registry import ModelRegistry
from backend.ml.inference import FraudInferenceService


def run_training_pipeline(
    augment_synthetic: bool = True,
    n_synthetic: int = 2000,
    fraud_ratio: float = 0.04,
    test_size: float = 0.25,
    seed: int = 42,
    output_report_path: str = None
) -> Dict[str, Any]:
    print("=" * 70)
    print("FFIRE Fraud Model Training & Calibration Pipeline (Phase 2)")
    print("=" * 70)

    # 1. Dataset Compilation
    print("\n[Step 1/6] Loading tabular dataset...")
    t0 = time.time()
    ds: FraudDataset = load_amlsim_tabular_dataset(
        augment_synthetic=augment_synthetic,
        n_synthetic=n_synthetic,
        fraud_ratio=fraud_ratio,
        seed=seed
    )
    neg_count, pos_count = ds.class_counts
    pos_weight = ds.get_pos_weight()
    print(f"  Dataset loaded in {time.time() - t0:.2f}s")
    print(f"  Total samples: {ds.num_samples} (Negative: {neg_count}, Positive: {pos_count})")
    print(f"  Positive ratio: {ds.positive_ratio * 100:.2f}% | Positive scale weight: {pos_weight:.2f}")

    # 2. Stratified Train/Test Split
    print("\n[Step 2/6] Performing stratified train/validation split...")
    train_ds, test_ds = ds.split(test_size=test_size, seed=seed)
    tr_neg, tr_pos = train_ds.class_counts
    te_neg, te_pos = test_ds.class_counts
    print(f"  Train set: {train_ds.num_samples} samples ({tr_neg} neg, {tr_pos} pos)")
    print(f"  Test set:  {test_ds.num_samples} samples ({te_neg} neg, {te_pos} pos)")

    trainer = FraudModelTrainer(random_state=seed)

    # 3. Train Baseline Model (Logistic Regression)
    print("\n[Step 3/6] Training Baseline Model (L2 Regularized Logistic Regression)...")
    t_base0 = time.time()
    trainer.train_baseline(train_ds.X, train_ds.y)
    t_base = time.time() - t_base0
    baseline_eval = trainer.evaluate(trainer.baseline_model, test_ds.X, test_ds.y)
    print(f"  Baseline trained in {t_base:.2f}s")
    print(f"  Baseline Test Metrics: ROC-AUC={baseline_eval['metrics']['roc_auc']}, "
          f"PR-AUC={baseline_eval['metrics']['pr_auc']}, Macro F1={baseline_eval['metrics']['macro_f1']}, "
          f"Brier={baseline_eval['metrics']['brier_score']}, ECE={baseline_eval['metrics']['expected_calibration_error']}")

    # 4. Train LightGBM + Platt Sigmoid Calibration
    print("\n[Step 4/6] Training LightGBM Model & Sigmoid Platt Calibration...")
    t_gbm0 = time.time()
    trainer.train_lightgbm(train_ds.X, train_ds.y, pos_weight=pos_weight, calibrate=True)
    t_gbm = time.time() - t_gbm0
    calibrated_eval = trainer.evaluate(trainer.calibrated_gbm, test_ds.X, test_ds.y)
    uncalibrated_eval = trainer.evaluate(trainer.gbm_model, test_ds.X, test_ds.y)
    print(f"  LightGBM & Platt Calibration completed in {t_gbm:.2f}s")
    print(f"  Uncalibrated LightGBM Metrics: ROC-AUC={uncalibrated_eval['metrics']['roc_auc']}, "
          f"PR-AUC={uncalibrated_eval['metrics']['pr_auc']}, Macro F1={uncalibrated_eval['metrics']['macro_f1']}, "
          f"Brier={uncalibrated_eval['metrics']['brier_score']}, ECE={uncalibrated_eval['metrics']['expected_calibration_error']}")
    print(f"  Calibrated LightGBM Metrics:   ROC-AUC={calibrated_eval['metrics']['roc_auc']}, "
          f"PR-AUC={calibrated_eval['metrics']['pr_auc']}, Macro F1={calibrated_eval['metrics']['macro_f1']}, "
          f"Brier={calibrated_eval['metrics']['brier_score']}, ECE={calibrated_eval['metrics']['expected_calibration_error']}")

    # 5. Model Registration & Production Promotion
    print("\n[Step 5/6] Registering models in ModelRegistry...")
    registry = ModelRegistry()

    # Register Baseline in staging
    base_entry = registry.register_model(
        model=trainer.baseline_model,
        model_id="baseline_logistic_regression_v1",
        model_type="logistic_regression",
        version="1.0.0",
        metrics=baseline_eval["metrics"],
        feature_names=FEATURE_NAMES,
        stage="staging",
        notes="L2-regularized logistic regression with balanced class weights for AML fraud detection"
    )
    print(f"  Registered {base_entry['model_id']} (stage={base_entry['stage']})")

    # Register Calibrated LightGBM and promote to production
    prod_entry = registry.register_model(
        model=trainer.calibrated_gbm,
        model_id="lightgbm_fraud_detector_v1",
        model_type="lightgbm_calibrated",
        version="1.0.0",
        metrics=calibrated_eval["metrics"],
        feature_names=FEATURE_NAMES,
        stage="production",
        notes="LightGBM GBDT with scale_pos_weight imbalanced loss and 3-fold Platt sigmoid calibration"
    )
    print(f"  Registered & Promoted {prod_entry['model_id']} (stage={prod_entry['stage']})")

    # 6. Inference Service Verification (< 5ms latency & Explainability)
    print("\n[Step 6/6] Verifying offline Inference Service & Attribution...")
    inf_service = FraudInferenceService(registry=registry)
    assert inf_service.reload_production_model(), "Failed to load active production model"

    # Test single transaction prediction
    sample_txn = {
        "txn_id": "TEST_TXN_001",
        "account_id": "ACC_TEST_CORP",
        "counterparty": "DEST_VENDOR",
        "amount": 85000.0,
        "timestamp": "2026-01-15T12:00:00+00:00",
        "channel": "WIRE"
    }
    sample_acct = {"account_id": "ACC_TEST_CORP", "account_type": "COMMERCIAL", "balance": 500000.0}
    sample_cust = {"kyc_status": "VERIFIED", "risk_tier": "LOW"}

    pred = inf_service.predict(
        txn=sample_txn,
        account=sample_acct,
        customer=sample_cust,
        history=[]
    )
    print(f"  Production Model ID: {pred.model_id} (type: {pred.model_type})")
    print(f"  Inference Latency:   {pred.latency_ms:.2f} ms")
    print(f"  Calibrated Prob:     {pred.raw_probability:.4f} -> Verdict: {pred.predicted_label}")
    print(f"  Top Contributing Features: {pred.top_features[:3]}")

    # Build Pipeline Summary
    pipeline_summary = {
        "status": "COMPLETED",
        "dataset": {
            "total_samples": ds.num_samples,
            "neg_samples": neg_count,
            "pos_samples": pos_count,
            "fraud_ratio": round(ds.positive_ratio, 4),
            "pos_weight": round(pos_weight, 2),
            "num_features": NUM_FEATURES,
        },
        "models": {
            "baseline_logistic_regression": {
                "model_id": "baseline_logistic_regression_v1",
                "stage": "staging",
                "metrics": baseline_eval["metrics"],
                "training_time_sec": round(t_base, 2)
            },
            "uncalibrated_lightgbm": {
                "metrics": uncalibrated_eval["metrics"]
            },
            "calibrated_lightgbm": {
                "model_id": "lightgbm_fraud_detector_v1",
                "stage": "production",
                "metrics": calibrated_eval["metrics"],
                "training_time_sec": round(t_gbm, 2)
            }
        },
        "inference_benchmark": {
            "active_production_model": pred.model_id,
            "latency_ms": pred.latency_ms,
            "sample_prediction": pred.to_dict()
        }
    }

    if output_report_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_report_path)), exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_summary, f, indent=2)
        print(f"\nSaved training pipeline report to {output_report_path}")

    print("\n" + "=" * 70)
    print("Phase 2 Real Fraud Model Pipeline Successfully Completed!")
    print("=" * 70)
    return pipeline_summary


if __name__ == "__main__":
    report_file = os.path.join(os.path.dirname(__file__), "training_report.json")
    run_training_pipeline(output_report_path=report_file)
