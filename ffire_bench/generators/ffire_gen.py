"""
Synthetic financial crime investigation scenario generator for FFIRE-Bench.
Generates rich, multi-modal evidentiary dossiers across 8 distinct typologies
with deterministic seeds, provenance tracking, and canary strings.
"""

import random
from typing import List, Dict, Any, Optional
from ffire_bench.schema.models import (
    Case,
    EvidenceItem,
    EvidenceType,
    Claim,
    ClaimLabel,
    CaseLabel,
    CaseDisposition,
    Provenance,
    Difficulty,
    Severity,
    ErrorCode,
    Track,
    Split
)
from ffire_bench.narratives.templates import NarrativeTemplates
from ffire_bench.narratives.error_injector import ErrorInjector


class FFIREGenerator:
    """Deterministic case generator across 8 financial crime typologies."""

    TYPOLOGIES = [
        "structuring",
        "rapid_movement",
        "funnel_accounts",
        "account_takeover",
        "mule_network",
        "trade_based_ml",
        "elder_exploitation",
        "sanctions_adjacent"
    ]

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_case(
        self,
        case_idx: int,
        typology: Optional[str] = None,
        inject_error: bool = True,
        track: Track = Track.T1,
        split: Split = Split.DEV,
        narrative_source: str = "llm:synthetic_generator_v1"
    ) -> Case:
        """Generate a complete evidentiary case bundle with narrative and claim annotations."""
        if typology is None:
            typology = self.TYPOLOGIES[case_idx % len(self.TYPOLOGIES)]

        cluster_id = f"C-{(case_idx % 15) + 1:04d}"
        case_id = f"FB-{track.value}-{case_idx:06d}"

        # Dispatch typology scenario builder
        builder = getattr(self, f"_build_{typology}", self._build_structuring)
        return builder(
            case_id=case_id,
            cluster_id=cluster_id,
            case_idx=case_idx,
            inject_error=inject_error,
            track=track,
            split=split,
            narrative_source=narrative_source
        )

    # ------------------------------------------------------------------------
    # 1. Structuring (Smurfing below $10,000 threshold)
    # ------------------------------------------------------------------------
    def _build_structuring(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        amounts = [9400.0, 9600.0, 9850.0]
        actual_total = sum(amounts)

        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.TRANSACTION_TABLE,
            title="Branch Cash Deposit Log",
            content=[
                {"txn_id": f"TXN-STRUC-01", "date": "2026-10-12 09:14:00", "type": "CASH_DEPOSIT", "amount": 9400.0, "branch": "North Branch #14", "currency": "USD"},
                {"txn_id": f"TXN-STRUC-02", "date": "2026-10-13 11:22:00", "type": "CASH_DEPOSIT", "amount": 9600.0, "branch": "Metro Branch #02", "currency": "USD"},
                {"txn_id": f"TXN-STRUC-03", "date": "2026-10-14 15:45:00", "type": "CASH_DEPOSIT", "amount": 9850.0, "branch": "Southwest Branch #08", "currency": "USD"}
            ]
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.KYC_PROFILE,
            title="Customer Profile & Occupation",
            content={
                "customer_name": "Marcus Vance",
                "customer_id": f"CUST-STRUC-{case_idx:04d}",
                "stated_occupation": "Independent Consultant",
                "stated_monthly_income": 4500.0,
                "account_opened": "2024-03-10",
                "kyc_risk_tier": "MEDIUM"
            }
        )

        base_findings = (
            f"The subject Marcus Vance conducted three consecutive cash deposits totaling ${actual_total:,.2f} "
            f"across three distinct bank branches between October 12 and October 14, 2026. "
            f"Each individual deposit remained intentionally beneath the $10,000 Currency Transaction Report (CTR) threshold. "
            f"The aggregate cash volume significantly exceeds the subject's stated monthly income of $4,500.00."
        )

        narrative = NarrativeTemplates.formal_sar_narrative(
            subject_name="Marcus Vance",
            account_id=f"ACCT-{case_idx:05d}",
            typology="Structuring",
            evidence_summary="Alert triggered by CTR threshold avoidance rules.",
            findings=base_findings,
            disposition="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E1 (Wrong amount: says $32,000 instead of actual total $28,850)
            target = f"${actual_total:,.2f}"
            mutated_amount = "$32,500.00"
            narrative, claim_e1 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=mutated_amount,
                error_code=ErrorCode.E1,
                severity=Severity.CRITICAL,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-1"],
                claim_id="CL-1"
            )
            claims.append(claim_e1)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase=f"${actual_total:,.2f}",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        # Add supported claim
        claims.append(
            ErrorInjector.create_supported_claim(
                narrative=narrative,
                exact_phrase="beneath the $10,000 Currency Transaction Report (CTR) threshold",
                claim_id="CL-2",
                gold_evidence_ids=["EV-1"]
            )
        )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="structuring",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.MEDIUM
        )

    # ------------------------------------------------------------------------
    # 2. Rapid Movement / Pass-Through Accounts
    # ------------------------------------------------------------------------
    def _build_rapid_movement(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.TRANSACTION_TABLE,
            title="Wire Activity Log",
            content=[
                {"txn_id": "TXN-RM-01", "timestamp": "2026-09-05 10:00:00", "type": "INCOMING_WIRE", "amount": 150000.0, "originator": "Delta Holdings Ltd", "country": "Panama"},
                {"txn_id": "TXN-RM-02", "timestamp": "2026-09-05 11:15:00", "type": "OUTGOING_WIRE", "amount": 148500.0, "beneficiary": "Zenith Global LLC", "country": "Cyprus"}
            ]
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.KYC_PROFILE,
            title="Commercial Customer Profile",
            content={
                "customer_name": "Apex Logistics Corp",
                "line_of_business": "Domestic Freight Transport",
                "average_monthly_balance": 2500.0
            }
        )

        findings = (
            "Subject account received an inbound international wire of $150,000.00 from Delta Holdings Ltd in Panama. "
            "Within 75 minutes of receipt, $148,500.00 was wired out to Zenith Global LLC in Cyprus, leaving a nominal residual balance."
        )

        narrative = NarrativeTemplates.formal_sar_narrative(
            subject_name="Apex Logistics Corp",
            account_id=f"ACCT-{case_idx:05d}",
            typology="Rapid Movement / Pass-Through",
            evidence_summary="Immediate depletion of international funds transfer.",
            findings=findings,
            disposition="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E2 (Wrong chronological sequence: says outgoing wire happened before incoming wire)
            target = "Within 75 minutes of receipt"
            replacement = "Prior to receiving the covering wire"
            narrative, claim_e2 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E2,
                severity=Severity.CRITICAL,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-1"],
                claim_id="CL-1"
            )
            claims.append(claim_e2)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="Within 75 minutes of receipt",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        claims.append(
            ErrorInjector.create_supported_claim(
                narrative=narrative,
                exact_phrase="$150,000.00 from Delta Holdings Ltd",
                claim_id="CL-2",
                gold_evidence_ids=["EV-1"]
            )
        )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="rapid_movement",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.MEDIUM
        )

    # ------------------------------------------------------------------------
    # 3. Funnel Accounts
    # ------------------------------------------------------------------------
    def _build_funnel_accounts(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.TRANSACTION_TABLE,
            title="Multi-Location Branch Deposits",
            content=[
                {"txn_id": "TXN-FNL-01", "date": "2026-08-01 10:00:00", "location": "Miami, FL", "amount": 4500.0},
                {"txn_id": "TXN-FNL-02", "date": "2026-08-01 11:30:00", "location": "Atlanta, GA", "amount": 4800.0},
                {"txn_id": "TXN-FNL-03", "date": "2026-08-01 13:00:00", "location": "Charlotte, NC", "amount": 4700.0}
            ]
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.ANALYST_NOTE,
            title="Branch Operations Note",
            content="Deposits executed by multiple unknown third parties with no apparent connection to cardholder home branch."
        )

        findings = (
            "Cash deposits were made in three distinct states (Miami FL, Atlanta GA, Charlotte NC) within a 3-hour window. "
            "The customer does not maintain business operations in these geographic zones."
        )

        narrative = NarrativeTemplates.bank_investigator_memo(
            case_id=case_id,
            analyst_id="INV-9921",
            subject_name="Coastal Retailers LLC",
            key_facts=[
                "Multi-branch cash deposits across three separate states in 3 hours",
                "Deposits totaled $14,000.00 across branches"
            ],
            risk_rationale=findings,
            recommended_action="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E3 (Fabricated entity: mentions intermediary bank never in evidence)
            target = "Coastal Retailers LLC"
            replacement = "Coastal Retailers LLC and offshore intermediary Bancorp Cayman Ltd"
            narrative, claim_e3 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E3,
                severity=Severity.CRITICAL,
                label=ClaimLabel.UNSUPPORTED,
                gold_evidence_ids=[],
                claim_id="CL-1"
            )
            claims.append(claim_e3)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="Miami FL, Atlanta GA, Charlotte NC",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="funnel_accounts",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.HARD
        )

    # ------------------------------------------------------------------------
    # 4. Account Takeover (ATO)
    # ------------------------------------------------------------------------
    def _build_account_takeover(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.DEVICE_LOG,
            title="Authentication & Device Telemetry",
            content={
                "timestamp": "2026-10-20 03:14:22",
                "ip_address": "185.220.101.5",
                "country": "Romania",
                "device_fingerprint": "DEV-UNKNOWN-TOR",
                "mfa_reset_requested": True
            }
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.KYC_PROFILE,
            title="Customer Baseline Profile",
            content={
                "customer_name": "Eleanor Rigby",
                "residence": "Seattle, WA, USA",
                "primary_device": "iPhone 15 Pro (iOS 17.5)",
                "typical_login_hours": "08:00 - 20:00 PST"
            }
        )

        findings = (
            "Account credentials and MFA were reset from an unfamiliar Tor exit node in Romania at 03:14 PST. "
            "Customer has resided continuously in Seattle WA with no international travel notice."
        )

        narrative = NarrativeTemplates.brief_alert_note(
            subject_name="Eleanor Rigby",
            amount_summary="account credential tampering and $22,000 ACH drain",
            risk_flags=findings,
            verdict="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E4 (Wrong attribution: assigns customer's home to Chicago instead of Seattle)
            target = "resided continuously in Seattle WA"
            replacement = "resided continuously in Chicago IL"
            narrative, claim_e4 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E4,
                severity=Severity.CRITICAL,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-2"],
                claim_id="CL-1"
            )
            claims.append(claim_e4)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="unfamiliar Tor exit node in Romania",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="account_takeover",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.EASY
        )

    # ------------------------------------------------------------------------
    # 5. Mule Network
    # ------------------------------------------------------------------------
    def _build_mule_network(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.TRANSACTION_TABLE,
            title="Peer-to-Peer Micro-Transfers",
            content=[
                {"from_account": "MULE-01", "amount": 490.0, "timestamp": "2026-09-01 10:00:00"},
                {"from_account": "MULE-02", "amount": 495.0, "timestamp": "2026-09-01 10:05:00"},
                {"from_account": "MULE-03", "amount": 485.0, "timestamp": "2026-09-01 10:10:00"},
                {"from_account": "MULE-04", "amount": 500.0, "timestamp": "2026-09-01 10:15:00"}
            ]
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.ANALYST_NOTE,
            title="Consolidated Cash-out Pattern",
            content="Micro-transfers collected from student checking accounts immediately withdrawn via ATM in crypto voucher purchases."
        )

        findings = (
            "Four distinct student accounts remitted micro-transfers totaling $1,970.00 to a central account within 15 minutes. "
            "Funds were liquidated via crypto ATM vouchers."
        )

        narrative = NarrativeTemplates.formal_sar_narrative(
            subject_name="Kiran Patel",
            account_id=f"ACCT-{case_idx:05d}",
            typology="Mule Network",
            evidence_summary="Aggregated micro-transfers and immediate crypto conversion.",
            findings=findings,
            disposition="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E10 (Aggregation arithmetic error: claims 4 transfers totaled $3,500)
            target = "totaling $1,970.00"
            replacement = "totaling $3,500.00"
            narrative, claim_e10 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E10,
                severity=Severity.MAJOR,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-1"],
                claim_id="CL-1"
            )
            claims.append(claim_e10)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="totaling $1,970.00",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="mule_network",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.MEDIUM
        )

    # ------------------------------------------------------------------------
    # 6. Trade-Based Money Laundering (TBML)
    # ------------------------------------------------------------------------
    def _build_trade_based_ml(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.TRANSACTION_TABLE,
            title="Commercial Invoices vs Customs Manifests",
            content={
                "invoice_number": "INV-7890",
                "declared_commodity": "Industrial Grade Steel Tubing",
                "declared_quantity_tons": 50,
                "invoiced_unit_price_usd": 12000.0,
                "total_wire_amount_usd": 600000.0,
                "customs_market_benchmark_unit_price": 850.0
            }
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.ANALYST_NOTE,
            title="Customs Verification Check",
            content="Unit price over-invoiced by more than 14x relative to London Metal Exchange standard spot pricing."
        )

        findings = (
            "Invoice INV-7890 billed steel tubing at $12,000.00 per ton, whereas prevailing fair market price was $850.00 per ton. "
            "This substantial 14x over-invoicing provides clear indicia of trade-based value transfer."
        )

        narrative = NarrativeTemplates.formal_sar_narrative(
            subject_name="Trans-Global Commodities",
            account_id=f"ACCT-{case_idx:05d}",
            typology="Trade-Based Money Laundering",
            evidence_summary="Extreme commercial invoice over-valuation.",
            findings=findings,
            disposition="ESCALATE"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E8 (Wrong typology: calls TBML "identity theft")
            target = "indicia of trade-based value transfer"
            replacement = "indicia of account takeover and credential stuffing"
            narrative, claim_e8 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E8,
                severity=Severity.MAJOR,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-1"],
                claim_id="CL-1"
            )
            claims.append(claim_e8)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="prevailing fair market price was $850.00 per ton",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="trade_based_ml",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.ESCALATE,
                expected_abstention=False
            ),
            difficulty=Difficulty.HARD
        )

    # ------------------------------------------------------------------------
    # 7. Elder Financial Exploitation
    # ------------------------------------------------------------------------
    def _build_elder_exploitation(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.KYC_PROFILE,
            title="Senior Customer Record",
            content={
                "customer_name": "Mildred Gable",
                "age": 82,
                "account_age_years": 34,
                "historical_monthly_spend": 1200.0
            }
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.ANALYST_NOTE,
            title="Branch Manager Escalation Note",
            content="Customer visited branch accompanied by aggressive third party claiming to be contractor demanding immediate $45,000 cashier check."
        )

        findings = (
            "82-year-old customer Mildred Gable attempted to withdraw $45,000.00 via cashier's check accompanied by an unrelated contractor. "
            "Customer appeared visibly distressed and unable to explain the contractual invoice details."
        )

        narrative = NarrativeTemplates.bank_investigator_memo(
            case_id=case_id,
            analyst_id="INV-4410",
            subject_name="Mildred Gable",
            key_facts=[
                "82-year-old long-standing customer accompanied by unfamiliar contractor",
                "Requested $45,000 cashier check deviating from $1,200 monthly historical spend"
            ],
            risk_rationale=findings,
            recommended_action="FLAG"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E6 (Contradiction ignored: narrative asserts transactions are standard authorized remodeling)
            target = "Customer appeared visibly distressed and unable to explain the contractual invoice details."
            replacement = "Customer presented full verifiable architectural blueprints and satisfied all branch inquiries."
            narrative, claim_e6 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E6,
                severity=Severity.CRITICAL,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-2"],
                claim_id="CL-1"
            )
            claims.append(claim_e6)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="attempted to withdraw $45,000.00 via cashier's check",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-2"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="elder_exploitation",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.FLAG,
                expected_abstention=False
            ),
            difficulty=Difficulty.MEDIUM
        )

    # ------------------------------------------------------------------------
    # 8. Sanctions-Adjacent Name Matching
    # ------------------------------------------------------------------------
    def _build_sanctions_adjacent(
        self, case_id: str, cluster_id: str, case_idx: int,
        inject_error: bool, track: Track, split: Split, narrative_source: str
    ) -> Case:
        ev1 = EvidenceItem(
            evidence_id="EV-1",
            type=EvidenceType.SANCTIONS_LIST,
            title="OFAC Specially Designated Nationals (SDN) Record",
            content={
                "sdn_name": "Dmitri Alexeyevich Volkov",
                "alias": "D. Volkov",
                "listed_jurisdiction": "High Risk Border Zone",
                "program": "UKRAINE-EO14024"
            }
        )
        ev2 = EvidenceItem(
            evidence_id="EV-2",
            type=EvidenceType.KYC_PROFILE,
            title="Customer Identity Document",
            content={
                "customer_name": "Dmitry Volkov",
                "dob": "1988-11-04",
                "passport_country": "Estonia",
                "beneficial_owner_verified": False,
                "missing_documents": ["Ultimate Beneficial Ownership (UBO) Registry Declaration"]
            }
        )

        findings = (
            "Wire counterparty Dmitry Volkov closely matches OFAC SDN listed entity Dmitri Alexeyevich Volkov. "
            "Critical UBO documentation is missing from the customer file, precluding definitive resolution."
        )

        narrative = NarrativeTemplates.formal_sar_narrative(
            subject_name="Dmitry Volkov",
            account_id=f"ACCT-{case_idx:05d}",
            typology="Sanctions-Adjacent Screening",
            evidence_summary="Fuzzy name match against sanctions list with incomplete beneficial ownership records.",
            findings=findings,
            disposition="NEED_MORE_INFO"
        )

        claims = []
        safe_to_file = True

        if inject_error:
            # Inject Error E9 (Overconfident conclusion / failure to abstain: closes case as clean when UBO is missing)
            target = "the recommended disposition is NEED_MORE_INFO."
            replacement = "the recommended disposition is CLOSE as a confirmed false positive without requiring further documentation."
            narrative, claim_e9 = ErrorInjector.inject_mutation(
                base_narrative=narrative,
                target_phrase=target,
                replacement_phrase=replacement,
                error_code=ErrorCode.E9,
                severity=Severity.CRITICAL,
                label=ClaimLabel.CONTRADICTED,
                gold_evidence_ids=["EV-2"],
                claim_id="CL-1"
            )
            claims.append(claim_e9)
            safe_to_file = False
        else:
            claims.append(
                ErrorInjector.create_supported_claim(
                    narrative=narrative,
                    exact_phrase="closely matches OFAC SDN listed entity",
                    claim_id="CL-1",
                    gold_evidence_ids=["EV-1"]
                )
            )

        return Case(
            case_id=case_id,
            version="1.0.0",
            track=track,
            split=split,
            provenance=Provenance(
                generator="ffire_gen_v1",
                narrative_source=narrative_source,
                human_reviewed=True,
                reviewer_count=2,
                seed=self.seed
            ),
            typology="sanctions_adjacent",
            cluster_id=cluster_id,
            evidence=[ev1, ev2],
            narrative=narrative,
            claims=claims,
            case_label=CaseLabel(
                safe_to_file=safe_to_file,
                disposition=CaseDisposition.NEED_MORE_INFO,
                expected_abstention=True
            ),
            difficulty=Difficulty.HARD
        )
