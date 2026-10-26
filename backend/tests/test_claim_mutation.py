"""
FFIRE Deterministic Claim-Mutation Verifier Suite (Task T2.2 / Finding V6).

Validates grounding guardrail behavior under metamorphic attribute mutations:
- Amount and numerical mutations (scaling, 1-cent tampering, arbitrary amounts)
- Merchant and category mutations (fabricated vendors, high-risk categories)
- Location and jurisdiction mutations (offshore, conflicting countries, missing evidence)
- Customer identity mutations (identity tampering, adversary claims)
- Device and OS mutations (conflicting OS, fabricated new-device flags)
- Velocity burst mutations (false velocity spikes, smurfing claims)
- Adversarial hallucinations and ungrounded factual assertions
- Metamorphic monotonicity and reversibility verification
"""

import pytest
from guardrails import extract_and_verify_claims, validate_claims


@pytest.fixture
def baseline_evidence_bundle():
    """Ground-truth canonical evidence bundle representing a verified benign transaction."""
    return {
        "customer": {
            "name": "Eleanor Vance",
            "customer_id": "cust_el_001",
            "kyc_status": "VERIFIED",
            "risk_level": "LOW"
        },
        "account": {
            "account_id": "acc_el_99214",
            "status": "ACTIVE",
            "balance": 15420.00
        },
        "transaction": {
            "txn_id": "txn_base_1001",
            "account_id": "acc_el_99214",
            "counterparty": "acc_dest_store_99",
            "amount": 425.50,
            "currency": "USD",
            "channel": "MOBILE",
            "status": "COMPLETED",
            "timestamp": "2026-01-15T10:30:00Z"
        },
        "merchant": {
            "merchant_id": "merch_bb_55",
            "name": "Best Buy Retail",
            "category": "ELECTRONICS",
            "historical_fraud_rate": 0.008
        },
        "device": {
            "device_id": "dev_ios_9981",
            "os": "iOS",
            "fingerprint": "fp_apple_secure_01",
            "new_device": False,
            "ip_address": "192.168.1.10"
        },
        "location": {
            "country": "US",
            "city": "New York",
            "geo_coord": "40.7128,-74.0060"
        },
        "velocity_evidence": {
            "high_velocity_flag": False,
            "velocity_1h_count": 1,
            "velocity_24h_count": 3
        }
    }


def test_amount_mutation_rejection(baseline_evidence_bundle):
    """Verify that tampering with transaction amounts is deterministically rejected."""
    # 1. Mutate amount by 1 cent ($425.50 -> $425.51)
    mutated_explanation_1cent = (
        "The transaction for customer Eleanor Vance was processed for an amount of $425.51 USD."
    )
    claims_1cent = extract_and_verify_claims(mutated_explanation_1cent, baseline_evidence_bundle)
    assert len(claims_1cent) > 0
    amt_claim_1c = next((c for c in claims_1cent if not c["supported"]), claims_1cent[0])
    assert amt_claim_1c["supported"] is False
    assert amt_claim_1c["confidence"] <= 0.25
    assert "425.51" in amt_claim_1c["verification_reason"]

    # 2. Mutate amount by 10x ($425.50 -> $4255.00)
    mutated_explanation_10x = (
        "The customer completed a transaction with an amount of $4255.00 USD at Best Buy Retail."
    )
    claims_10x = extract_and_verify_claims(mutated_explanation_10x, baseline_evidence_bundle)
    amt_claim_10x = next((c for c in claims_10x if not c["supported"]), claims_10x[0])
    assert amt_claim_10x["supported"] is False
    assert amt_claim_10x["confidence"] <= 0.25
    assert "4255.00" in amt_claim_10x["verification_reason"] or "4255" in amt_claim_10x["verification_reason"]

    # 3. Mutate amount to unrelated large value
    mutated_explanation_large = (
        "The transaction amount was $98500.00 USD initiated from the mobile channel."
    )
    claims_large = extract_and_verify_claims(mutated_explanation_large, baseline_evidence_bundle)
    assert claims_large[0]["supported"] is False
    assert claims_large[0]["confidence"] <= 0.25

    # 4. Unmutated exact amount ($425.50) must be supported with high confidence
    valid_explanation = (
        "The transaction of 425.50 USD for customer Eleanor Vance was verified."
    )
    valid_claims = extract_and_verify_claims(valid_explanation, baseline_evidence_bundle)
    assert valid_claims[0]["supported"] is True
    assert valid_claims[0]["confidence"] >= 0.85


