from __future__ import annotations

from app.models import ClaimSubmission, DecisionResponse, DecisionStatus, ExtractedClaim, FraudResult, PolicyResult
from app.trace import TraceBuilder


def make_decision(
    claim_id: str,
    claim: ClaimSubmission,
    extracted: ExtractedClaim,
    policy_result: PolicyResult,
    fraud_result: FraudResult,
    trace: TraceBuilder,
) -> DecisionResponse:
    confidence = extracted.confidence + policy_result.confidence_delta
    notes = list(policy_result.notes)

    if fraud_result.failed:
        confidence -= 0.22
        notes.append("Manual review is recommended because fraud analysis was skipped after a simulated component failure.")
    elif fraud_result.manual_review:
        confidence -= 0.18

    if policy_result.decision_hint == DecisionStatus.REJECTED:
        decision = DecisionStatus.REJECTED
        approved_amount = 0.0
        message = "Claim rejected: " + "; ".join(policy_result.notes)
    elif fraud_result.manual_review:
        decision = DecisionStatus.MANUAL_REVIEW
        approved_amount = 0.0
        message = "Claim routed to manual review due to fraud signals: " + "; ".join(fraud_result.signals)
    elif policy_result.decision_hint == DecisionStatus.PARTIAL:
        decision = DecisionStatus.PARTIAL
        approved_amount = policy_result.approved_amount
        message = "Claim partially approved. " + "; ".join(notes)
    else:
        decision = DecisionStatus.APPROVED
        approved_amount = policy_result.approved_amount
        message = "Claim approved. " + "; ".join(notes)

    if claim.simulate_component_failure and decision == DecisionStatus.APPROVED:
        message += " Manual review is recommended due to incomplete processing."

    confidence = max(0.35, min(0.98, confidence))
    trace.add(
        "decision_agent",
        "PASS" if decision in {DecisionStatus.APPROVED, DecisionStatus.PARTIAL} else "WARN",
        "Final claim decision produced.",
        decision=decision.value,
        approved_amount=approved_amount,
        confidence_score=round(confidence, 2),
    )
    return DecisionResponse(
        claim_id=claim_id,
        stopped_early=False,
        message=message,
        decision=decision,
        approved_amount=round(approved_amount, 2),
        confidence_score=round(confidence, 2),
        rejection_reasons=policy_result.rejection_reasons,
        line_item_results=policy_result.line_item_results,
        fraud_score=fraud_result.fraud_score,
        fraud_signals=fraud_result.signals,
        trace=trace.list(),
        extracted=extracted,
    )
