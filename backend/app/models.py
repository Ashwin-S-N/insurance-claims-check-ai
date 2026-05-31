from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ClaimCategory(str, Enum):
    CONSULTATION = "CONSULTATION"
    DIAGNOSTIC = "DIAGNOSTIC"
    PHARMACY = "PHARMACY"
    DENTAL = "DENTAL"
    VISION = "VISION"
    ALTERNATIVE_MEDICINE = "ALTERNATIVE_MEDICINE"


class DocumentType(str, Enum):
    PRESCRIPTION = "PRESCRIPTION"
    HOSPITAL_BILL = "HOSPITAL_BILL"
    LAB_REPORT = "LAB_REPORT"
    DIAGNOSTIC_REPORT = "DIAGNOSTIC_REPORT"
    PHARMACY_BILL = "PHARMACY_BILL"
    DISCHARGE_SUMMARY = "DISCHARGE_SUMMARY"
    DENTAL_REPORT = "DENTAL_REPORT"
    UNKNOWN = "UNKNOWN"


class DecisionStatus(str, Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class StopCode(str, Enum):
    DOCUMENTS_MISSING_OR_WRONG = "DOCUMENTS_MISSING_OR_WRONG"
    DOCUMENT_UNREADABLE = "DOCUMENT_UNREADABLE"
    PATIENT_MISMATCH = "PATIENT_MISMATCH"
    INVALID_MEMBER = "INVALID_MEMBER"


class UploadedDocument(BaseModel):
    file_id: str
    file_name: str | None = None
    actual_type: DocumentType = DocumentType.UNKNOWN
    quality: Literal["GOOD", "UNREADABLE", "LOW"] | None = "GOOD"
    patient_name_on_doc: str | None = None
    content: dict[str, Any] | None = None


class ClaimsHistoryItem(BaseModel):
    claim_id: str | None = None
    date: date
    amount: float
    provider: str | None = None


class ClaimSubmission(BaseModel):
    member_id: str
    policy_id: str
    claim_category: ClaimCategory
    treatment_date: date
    claimed_amount: float = Field(gt=0)
    ytd_claims_amount: float = 0
    hospital_name: str | None = None
    claims_history: list[ClaimsHistoryItem] = Field(default_factory=list)
    simulate_component_failure: bool = False
    documents: list[UploadedDocument]


class TraceEvent(BaseModel):
    step: str
    status: Literal["PASS", "FAIL", "WARN", "SKIPPED", "INFO"]
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExtractedClaim(BaseModel):
    patient_names: list[str] = Field(default_factory=list)
    diagnosis: str | None = None
    treatment: str | None = None
    hospital_name: str | None = None
    doctor_name: str | None = None
    doctor_registration: str | None = None
    test_names: list[str] = Field(default_factory=list)
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    total_amount: float | None = None
    confidence: float = 0.90
    fields: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class PolicyResult(BaseModel):
    eligible_amount: float = 0
    approved_amount: float = 0
    decision_hint: DecisionStatus | None = None
    rejection_reasons: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    line_item_results: list[dict[str, Any]] = Field(default_factory=list)
    confidence_delta: float = 0


class FraudResult(BaseModel):
    fraud_score: float
    signals: list[str] = Field(default_factory=list)
    manual_review: bool = False
    failed: bool = False


class DecisionResponse(BaseModel):
    claim_id: str
    stopped_early: bool = False
    stop_code: StopCode | None = None
    message: str
    decision: DecisionStatus | None = None
    approved_amount: float = 0
    confidence_score: float = 0
    rejection_reasons: list[str] = Field(default_factory=list)
    line_item_results: list[dict[str, Any]] = Field(default_factory=list)
    fraud_score: float | None = None
    fraud_signals: list[str] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    extracted: ExtractedClaim | None = None