def test_merchant_and_category_mutation_rejection(baseline_evidence_bundle):
    """Verify that fabricating high-risk merchant categories or names is rejected."""
    # 1. Mutate category to CRYPTO
    crypto_mutation = (
        "The merchant Best Buy Retail was classified under the high-risk category of crypto."
    )
    claims_crypto = extract_and_verify_claims(crypto_mutation, baseline_evidence_bundle)
    assert claims_crypto[0]["supported"] is False
    assert claims_crypto[0]["confidence"] <= 0.25

    # 2. Mutate category to GAMBLING
    gambling_mutation = (
        "The transaction at the merchant was processed as an online gambling charge."
    )
    claims_gambling = extract_and_verify_claims(gambling_mutation, baseline_evidence_bundle)
    assert claims_gambling[0]["supported"] is False
    assert claims_gambling[0]["confidence"] <= 0.25

    # 3. Mutate vendor to high-risk electronics darknet vendor
    darknet_mutation = (
        "The transaction occurred at merchant HighRisk Electronics on a darknet market."
    )
    claims_darknet = extract_and_verify_claims(darknet_mutation, baseline_evidence_bundle)
    assert claims_darknet[0]["supported"] is False
    assert claims_darknet[0]["confidence"] <= 0.25

    # 4. Grounded merchant statement must be supported
    grounded_merchant = (
        "The merchant Best Buy Retail operates under electronics retail."
    )
    claims_valid = extract_and_verify_claims(grounded_merchant, baseline_evidence_bundle)
    assert claims_valid[0]["supported"] is True
    assert claims_valid[0]["confidence"] >= 0.85


def test_location_and_jurisdiction_mutation_rejection(baseline_evidence_bundle):
    """Verify that foreign or offshore location mutations are rejected."""
    # 1. Asserting offshore / Zurich jurisdiction
    offshore_mutation = (
        "The customer performed the transaction from an offshore location in Zurich."
    )
    claims_offshore = extract_and_verify_claims(offshore_mutation, baseline_evidence_bundle)
    assert claims_offshore[0]["supported"] is False
    assert claims_offshore[0]["confidence"] <= 0.25

    # 2. Asserting sanctioned country (Russia / North Korea / Iran)
    sanction_mutation = (
        "The IP address and location indicate the transaction originated in Russia."
    )
    claims_sanction = extract_and_verify_claims(sanction_mutation, baseline_evidence_bundle)
    assert claims_sanction[0]["supported"] is False
    assert claims_sanction[0]["confidence"] <= 0.25

    # 3. Missing location evidence in bundle
    bundle_no_loc = dict(baseline_evidence_bundle)
    bundle_no_loc.pop("location")
    claims_no_loc = extract_and_verify_claims("The transaction location is verified in the US.", bundle_no_loc)
    assert claims_no_loc[0]["supported"] is False
    assert claims_no_loc[0]["confidence"] <= 0.25
    assert "no location evidence" in claims_no_loc[0]["verification_reason"]

    # 4. Unmutated US / New York location must be supported
    grounded_loc = (
        "The transaction location was confirmed in New York, US."
    )
    claims_grounded = extract_and_verify_claims(grounded_loc, baseline_evidence_bundle)
    assert claims_grounded[0]["supported"] is True
    assert claims_grounded[0]["confidence"] >= 0.85


