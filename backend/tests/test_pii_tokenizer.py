"""
Automated Test Suite for Bi-Directional PII Redaction Tokenizer (Task T1.3).

Validates:
1. Deterministic redaction of customer names, emails, phone numbers, SSNs, credit cards, account IDs, and IPs.
2. Collision-free, multi-entity redaction with longest-match precedence.
3. Perfect bidirectional re-hydration restoring original PII without alteration.
4. Vault export, persistence across DAG state, and restoration.
5. End-to-end LangGraph assertion: Plaintext PII is strictly absent from prompts sent to LLM,
   while final explanation and report are re-hydrated with original entities.
"""

import json
import pytest
from unittest.mock import MagicMock

from security import PIITokenizer
from llm_gateway import MockProvider, get_llm_gateway
import graph


def test_pii_tokenizer_explicit_and_pattern_redaction():
    """Verify explicit registration and automatic regex pattern redaction."""
    tokenizer = PIITokenizer()

    # Explicit entity registrations
    token_name = tokenizer.register_pii("CUSTOMER_NAME", "Alexander Hamilton")
    token_acct = tokenizer.register_pii("ACCOUNT_ID", "acct_treasury_001")
    token_email = tokenizer.register_pii("EMAIL", "ahamilton@treasury.gov")

    assert token_name == "<CUSTOMER_NAME_1>"
    assert token_acct == "<ACCOUNT_ID_1>"
    assert token_email == "<EMAIL_1>"

    # Text containing explicit and pattern-detectable PII (SSN, IP, Phone)
    sample_text = (
        "Customer Alexander Hamilton (email: ahamilton@treasury.gov, SSN: 123-45-6789) "
        "initiated transfer from acct_treasury_001 via IP 192.168.10.45 "
        "and phone (555) 123-4567."
    )

    redacted = tokenizer.redact_text(sample_text)

    # Plaintext PII must be completely absent
    assert "Alexander Hamilton" not in redacted
    assert "ahamilton@treasury.gov" not in redacted
    assert "123-45-6789" not in redacted
    assert "acct_treasury_001" not in redacted
    assert "192.168.10.45" not in redacted
    assert "(555) 123-4567" not in redacted

    # Surrogate tokens must be present
    assert "<CUSTOMER_NAME_1>" in redacted
    assert "<EMAIL_1>" in redacted
    assert "<ACCOUNT_ID_1>" in redacted
    assert "<SSN_1>" in redacted
    assert "<IP_ADDRESS_1>" in redacted
    assert "<PHONE_1>" in redacted

    # Bi-directional re-hydration must restore exact original text
    rehydrated = tokenizer.rehydrate_text(redacted)
    assert rehydrated == sample_text


def test_pii_tokenizer_longest_match_precedence():
    """Verify longer names take precedence over substrings to prevent partial corruption."""
    tokenizer = PIITokenizer()
    tokenizer.register_pii("CUSTOMER_NAME", "John")
    tokenizer.register_pii("CUSTOMER_NAME", "Johnathan Smith")

    text = "Transfers between John and Johnathan Smith occurred today."
    redacted = tokenizer.redact_text(text)

    assert "Johnathan Smith" not in redacted
    assert "John" not in redacted
    assert "<CUSTOMER_NAME_2>" in redacted  # Johnathan Smith
    assert "<CUSTOMER_NAME_1>" in redacted  # John

    rehydrated = tokenizer.rehydrate_text(redacted)
    assert rehydrated == text


def test_pii_tokenizer_vault_export_and_restoration():
    """Verify token vault export and restoration across independent tokenizer instances."""
    tokenizer1 = PIITokenizer()
    tokenizer1.register_pii("CUSTOMER_NAME", "Alice Walker")
    tokenizer1.register_pii("ACCOUNT_ID", "acct_alice_999")

    vault = tokenizer1.export_vault()
    assert "<CUSTOMER_NAME_1>" in vault
    assert vault["<CUSTOMER_NAME_1>"] == "Alice Walker"

    # Restore in second tokenizer
    tokenizer2 = PIITokenizer(existing_vault=vault)
    redacted = "<CUSTOMER_NAME_1> transferred to <ACCOUNT_ID_1>."
    rehydrated = tokenizer2.rehydrate_text(redacted)

    assert rehydrated == "Alice Walker transferred to acct_alice_999."

    # New registration continues sequence without collision
    token_new = tokenizer2.register_pii("CUSTOMER_NAME", "Bob Vance")
    assert token_new == "<CUSTOMER_NAME_2>"


