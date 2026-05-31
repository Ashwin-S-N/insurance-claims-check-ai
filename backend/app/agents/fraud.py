from __future__ import annotations

from app.models import ClaimSubmission, ExtractedClaim, FraudResult
from app.trace import TraceBuilder


def detect_fraud(claim: ClaimSubmission, extracted: ExtractedClaim, policy: dict, trace: TraceBuilder) -> FraudResult:
    if claim.simulate_component_failure:
        trace.add(
            "fraud_agent",
            "SKIPPED",
            "Fraud agent failure simulated; continuing with policy and decision agents.",
            component="fraud_agent",
        )
        return FraudResult(fraud_score=0.0, signals=["FRAUD_AGENT_SKIPPED_DUE_TO_FAILURE"], failed=True)

    thresholds = policy["fraud_thresholds"]
    score = 0.05
    signals: list[str] = []
    same_day_count = sum(1 for item in claim.claims_history if item.date == claim.treatment_date)
    if same_day_count >= thresholds["same_day_claims_limit"]:
        score += 0.78
        signals.append(
            f"SAME_DAY_CLAIM_PATTERN: {same_day_count} previous claims on {claim.treatment_date}; this is claim #{same_day_count + 1}."
        )
    if claim.claimed_amount >= thresholds["high_value_claim_threshold"]:
        score += 0.25
        signals.append(f"HIGH_VALUE_CLAIM: claimed amount {claim.claimed_amount} exceeds threshold.")
    for item in extracted.line_items:
        if "correction" in str(item).lower() or "duplicate" in str(item).lower():
            score += 0.20
            signals.append("DOCUMENT_ALTERATION_SIGNAL")

    score = min(score, 0.99)
    manual_review = score >= thresholds["fraud_score_manual_review_threshold"]
    trace.add(
        "fraud_agent",
        "WARN" if manual_review else "PASS",
        "Fraud signals evaluated.",
        fraud_score=score,
        signals=signals,
        manual_review=manual_review,
    )
    return FraudResult(fraud_score=score, signals=signals, manual_review=manual_review)
