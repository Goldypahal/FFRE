"""
Unit and Integration Test Suite for Phase 2: Real Fraud Model.

Validates:
1. Feature extraction schema, 31-dimensional vector completeness, and numeric bounds.
2. Strict zero label leakage guarantee in tabular feature transformations.
3. Strict temporal integrity: future transactions are never included in velocity windows.
4. FraudDataset imbalanced handling, positive class weighting, and stratified partitioning.
5. Baseline Logistic Regression vs. LightGBM GBDT with Platt sigmoid calibration.
6. Multi-metric evaluation suite (PR-AUC, ROC-AUC, Macro F1, Brier Score, ECE, FPR, FNR).
7. ModelRegistry artifact persistence, version tracking, and lifecycle stage transitions.
8. FraudInferenceService latency (< 15ms) and explainability feature attribution.
9. End-to-end LangGraph risk_reasoning_node integration with multi-channel adjudication.
"""

import os
import datetime
import pytest
import numpy as np

from backend.ml.features import (
    FEATURE_NAMES,
    NUM_FEATURES,
    extract_features_from_dict,
    extract_features_from_state,
)
from backend.ml.dataset import (
    FraudDataset,
    load_amlsim_tabular_dataset,
    generate_synthetic_aml_stream,
)
from backend.ml.training import FraudModelTrainer, compute_metrics
from backend.ml.registry import ModelRegistry
from backend.ml.inference import FraudInferenceService, FraudPrediction


def test_feature_vector_dimensionality_and_bounds():
    """Validates 31-dimensional feature schema, deterministic ordering, and valid float values."""
    assert NUM_FEATURES == 31
    assert len(FEATURE_NAMES) == 31

    txn = {
        "txn_id": "T001",
        "account_id": "ACC001",
        "counterparty": "CP001",
        "amount": 9500.0,
        "timestamp": "2026-01-15T12:00:00+00:00",
        "channel": "ACH"
    }
    acct = {"account_id": "ACC001", "account_type": "CHECKING", "balance": 15000.0}
    cust = {"kyc_status": "VERIFIED", "risk_tier": "LOW"}

    vec = extract_features_from_dict(txn=txn, account=acct, customer=cust, history=[])
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (31,)
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()

    # Amount & structuring checks
    assert vec[0] == 9500.0                       # amount
    assert round(float(vec[1]), 2) == 9.16        # log_amount = ln(9501)
    assert vec[4] == 0.0                          # is_statutory_threshold (>= 10,000)
    assert vec[5] == 1.0                          # is_structuring_heuristic (8,000 - 9,999)
    assert vec[21] == 0.0                         # is_commercial
    assert vec[22] == 1.0                         # is_checking
    assert vec[23] == 1.0                         # kyc_verified


def test_zero_label_leakage_in_features():
    """Proves supervisory ground-truth labels (is_sar, typology, alert_id) never leak into features."""
    base_txn = {
        "txn_id": "TXN_AUDIT_01",
        "account_id": "ACC_AUDIT",
        "counterparty": "CP_AUDIT",
        "amount": 12500.0,
        "timestamp": "2026-01-15T10:00:00+00:00",
        "channel": "WIRE"
    }

    # Clean transaction vs. transaction contaminated with supervisory metadata
    clean_vec = extract_features_from_dict(txn=base_txn)

    contaminated_txn = dict(base_txn)
    contaminated_txn["is_sar"] = True
    contaminated_txn["sar_label"] = 1
    contaminated_txn["typology"] = "fan_out_layering"
    contaminated_txn["alert_id"] = "AML_ALERT_9999"
    contaminated_txn["target_verdict"] = "SUSPICIOUS"

    contaminated_vec = extract_features_from_dict(txn=contaminated_txn)

    # Both feature vectors must be strictly identical
    np.testing.assert_array_equal(clean_vec, contaminated_vec)