def test_customer_identity_mutation_rejection(baseline_evidence_bundle):
    """Verify that replacing the customer identity is deterministically flagged."""
    # 1. Conflicting customer Bob Jones
    mutated_identity_bob = (
        "The customer Bob Jones initiated this transfer from his primary account."
    )
    claims_bob = extract_and_verify_claims(mutated_identity_bob, baseline_evidence_bundle)
    assert claims_bob[0]["supported"] is False
    assert claims_bob[0]["confidence"] <= 0.25
    assert "conflicts with evidence" in claims_bob[0]["verification_reason"]

    # 2. Fabricated attacker identity
    mutated_identity_hacker = (
        "The customer account was taken over by an external attacker."
    )
    claims_hacker = extract_and_verify_claims(mutated_identity_hacker, baseline_evidence_bundle)
    assert claims_hacker[0]["supported"] is False
    assert claims_hacker[0]["confidence"] <= 0.25

    # 3. Grounded customer identity
    grounded_identity = (
        "Customer Eleanor Vance holds an active verified account."
    )
    claims_grounded = extract_and_verify_claims(grounded_identity, baseline_evidence_bundle)
    assert claims_grounded[0]["supported"] is True
    assert claims_grounded[0]["confidence"] >= 0.85


def test_device_and_os_mutation_rejection(baseline_evidence_bundle):
    """Verify that OS conflicts and fabricated new-device claims are rejected."""
    # 1. Conflicting OS: claiming Android when evidence is iOS
    android_mutation = (
        "The device used for this transaction was running Android mobile OS."
    )
    claims_android = extract_and_verify_claims(android_mutation, baseline_evidence_bundle)
    assert claims_android[0]["supported"] is False
    assert claims_android[0]["confidence"] <= 0.25

    # 2. Claiming "unknown OS" when known iOS is present
    unknown_os_mutation = (
        "The user connected via an unrecognized unknown OS device."
    )
    claims_unknown = extract_and_verify_claims(unknown_os_mutation, baseline_evidence_bundle)
    assert claims_unknown[0]["supported"] is False
    assert claims_unknown[0]["confidence"] <= 0.25

    # 3. Claiming new device when evidence indicates existing device (new_device=False)
    new_dev_mutation = (
        "The investigation flagged a suspicious new device that was never seen before."
    )
    claims_new_dev = extract_and_verify_claims(new_dev_mutation, baseline_evidence_bundle)
    assert claims_new_dev[0]["supported"] is False
    assert claims_new_dev[0]["confidence"] <= 0.25

    # 4. Missing device evidence completely
    bundle_no_dev = dict(baseline_evidence_bundle)
    bundle_no_dev.pop("device")
    claims_no_dev = extract_and_verify_claims("The device fingerprint was verified.", bundle_no_dev)
    assert claims_no_dev[0]["supported"] is False
    assert claims_no_dev[0]["confidence"] <= 0.25

    # 5. Grounded iOS device statement
    grounded_dev = (
        "The transaction was submitted through a known iOS mobile device."
    )
    claims_valid = extract_and_verify_claims(grounded_dev, baseline_evidence_bundle)
    assert claims_valid[0]["supported"] is True
    assert claims_valid[0]["confidence"] >= 0.85


def test_velocity_and_temporal_mutation_rejection(baseline_evidence_bundle):
    """Verify that fabricating velocity spikes or smurfing is rejected."""
    # 1. Claiming velocity spike when high_velocity_flag is False
    velocity_mutation = (
        "A rapid burst of transactions triggered a high velocity alert on the account."
    )
    claims_vel = extract_and_verify_claims(velocity_mutation, baseline_evidence_bundle)
    assert claims_vel[0]["supported"] is False
    assert claims_vel[0]["confidence"] <= 0.25

    # 2. Claiming smurfing / structuring without evidence
    smurfing_mutation = (
        "The account exhibits high velocity smurfing and structuring behavior."
    )
    claims_smurf = extract_and_verify_claims(smurfing_mutation, baseline_evidence_bundle)
    assert claims_smurf[0]["supported"] is False
    assert claims_smurf[0]["confidence"] <= 0.25

    # 3. Grounded velocity with high_velocity_flag=True
    bundle_high_vel = dict(baseline_evidence_bundle)
    bundle_high_vel["velocity_evidence"] = {
        "high_velocity_flag": True,
        "velocity_1h_count": 12,
        "velocity_24h_count": 28
    }
    claims_true_vel = extract_and_verify_claims(
        "A rapid burst of transactions triggered high velocity.",
        bundle_high_vel
    )
    assert claims_true_vel[0]["supported"] is True
    assert claims_true_vel[0]["confidence"] >= 0.85


