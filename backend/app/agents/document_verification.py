from __future__ import annotations

from collections import Counter

from app.models import ClaimSubmission, DecisionResponse, DocumentType, StopCode
from app.policy_loader import member_by_id
from app.trace import TraceBuilder


def verify_documents(claim: ClaimSubmission, policy: dict, trace: TraceBuilder) -> DecisionResponse | None:
    member = member_by_id(policy, claim.member_id)
    if not member:
        trace.add("document_verification", "FAIL", f"Member {claim.member_id} was not found.")
        return DecisionResponse(
            claim_id="pending",
            stopped_early=True,
            stop_code=StopCode.INVALID_MEMBER,
            message=f"Member {claim.member_id} is not covered under policy {claim.policy_id}.",
            trace=trace.list(),
        )

    requirements = policy["document_requirements"][claim.claim_category.value]
    required = set(requirements["required"])
    uploaded = [doc.actual_type.value for doc in claim.documents]
    counts = Counter(uploaded)
    missing = [doc_type for doc_type in required if counts[doc_type] == 0]
    extra_required_duplicates = [doc_type for doc_type, count in counts.items() if count > 1 and doc_type in required]

    if missing:
        uploaded_summary = ", ".join(f"{count} x {doc_type}" for doc_type, count in counts.items())
        message = (
            f"This {claim.claim_category.value.lower()} claim needs {', '.join(sorted(required))}. "
            f"You uploaded {uploaded_summary}. Please upload the missing {', '.join(missing)} document."
        )
        trace.add(
            "document_verification",
            "FAIL",
            message,
            required=sorted(required),
            uploaded=uploaded,
            missing=missing,
            duplicate_required_documents=extra_required_duplicates,
        )
        return DecisionResponse(
            claim_id="pending",
            stopped_early=True,
            stop_code=StopCode.DOCUMENTS_MISSING_OR_WRONG,
            message=message,
            trace=trace.list(),
        )

    for doc in claim.documents:
        if doc.quality == "UNREADABLE":
            doc_label = doc.actual_type.value.replace("_", " ").lower()
            message = (
                f"The uploaded {doc_label} ({doc.file_name or doc.file_id}) cannot be read. "
                f"Please re-upload a clear image or PDF of that specific {doc_label}; the claim has not been rejected."
            )
            trace.add("document_verification", "FAIL", message, file_id=doc.file_id, document_type=doc.actual_type)
            return DecisionResponse(
                claim_id="pending",
                stopped_early=True,
                stop_code=StopCode.DOCUMENT_UNREADABLE,
                message=message,
                trace=trace.list(),
            )

    names: dict[str, str] = {}
    for doc in claim.documents:
        name = doc.patient_name_on_doc or (doc.content or {}).get("patient_name")
        if name:
            names[doc.file_id] = name
    unique_names = sorted({name.casefold(): name for name in names.values()}.values())
    if len(unique_names) > 1:
        details = "; ".join(f"{file_id}: {name}" for file_id, name in names.items())
        message = (
            "The uploaded documents appear to belong to different patients. "
            f"I found these names: {details}. Please upload documents for the same patient."
        )
        trace.add("document_verification", "FAIL", message, patient_names_by_file=names)
        return DecisionResponse(
            claim_id="pending",
            stopped_early=True,
            stop_code=StopCode.PATIENT_MISMATCH,
            message=message,
            trace=trace.list(),
        )

    expected_name = member["name"]
    mismatched = {file_id: name for file_id, name in names.items() if name.casefold() != expected_name.casefold()}
    if mismatched:
        trace.add(
            "document_verification",
            "WARN",
            "Document patient name does not exactly match member roster; continuing because all documents match each other.",
            expected_member_name=expected_name,
            document_names=mismatched,
        )

    trace.add(
        "document_verification",
        "PASS",
        "Required documents are present, readable, and internally consistent.",
        required=sorted(required),
        uploaded=uploaded,
    )
    return None
