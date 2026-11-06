"""
Guards for the held-out scenario battery used to evaluate the fraud model.

1. The held-out cases (``TEST_*``) are never part of the default training dataset.
2. ``assert_disjoint_case_ids`` rejects any overlap between training and evaluation ids.
3. Scenario feature rows contain no single feature that perfectly separates the labels,
   i.e. the label-derived KYC / risk-tier / balance / graph values cannot come back.
"""

import pytest

from backend.ml.dataset import (
    assert_disjoint_case_ids,
    load_amlsim_held_out_dataset,
    load_amlsim_tabular_dataset,
)
from backend.ml.features import FEATURE_NAMES


def test_held_out_cases_excluded_from_training_dataset():
    train_pool = load_amlsim_tabular_dataset(n_synthetic=50, seed=7)
    held_out = load_amlsim_held_out_dataset()

    assert held_out.num_samples > 0
    assert all(cid.startswith("TEST_") for cid in held_out.case_ids)
    assert not any(cid.startswith("TEST_") for cid in train_pool.case_ids)
    assert_disjoint_case_ids(train_pool.case_ids, held_out.case_ids)


def test_include_held_out_flag_is_explicit_opt_in():
    with_held = load_amlsim_tabular_dataset(n_synthetic=0, include_held_out=True)
    without = load_amlsim_tabular_dataset(n_synthetic=0)
    held_out = load_amlsim_held_out_dataset()
    assert with_held.num_samples == without.num_samples + held_out.num_samples


def test_assert_disjoint_case_ids_detects_leak():
    assert_disjoint_case_ids(["SYN_1", "AML_2"], ["TEST_1"])
    with pytest.raises(ValueError, match="leaked into training"):
        assert_disjoint_case_ids(["SYN_1", "TEST_1"], ["TEST_1", "TEST_2"])


def test_scenario_features_do_not_encode_the_label():
    held_out = load_amlsim_held_out_dataset()
    neg, pos = held_out.X[held_out.y == 0], held_out.X[held_out.y == 1]
    assert len(neg) and len(pos)

    separating = [
        name
        for j, name in enumerate(FEATURE_NAMES)
        if neg[:, j].max() < pos[:, j].min() or pos[:, j].max() < neg[:, j].min()
    ]
    assert not separating, f"Features perfectly separate held-out labels (label leakage): {separating}"
