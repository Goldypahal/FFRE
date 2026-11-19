"""
Multi-family narrative generation templates simulating diverse investigator and model drafting styles.
"""

from typing import Dict, Any, List


class NarrativeTemplates:
    @staticmethod
    def formal_sar_narrative(
        subject_name: str,
        account_id: str,
        typology: str,
        evidence_summary: str,
        findings: str,
        disposition: str
    ) -> str:
        """Formal FinCEN-style Suspicious Activity Report (SAR) narrative."""
        return (
            f"SUSPICIOUS ACTIVITY REPORT NARRATIVE\n"
            f"SUBJECT: {subject_name} | ACCOUNT: {account_id}\n"
            f"PRIMARY TYPOLOGY: {typology.upper()}\n\n"
            f"1. BACKGROUND & SUMMARY OF ACTIVITY:\n"
            f"This narrative details suspicious transaction activity identified during periodic review. {evidence_summary}\n\n"
            f"2. INVESTIGATIVE FINDINGS:\n"
            f"{findings}\n\n"
            f"3. DISPOSITION & CONCLUSION:\n"
            f"Based upon evidentiary review, the recommended disposition is {disposition}. "
            f"All supporting documentation remains retained in compliance files."
        )

    @staticmethod
    def bank_investigator_memo(
        case_id: str,
        analyst_id: str,
        subject_name: str,
        key_facts: List[str],
        risk_rationale: str,
        recommended_action: str
    ) -> str:
        """Tier-1 Bank Alert Disposition Memo."""
        facts_bulleted = "\n".join(f"- {f}" for f in key_facts)
        return (
            f"INVESTIGATION MEMORANDUM | CASE ID: {case_id}\n"
            f"INVESTIGATOR ID: {analyst_id} | SUBJECT: {subject_name}\n\n"
            f"EVIDENTIARY FACTS:\n"
            f"{facts_bulleted}\n\n"
            f"RISK ANALYSIS & REASONING:\n"
            f"{risk_rationale}\n\n"
            f"DISPOSITION:\n"
            f"Recommendation: {recommended_action}."
        )

    @staticmethod
    def brief_alert_note(
        subject_name: str,
        amount_summary: str,
        risk_flags: str,
        verdict: str
    ) -> str:
        """Concise alert summary narrative."""
        return (
            f"ALERT SUMMARY for {subject_name}. Activity involves {amount_summary}. "
            f"Risk indicators identified: {risk_flags}. Final evaluation: {verdict}."
        )
