"""
FFIRE Machine Learning Subsystem (Phase 2).

Provides:
- Tabular feature extraction with strict zero-label-leakage guarantees
- Imbalanced dataset synthesis and cross-validation splitting
- Gradient boosted decision trees (LightGBM) & baseline logistic classifiers
- Probability calibration (Platt scaling & Isotonic regression)
- Rigorous evaluation metrics (PR-AUC, ROC-AUC, FPR, FNR, Brier score, ECE)
- Model registry for staging, metadata tracking, and artifact persistence
- Offline inference service integrated into LangGraph
"""

__version__ = "1.0.0"