def test_adversarial_hallucination_and_fabrication_rejection(baseline_evidence_bundle):
    """Verify that ungrounded external fraud typologies are rejected."""
    # 1. Explicit hallucinated fact token
    hallucination_text = "The user transferred funds. [hallucinated_fact: offshore shell entity]"
    claims_hal = extract_and_verify_claims(hallucination_text, baseline_evidence_bundle)
    unsupported = [c for c in claims_hal if not c["supported"]]
    assert len(unsupported) > 0
    assert any(c["confidence"] <= 0.15 for c in unsupported)

    # 2. Ungrounded wire transfer and compromised password assertions
    fabricated_story = (
        "The customer transferred $75,000 via unauthorized wire following a compromised credential dump."
    )
    claims_fab = extract_and_verify_claims(fabricated_story, baseline_evidence_bundle)
    assert claims_fab[0]["supported"] is False
    assert claims_fab[0]["confidence"] <= 0.25

    # 3. Disconnected statement with zero evidence matches
    disconnected_text = "The satellite telemetry indicates atmospheric interference."
    claims_disc = extract_and_verify_claims(disconnected_text, baseline_evidence_bundle)
    assert claims_disc[0]["supported"] is False
    assert claims_disc[0]["confidence"] <= 0.30


def test_metamorphic_mutation_monotonicity(baseline_evidence_bundle):
    """
    Metamorphic Property Test:
    Mutating any single grounded attribute to an ungrounded value must strictly decrease
    claim confidence and set supported=False. Reverting the attribute must restore supported=True.
    """
    grounded_template = (
        "Customer {customer} processed transaction {txn} for {amount} USD at {merchant} on {os}."
    )
    canonical_text = grounded_template.format(
        customer="Eleanor Vance",
        txn="txn_base_1001",
        amount="425.50",
        merchant="Best Buy Retail",
        os="iOS"
    )

    # Baseline verification
    baseline_claims = extract_and_verify_claims(canonical_text, baseline_evidence_bundle)
    assert len(baseline_claims) == 1
    assert baseline_claims[0]["supported"] is True
    baseline_conf = baseline_claims[0]["confidence"]
    assert baseline_conf >= 0.85

    # Metamorphic mutations
    mutations = [
        ("customer", "Bob Jones"),
        ("amount", "9999.00"),
        ("merchant", "Apex Crypto"),
        ("os", "Android"),
    ]

    for key, mutated_val in mutations:
        params = {
            "customer": "Eleanor Vance",
            "txn": "txn_base_1001",
            "amount": "425.50",
            "merchant": "Best Buy Retail",
            "os": "iOS"
        }
        params[key] = mutated_val
        mutated_text = grounded_template.format(**params)

        mutated_claims = extract_and_verify_claims(mutated_text, baseline_evidence_bundle)
        assert len(mutated_claims) == 1
        m_claim = mutated_claims[0]

        # Monotonicity check: confidence must drop strictly below baseline
        assert m_claim["confidence"] < baseline_conf, f"Mutation of {key} did not decrease confidence"
        assert m_claim["supported"] is False, f"Mutation of {key} was unexpectedly supported"
        assert m_claim["confidence"] <= 0.25

        # Reversibility check: replacing back restores validity
        params[key] = {
            "customer": "Eleanor Vance",
            "amount": "425.50",
            "merchant": "Best Buy Retail",
            "os": "iOS"
        }[key]
        reverted_text = grounded_template.format(**params)
        reverted_claims = extract_and_verify_claims(reverted_text, baseline_evidence_bundle)
        assert reverted_claims[0]["supported"] is True
        assert reverted_claims[0]["confidence"] >= baseline_conf


