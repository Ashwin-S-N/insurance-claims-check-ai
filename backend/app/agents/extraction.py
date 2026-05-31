from __future__ import annotations

from typing import Any

from app.models import ClaimSubmission, ExtractedClaim
from app.trace import TraceBuilder


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_claim_fields(claim: ClaimSubmission, trace: TraceBuilder) -> ExtractedClaim:
    patient_names: list[str] = []
    line_items: list[dict[str, Any]] = []
    test_names: list[str] = []
    fields: dict[str, Any] = {}
    total_amount: float | None = None
    diagnosis = treatment = hospital_name = doctor_name = doctor_registration = None
    confidence = 0.92
    warnings: list[str] = []

    for doc in claim.documents:
        content = doc.content or {}
        doc_name = doc.patient_name_on_doc or content.get("patient_name")
        if doc_name:
            patient_names.append(doc_name)
        diagnosis = diagnosis or content.get("diagnosis")
        treatment = treatment or content.get("treatment")
        hospital_name = hospital_name or content.get("hospital_name") or claim.hospital_name
        doctor_name = doctor_name or content.get("doctor_name")
        doctor_registration = doctor_registration or content.get("doctor_registration")
        line_items.extend(content.get("line_items") or [])
        if content.get("tests_ordered"):
            test_names.extend(content["tests_ordered"])
        if content.get("test_name"):
            test_names.append(content["test_name"])
        if content.get("total") is not None:
            total_amount = _as_float(content.get("total"))
        fields[doc.file_id] = {"document_type": doc.actual_type.value, "content": content}
        if doc.quality == "LOW":
            confidence -= 0.10
            warnings.append(f"{doc.file_id} is low quality; extracted fields may be incomplete.")

    if total_amount is None:
        total_amount = claim.claimed_amount
        warnings.append("No document total found; using submitted claimed amount.")
        confidence -= 0.04
    if not line_items and total_amount is not None:
        line_items = [{"description": claim.claim_category.value.title(), "amount": total_amount}]

    extracted = ExtractedClaim(
        patient_names=sorted(set(patient_names)),
        diagnosis=diagnosis,
        treatment=treatment,
        hospital_name=hospital_name,
        doctor_name=doctor_name,
        doctor_registration=doctor_registration,
        test_names=test_names,
        line_items=line_items,
        total_amount=total_amount,
        confidence=max(0.45, confidence),
        fields=fields,
        warnings=warnings,
    )
    trace.add(
        "extraction_agent",
        "PASS" if extracted.confidence >= 0.75 else "WARN",
        "Structured claim fields extracted from document metadata/content.",
        confidence=extracted.confidence,
        patient_names=extracted.patient_names,
        total_amount=extracted.total_amount,
        warnings=warnings,
    )
    return extracted
