import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import models
import database

DEFAULT_PROMPTS: Dict[str, Dict[str, Any]] = {
    "planner": {
        "version": "v1.0",
        "description": "Decomposes transaction investigation into concurrent evidence retrieval sub-tasks.",
        "variables": "transaction_summary",
        "template": """You are a financial fraud investigation planner. Given the transaction summary below,
output a JSON list of evidence-gathering tasks required to investigate it. Only select tasks
from the approved task catalog: [customer_history, transaction_detail, merchant_reputation,
device_fingerprint, location_check].
Transaction: {transaction_summary}"""
    },
    "reasoner": {
        "version": "v1.0",
        "description": "Synthesizes multidimensional evidence bundle into structured risk scoring and reasoning.",
        "variables": "evidence_bundle",
        "template": """You are a fraud investigation reasoning engine. Using ONLY the evidence provided below,
explain whether this transaction is likely fraudulent. Every claim must reference a specific
evidence field by name. If evidence is insufficient to support a conclusion, state this explicitly.
Output JSON schema: {{"reasoning": "...", "risk_score": 0.85, "confidence": 0.90}}
Evidence: {evidence_bundle}"""
    },
    "critic": {
        "version": "v1.0",
        "description": "Adversarially critiques draft explanation against ground truth evidence and velocity metrics.",
        "variables": "draft_explanation,evidence_bundle,velocity_analysis",
        "template": """You are an evidence critic. Evaluate the draft explanation below against the evidence bundle and velocity analysis.
Verify whether claims are logically consistent and evidence-backed.
Output JSON schema:
{{
  "critic_issues": true/false,
  "critique": "Detailed critique message",
  "affected_claims": ["claim 1"],
  "evidence_references": ["customer_evidence.name"],
  "severity": "LOW" | "MEDIUM" | "HIGH"
}}
Draft: {draft_explanation}
Evidence: {evidence_bundle}
Velocity Analysis: {velocity_analysis}"""
    },
    "validator": {
        "version": "v1.0",
        "description": "Validates sentence-by-sentence evidential grounding to prevent LLM hallucinations.",
        "variables": "draft_explanation,evidence_bundle",
        "template": """Review the draft explanation below against the evidence bundle. Flag any sentence that
is not directly supported by a named evidence field. Output a list of unsupported claims, or an
empty list if all claims are grounded.
Draft: {draft_explanation}
Evidence: {evidence_bundle}"""
    },
    "reporter": {
        "version": "v1.0",
        "description": "Formats validated investigation into compliance-ready executive and SAR narrative.",
        "variables": "report_context",
        "template": """Format the validated explanation as a structured investigation report with sections:
Summary, Evidence Table, Risk Factors, Confidence Score, and Recommendation. Use only the
validated, grounded content provided."""
    }
}

# In-memory prompt cache: key = f"{tenant_id}:{name}", value = (template_text, version)
_PROMPT_CACHE: Dict[str, Dict[str, Any]] = {}

def seed_default_prompts(db: Session, tenant_id: str = "default_tenant") -> int:
    """Seed initial prompt registry entries if none exist for this tenant."""
    created = 0
    for name, data in DEFAULT_PROMPTS.items():
        existing = db.query(models.PromptRecord).filter(
            models.PromptRecord.tenant_id == tenant_id,
            models.PromptRecord.name == name
        ).first()

        if not existing:
            prompt = models.PromptRecord(
                tenant_id=tenant_id,
                name=name,
                version=data["version"],
                template_text=data["template"].strip(),
                description=data["description"],
                variables=data["variables"],
                is_active=True,
                created_by="System Default"
            )
            db.add(prompt)
            created += 1

    if created > 0:
        db.commit()
    return created

def get_prompt_template(name: str, tenant_id: str = "default_tenant", db: Optional[Session] = None) -> str:
    """Retrieve active prompt template dynamically from database with fallback to default constant."""
    cache_key = f"{tenant_id}:{name}"
    if cache_key in _PROMPT_CACHE:
        return _PROMPT_CACHE[cache_key]["template"]

    should_close = False
    if db is None:
        try:
            db = database.SessionLocal()
            should_close = True
        except Exception:
            db = None

    template_text = None
    version = "v1.0"

    if db is not None:
        try:
            record = db.query(models.PromptRecord).filter(
                models.PromptRecord.tenant_id == tenant_id,
                models.PromptRecord.name == name,
                models.PromptRecord.is_active == True
            ).first()

            if record:
                template_text = record.template_text
                version = record.version
        except Exception as e:
            print(f"Warning: Prompt registry DB lookup failed for '{name}': {e}")
        finally:
            if should_close:
                db.close()

    if not template_text:
        template_text = DEFAULT_PROMPTS.get(name, {}).get("template", "").strip()

    # Cache prompt
    _PROMPT_CACHE[cache_key] = {"template": template_text, "version": version}
    return template_text

def invalidate_prompt_cache(name: Optional[str] = None, tenant_id: Optional[str] = None):
    """Invalidate prompt cache entries when an administrator updates or activates a prompt."""
    global _PROMPT_CACHE
    if name and tenant_id:
        _PROMPT_CACHE.pop(f"{tenant_id}:{name}", None)
    elif tenant_id:
        _PROMPT_CACHE = {k: v for k, v in _PROMPT_CACHE.items() if not k.startswith(f"{tenant_id}:")}
    else:
        _PROMPT_CACHE.clear()