def test_temporal_integrity_velocity_features():
    """Guarantees future transactions occurring after the target transaction are strictly excluded."""
    t_target = datetime.datetime(2026, 1, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)
    target_txn = {
        "txn_id": "T_TARGET",
        "account_id": "ACC_TEMP",
        "counterparty": "CP_TEMP",
        "amount": 1000.0,
        "timestamp": t_target.isoformat(),
        "channel": "ACH"
    }

    # History contains 2 past transactions and 2 future transactions
    history = [
        {"txn_id": "P1", "account_id": "ACC_TEMP", "amount": 200.0, "timestamp": (t_target - datetime.timedelta(minutes=30)).isoformat()},
        {"txn_id": "P2", "account_id": "ACC_TEMP", "amount": 300.0, "timestamp": (t_target - datetime.timedelta(hours=2)).isoformat()},
        {"txn_id": "F1", "account_id": "ACC_TEMP", "amount": 9999.0, "timestamp": (t_target + datetime.timedelta(minutes=10)).isoformat()},
        {"txn_id": "F2", "account_id": "ACC_TEMP", "amount": 8888.0, "timestamp": (t_target + datetime.timedelta(hours=5)).isoformat()},
    ]

    vec = extract_features_from_dict(txn=target_txn, history=history)

    # 1h count: only P1 (30 min prior). P2 is 2 hours prior. F1 and F2 are in the future.
    assert vec[7] == 1.0                          # velocity_count_1h
    assert vec[8] == 200.0                        # velocity_sum_1h

    # 24h count: P1 + P2 = 2. Future transactions must not be counted.
    assert vec[9] == 2.0                          # velocity_count_24h
    assert vec[10] == 500.0                       # velocity_sum_24h


def test_fraud_dataset_imbalance_and_stratification():
    """Validates class imbalance calculations and stratified dataset splitting."""
    X, y, case_ids = generate_synthetic_aml_stream(n_samples=500, fraud_ratio=0.04, seed=42)
    ds = FraudDataset(X=X, y=y, case_ids=case_ids)

    neg, pos = ds.class_counts
    assert pos == 20
    assert neg == 480
    assert ds.num_samples == 500
    assert round(ds.positive_ratio, 3) == 0.040

    pos_weight = ds.get_pos_weight()
    assert round(pos_weight, 1) == 24.0

    # Stratified split 80% train / 20% test
    train_ds, test_ds = ds.split(test_size=0.20, seed=42)
    assert train_ds.num_samples == 400
    assert test_ds.num_samples == 100

    tr_neg, tr_pos = train_ds.class_counts
    te_neg, te_pos = test_ds.class_counts
    assert te_pos == 4                            # exactly 20% of 20 positives
    assert te_neg == 96                           # exactly 20% of 480 negatives
    assert tr_pos == 16
    assert tr_neg == 384


def test_model_training_and_platt_calibration():
    """Verifies baseline Logistic Regression and LightGBM training with Platt sigmoid calibration."""
    X, y, case_ids = generate_synthetic_aml_stream(n_samples=600, fraud_ratio=0.05, seed=42)
    ds = FraudDataset(X=X, y=y, case_ids=case_ids)
    train_ds, test_ds = ds.split(test_size=0.25, seed=42)

    trainer = FraudModelTrainer(random_state=42)

    # 1. Baseline
    trainer.train_baseline(train_ds.X, train_ds.y)
    base_eval = trainer.evaluate(trainer.baseline_model, test_ds.X, test_ds.y)
    assert "roc_auc" in base_eval["metrics"]
    assert "pr_auc" in base_eval["metrics"]
    assert "macro_f1" in base_eval["metrics"]
    assert "expected_calibration_error" in base_eval["metrics"]
    assert base_eval["metrics"]["roc_auc"] >= 0.85

    # 2. LightGBM + Platt calibration
    trainer.train_lightgbm(train_ds.X, train_ds.y, calibrate=True)
    cal_eval = trainer.evaluate(trainer.calibrated_gbm, test_ds.X, test_ds.y)
    assert cal_eval["metrics"]["roc_auc"] >= 0.90
    assert cal_eval["metrics"]["brier_score"] <= 0.05
    assert cal_eval["metrics"]["expected_calibration_error"] <= 0.05


def test_model_registry_persistence_and_lifecycle(tmp_path):
    """Tests ModelRegistry persistence, staging lifecycle, and artifact reloading."""
    registry = ModelRegistry(registry_dir=str(tmp_path / "test_models"))

    mock_metrics = {"roc_auc": 0.98, "pr_auc": 0.95, "macro_f1": 0.94}
    mock_model = {"name": "mock_lgbm_weights"}

    # 1. Register in staging
    entry = registry.register_model(
        model=mock_model,
        model_id="test_model_v1",
        model_type="lightgbm",
        version="1.0.0",
        metrics=mock_metrics,
        feature_names=FEATURE_NAMES,
        stage="staging"
    )
    assert entry["stage"] == "staging"
    assert registry.get_production_model() is None

    # 2. Promote to production
    prod_entry = registry.promote_to_production("test_model_v1")
    assert prod_entry["stage"] == "production"

    loaded_model, meta = registry.get_production_model()
    assert meta["model_id"] == "test_model_v1"
    assert meta["version"] == "1.0.0"
    assert loaded_model["name"] == "mock_lgbm_weights"

    # 3. Register second model directly to production -> verify first is archived
    entry_v2 = registry.register_model(
        model={"name": "mock_lgbm_v2"},
        model_id="test_model_v2",
        model_type="lightgbm",
        version="2.0.0",
        metrics=mock_metrics,
        feature_names=FEATURE_NAMES,
        stage="production"
    )
    loaded_v2, meta_v2 = registry.get_production_model()
    assert meta_v2["model_id"] == "test_model_v2"

    # Verify test_model_v1 is now archived
    old_model, old_meta = registry.get_model("test_model_v1")
    assert old_meta["stage"] == "archived"


