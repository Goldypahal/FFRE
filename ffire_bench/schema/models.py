"""
Pydantic v2 data models for FFIRE-Bench schema specification.
Supports tracks T1–T6, error taxonomy E1–E12, evidentiary bundles, and prediction submissions.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field, ConfigDict


class Track(str, Enum):
    T1 = "T1"  # Claim Verification (headline)
    T2 = "T2"  # Narrative Error Detection
    T3 = "T3"  # Disposition with Abstention
    T4 = "T4"  # Grounded Narrative Generation
    T5 = "T5"  # Typology Detection (sanity)
    T6 = "T6"  # Robustness / Adversarial


class Split(str, Enum):
    DEV = "dev"
    PUBLIC_TEST = "public_test"
    PRIVATE_TEST = "private_test"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Severity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class ClaimLabel(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_CHECKABLE = "NOT_CHECKABLE"


class CaseDisposition(str, Enum):
    ALLOW = "ALLOW"
    CLOSE = "CLOSE"
    FLAG = "FLAG"
    ESCALATE = "ESCALATE"
    NEED_MORE_INFO = "NEED_MORE_INFO"


class ErrorCode(str, Enum):
    E1 = "E1"    # Wrong amount
    E2 = "E2"    # Wrong date / ordering
    E3 = "E3"    # Fabricated transaction or entity
    E4 = "E4"    # Wrong attribution
    E5 = "E5"    # Unsupported inference
    E6 = "E6"    # Contradiction ignored
    E7 = "E7"    # Missing required element
    E8 = "E8"    # Wrong typology
    E9 = "E9"    # Overconfident conclusion / failure to abstain
    E10 = "E10"  # Aggregation error
    E11 = "E11"  # Stale / out-of-window evidence
    E12 = "E12"  # PII / tipping-off leak


class EvidenceType(str, Enum):
    TRANSACTION_TABLE = "transaction_table"
    KYC_PROFILE = "kyc_profile"
    ANALYST_NOTE = "analyst_note"
    DEVICE_LOG = "device_log"
    GEOLOCATION_LOG = "geolocation_log"
    EMAIL_CORRESPONDENCE = "email_correspondence"
    SANCTIONS_LIST = "sanctions_list"


class Provenance(BaseModel):
    model_config = ConfigDict(extra="ignore")
    generator: str = Field(..., description="Generator origin, e.g. amlsim_v2, ffire_gen, expert_authored")
    narrative_source: str = Field(..., description="LLM family or human author, e.g. llm:gpt-4o, llm:claude-3-5, human, template")
    human_reviewed: bool = Field(default=False, description="Whether an AML expert reviewed the ground truth")
    reviewer_count: int = Field(default=0, description="Number of human annotators/adjudicators")
    generator_version: Optional[str] = "1.0.0"
    seed: Optional[int] = None


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evidence_id: str = Field(..., description="Unique evidence identifier, e.g. EV-1")
    type: EvidenceType = Field(..., description="Format and modality of the evidence item")
    title: Optional[str] = Field(default="", description="Descriptive label")
    content: Union[str, Dict[str, Any], List[Any]] = Field(..., description="Evidence payload or structured data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Claim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_id: str = Field(..., description="Claim identifier within narrative, e.g. CL-1")
    span: List[int] = Field(..., description="[start_char, end_char] character offset within narrative text")
    text: str = Field(..., description="Exact textual slice of the claim")
    label: ClaimLabel = Field(..., description="Ground-truth classification label")
    error_code: Optional[ErrorCode] = Field(default=None, description="E1-E12 if CONTRADICTED or UNSUPPORTED")
    severity: Optional[Severity] = Field(default=None, description="Severity tier if error is present")
    gold_evidence_ids: List[str] = Field(default_factory=list, description="Evidence items supporting or contradicting this claim")


class CaseLabel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    safe_to_file: bool = Field(..., description="Binary determination: whether narrative has zero critical errors and is compliant to submit")
    disposition: CaseDisposition = Field(..., description="Case disposition decision")
    expected_abstention: bool = Field(default=False, description="True if evidence is ambiguous/insufficient and system should abstain")
    notes: Optional[str] = None


class Case(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str = Field(..., description="Global unique case identifier, e.g. FB-T1-000123")
    version: str = Field(default="1.0.0", description="Schema specification version")
    track: Track = Field(default=Track.T1, description="Primary evaluation track")
    split: Split = Field(default=Split.DEV, description="Dataset split: dev, public_test, private_test")
    provenance: Provenance
    typology: str = Field(..., description="Financial crime typology, e.g. structuring, ato, funnel_accounts")
    cluster_id: str = Field(..., description="Cluster identifier for cluster-aware bootstrapping, e.g. C-0042")
    evidence: List[EvidenceItem]
    narrative: str = Field(..., description="Candidate investigation narrative under evaluation")
    claims: List[Claim] = Field(default_factory=list, description="Ground-truth annotated claims")
    case_label: CaseLabel
    difficulty: Difficulty = Field(default=Difficulty.MEDIUM)
    license: str = Field(default="CC-BY-4.0")
    canary: str = Field(default="FFIRE-BENCH-CANARY-v0.1-4f9e8a7c")


# Model Prediction / Submission Schema
class PredictionClaim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    claim_id: str
    predicted_label: ClaimLabel
    cited_evidence_ids: List[str] = Field(default_factory=list)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)


class PredictionErrorSpan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    span: List[int]
    error_code: Optional[ErrorCode] = None
    severity: Optional[Severity] = None


class PredictionCase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    case_id: str
    predicted_safe_to_file: Optional[bool] = None
    predicted_disposition: Optional[CaseDisposition] = None
    predicted_confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    claims: List[PredictionClaim] = Field(default_factory=list)
    predicted_error_spans: List[PredictionErrorSpan] = Field(default_factory=list)


class PredictionBundle(BaseModel):
    model_config = ConfigDict(extra="ignore")
    benchmark_version: str = "0.1.0"
    model_name: str
    track: Track
    submission_timestamp: Optional[str] = None
    predictions: List[PredictionCase]