def test_langgraph_redaction_assertion_on_llm_prompts(monkeypatch):
    """
    Assert that prompts delivered to LLM invoke strictly lack plaintext PII,
    and final DAG state output is properly re-hydrated with original entities.
    """
    mock_provider = MockProvider()
    gateway = get_llm_gateway()

    # Custom mock response that references surrogate tokens
    mock_provider.set_default_response(
        json.dumps({
            "reasoning": "Evaluated transaction for <CUSTOMER_NAME_1> from account <ACCOUNT_ID_1>. Risk profile is acceptable.",
            "risk_score": 0.22
        })
    )

    with gateway.override_provider(mock_provider):
        state = {
            "investigation_id": "inv_pii_test_777",
            "transaction_id": "tx_pii_777",
            "tenant_id": "tenant-pii-safe",
            "tasks": [],
            "customer_evidence": {
                "name": "Secret Customer Person",
                "email": "secret.person@privatecorp.ch",
                "customer_id": "cust_super_private_99",
                "status": "OK"
            },
            "transaction_evidence": {
                "account_id": "acct_swiss_numbered_8888",
                "counterparty": "Zurich Private Bank",
                "ip_address": "198.51.100.23",
                "amount": 7500.0,
                "status": "OK"
            },
            "merchant_evidence": {"name": "Merchant Clean", "status": "OK"},
            "device_evidence": {"fingerprint": "fp_secret_device_12345", "status": "OK"},
            "location_evidence": {"country": "CH", "status": "OK"},
            "velocity_evidence": {"high_velocity_flag": False, "status": "OK"},
            "verified_evidence": {},
            "historical_cases": [],
            "risk_score": None,
            "confidence": 0.0,
            "draft_explanation": None,
            "critic_feedback": None,
            "critic_issues": False,
            "retry_count": 0,
            "validated": False,
            "report": None,
            "rule_score": 0.20,
            "rule_reasons": ["Standard transaction size"],
            "pii_vault": None
        }

        # 1. Execute Risk Reasoning Node
        state = graph.risk_reasoning_node(state)

        # Inspect the prompts captured by mock_provider
        assert len(mock_provider.call_history) > 0
        last_call = mock_provider.call_history[-1]
        sent_prompt = last_call["prompt"]

        # ASSERTION 1: Zero plaintext PII reached the model gateway
        assert "Secret Customer Person" not in sent_prompt
        assert "secret.person@privatecorp.ch" not in sent_prompt
        assert "acct_swiss_numbered_8888" not in sent_prompt
        assert "Zurich Private Bank" not in sent_prompt
        assert "198.51.100.23" not in sent_prompt
        assert "fp_secret_device_12345" not in sent_prompt

        # ASSERTION 2: Surrogate tokens were transmitted instead
        assert "<CUSTOMER_NAME_1>" in sent_prompt
        assert "<ACCOUNT_ID_1>" in sent_prompt
        assert "<IP_ADDRESS_1>" in sent_prompt

        # ASSERTION 3: Returned explanation in state was re-hydrated back to original entities
        assert state["draft_explanation"] is not None
        assert "Secret Customer Person" in state["draft_explanation"]
        assert "acct_swiss_numbered_8888" in state["draft_explanation"]
        assert "<CUSTOMER_NAME_1>" not in state["draft_explanation"]
        assert "<ACCOUNT_ID_1>" not in state["draft_explanation"]

        # ASSERTION 4: PII vault is preserved in investigation state
        assert state["pii_vault"] is not None
        assert state["pii_vault"]["<CUSTOMER_NAME_1>"] == "Secret Customer Person"
        assert state["pii_vault"]["<ACCOUNT_ID_1>"] == "acct_swiss_numbered_8888"