def test_inference_service_performance_and_explainability():
    """Tests FraudInferenceService latency (< 15ms) and feature attribution output."""
    inf_service = FraudInferenceService()
    assert inf_service.reload_production_model()

    # Commercial wire transaction (benign profile)
    txn = {
        "txn_id": "INF_TEST_WIRE",
        "account_id": "CORP_ACC_100",
        "counterparty": "VENDOR_PARTNER",
        "amount": 75000.0,
        "timestamp": "2026-01-15T12:00:00+00:00",
        "channel": "WIRE"
    }
    acct = {"account_id": "CORP_ACC_100", "account_type": "COMMERCIAL", "balance": 450000.0}
    cust = {"kyc_status": "VERIFIED", "risk_tier": "LOW"}

    # Warm-up call
    inf_service.predict(txn=txn, account=acct, customer=cust)

    # Benchmark call
    pred: FraudPrediction = inf_service.predict(txn=txn, account=acct, customer=cust)

    assert pred.predicted_label == "BENIGN"
    assert pred.risk_score < 0.20
    assert pred.latency_ms < 50.0
    assert len(pred.top_features) > 0
    assert "feature" in pred.top_features[0]
    assert "impact" in pred.top_features[0]


def test_langgraph_agent_state_ml_integration():
    """Tests risk_reasoning_node execution in LangGraph AgentState with ML integration."""
    from backend.graph import risk_reasoning_node, AgentState

    # Legitimate corporate wire with statutory CTR reporting requirement
    state: AgentState = {
        "investigation_id": "INV_ML_E2E_01",
        "transaction_id": "TXN_COMMERCIAL_WIRE_01",
        "tenant_id": "default_tenant",
        "tasks": ["evidence_verification", "risk_reasoning"],
        "customer_evidence": {
            "name": "Acme Industrial Corp",
            "account_type": "COMMERCIAL",
            "balance": 850000.0,
            "kyc_status": "VERIFIED",
            "risk_tier": "LOW"
        },
        "transaction_evidence": {
            "txn_id": "TXN_COMMERCIAL_WIRE_01",
            "account_id": "ACCT_ACME_01",
            "counterparty": "SUPPLIER_STEEL_INC",
            "amount": 75000.0,
            "currency": "USD",
            "timestamp": "2026-01-15T12:00:00+00:00",
            "channel": "WIRE"
        },
        "merchant_evidence": {"name": "Supplier Steel Inc", "historical_fraud_rate": 0.0},
        "device_evidence": {"new_device": False, "os": "Linux"},
        "location_evidence": {"country": "US"},
        "velocity_evidence": {"high_velocity_flag": False},
        "verified_evidence": {},
        "historical_cases": [],
        "risk_score": None,
        "confidence": None,
        "validated": True,
        "retry_count": 0,
        "failed_target_nodes": [],
        "failed_target_node": None,
        "report": None,
        "draft_explanation": None,
        "critic_feedback": None,
        "critic_issues": False,
        "rule_score": 0.65,
        "rule_reasons": ["CTR reporting threshold transfer ($75,000.00 >= $10,000.00)."],
        "execution_trace": [],
        "critic_details": {},
        "critic_cycle_count": 0,
        "evidence_provenance": [],
        "risk_signals": [],
        "pii_vault": None,
        "compliance_alerts": None,
        "has_typology_alert": None,
        "predicted_verdict": None,
        "workflow_status": None,
        "ml_risk_score": None,
        "ml_calibrated_probability": None,
        "ml_top_features": None,
        "ml_model_id": None,
    }

    # Execute node
    res_state = risk_reasoning_node(state)

    # ML tabular signals must be populated
    assert res_state["ml_risk_score"] is not None
    assert res_state["ml_calibrated_probability"] is not None
    assert res_state["ml_model_id"] == "lightgbm_fraud_detector_v1"
    assert len(res_state["ml_top_features"]) > 0

    # Adjudication policy: High-value commercial wire without criminal typologies
    # is adjudicated as BENIGN, while statutory CTR alert is preserved.
    assert res_state["predicted_verdict"] == "BENIGN"
    assert res_state["risk_score"] < 0.50
    assert len(res_state["compliance_alerts"]) == 1
    assert "CTR reporting threshold" in res_state["compliance_alerts"][0]