def test_boundary_conditions_and_multi_sentence_isolation(baseline_evidence_bundle):
    """Verify empty input handling, None values in evidence, and sentence-level isolation."""
    # 1. Empty draft explanation
    assert extract_and_verify_claims("", baseline_evidence_bundle) == []
    assert validate_claims("", baseline_evidence_bundle) == (True, [])

    # 2. Bundle with None / null fields
    corrupt_bundle = {
        "customer": {"name": None, "kyc_status": None},
        "transaction": {"amount": None},
        "device": None,
        "location": {"country": None}
    }
    safe_claims = extract_and_verify_claims("The investigation status was reviewed.", corrupt_bundle)
    assert isinstance(safe_claims, list)

    # 3. Multi-sentence explanation with 1 valid sentence and 1 mutated sentence
    multi_sentence = (
        "The transaction of 425.50 USD for customer Eleanor Vance was verified. "
        "The user transferred $85,000 to an offshore account in Zurich via unauthorized wire."
    )
    results = extract_and_verify_claims(multi_sentence, baseline_evidence_bundle)
    assert len(results) == 2

    # Sentence 1: Valid & Grounded
    assert results[0]["supported"] is True
    assert results[0]["confidence"] >= 0.85

    # Sentence 2: Mutated & Ungrounded
    assert results[1]["supported"] is False
    assert results[1]["confidence"] <= 0.25

    # Overall validate_claims returns False with only the invalid sentence flagged
    is_valid, unsupported = validate_claims(multi_sentence, baseline_evidence_bundle)
    assert is_valid is False
    assert len(unsupported) == 1
    assert "Zurich" in unsupported[0] or "$85,000" in unsupported[0]


def test_typed_currency_mismatch_rejection(baseline_evidence_bundle):
    """Verify that asserting EUR, GBP, or JPY against a USD transaction is rejected."""
    eur_statement = "The transaction of 425.50 EUR for customer Eleanor Vance was verified."
    claims_eur = extract_and_verify_claims(eur_statement, baseline_evidence_bundle)
    assert len(claims_eur) > 0
    assert claims_eur[0]["supported"] is False
    assert "currency mismatch" in claims_eur[0]["verification_reason"].lower()

    gbp_statement = "The payment of £425.50 was charged to Eleanor Vance."
    claims_gbp = extract_and_verify_claims(gbp_statement, baseline_evidence_bundle)
    assert claims_gbp[0]["supported"] is False
    assert "currency mismatch" in claims_gbp[0]["verification_reason"].lower()


def test_directional_account_contradiction_rejection(baseline_evidence_bundle):
    """Verify that reversing originator and counterparty direction is caught as a contradiction."""
    # True flow is acc_el_99214 -> acc_dest_store_99
    # Assert reversed flow: acc_dest_store_99 transferred to acc_el_99214
    reversed_statement = (
        "Transfer from acc_dest_store_99 to acc_el_99214 for 425.50 USD was executed."
    )
    claims_rev = extract_and_verify_claims(reversed_statement, baseline_evidence_bundle)
    assert len(claims_rev) > 0
    assert claims_rev[0]["supported"] is False
    assert "directional contradiction" in claims_rev[0]["verification_reason"].lower()


def test_temporal_date_contradiction_rejection(baseline_evidence_bundle):
    """Verify that asserting contradictory dates or calendar months is rejected."""
    # True timestamp is 2026-01-15 (January 2026)
    # 1. Assert conflicting ISO date: 2026-12-25
    conflicting_date = (
        "The customer completed a transaction on 2026-12-25 of 425.50 USD."
    )
    claims_date = extract_and_verify_claims(conflicting_date, baseline_evidence_bundle)
    assert len(claims_date) > 0
    assert claims_date[0]["supported"] is False
    assert "temporal contradiction" in claims_date[0]["verification_reason"].lower()

    # 2. Assert conflicting month name: December 2026
    conflicting_month = (
        "In December 2026 the customer completed a transaction of 425.50 USD."
    )
    claims_month = extract_and_verify_claims(conflicting_month, baseline_evidence_bundle)
    assert claims_month[0]["supported"] is False
    assert "temporal contradiction" in claims_month[0]["verification_reason"].lower()


def test_status_contradiction_rejection(baseline_evidence_bundle):
    """Verify that asserting transaction reversal or failure against COMPLETED status is rejected."""
    # True status is COMPLETED
    failed_statement = (
        "The transaction for 425.50 USD had chargeback processed and funds reversed."
    )
    claims_fail = extract_and_verify_claims(failed_statement, baseline_evidence_bundle)
    assert len(claims_fail) > 0
    assert claims_fail[0]["supported"] is False
    assert "status assertion" in claims_fail[0]["verification_reason"].lower()

