from __future__ import annotations

from datetime import timedelta

from app.models import ClaimSubmission, DecisionStatus, ExtractedClaim, PolicyResult
from app.policy_loader import member_by_id
from app.trace import TraceBuilder


def _contains_any(text: str, needles: list[str]) -> bool:
    haystack = text.casefold()
    return any(needle.casefold() in haystack for needle in needles)


def _claim_text(extracted: ExtractedClaim) -> str:
    line_text = " ".join(str(item.get("description", "")) for item in extracted.line_items)
    return " ".join(
        part
        for part in [extracted.diagnosis or "", extracted.treatment or "", line_text, " ".join(extracted.test_names)]
        if part
    )


def apply_policy(claim: ClaimSubmission, extracted: ExtractedClaim, policy: dict, trace: TraceBuilder) -> PolicyResult:
    member = member_by_id(policy, claim.member_id)
    category_key = claim.claim_category.value.lower()
    category = policy["opd_categories"][category_key]
    result = PolicyResult(eligible_amount=extracted.total_amount or claim.claimed_amount)

    claim_text = _claim_text(extracted)
    if claim.claim_category.value == "DENTAL":
        covered = category.get("covered_procedures", [])
        excluded = category.get("excluded_procedures", []) + policy["exclusions"].get("dental_exclusions", [])
        approved = 0.0
        rejected = 0.0
        for item in extracted.line_items:
            description = str(item.get("description", ""))
            amount = float(item.get("amount", 0) or 0)
            if _contains_any(description, excluded):
                rejected += amount
                result.line_item_results.append(
                    {"description": description, "amount": amount, "status": "REJECTED", "reason": "COSMETIC_EXCLUSION"}
                )
            elif _contains_any(description, covered):
                approved += amount
                result.line_item_results.append({"description": description, "amount": amount, "status": "APPROVED"})
            else:
                rejected += amount
                result.line_item_results.append(
                    {"description": description, "amount": amount, "status": "REJECTED", "reason": "NOT_LISTED_AS_COVERED"}
                )
        result.approved_amount = approved
        result.eligible_amount = approved
        result.decision_hint = DecisionStatus.PARTIAL if approved and rejected else DecisionStatus.APPROVED
        result.notes.append("Dental line items were evaluated against covered and excluded procedures.")
        trace.add("policy_engine", "WARN" if rejected else "PASS", "Dental line-item policy applied.", line_items=result.line_item_results)
        return result

    exclusions = policy["exclusions"]
    exclusion_terms = exclusions["conditions"] + exclusions.get("dental_exclusions", []) + exclusions.get("vision_exclusions", [])
    if _contains_any(claim_text, exclusion_terms) or _contains_any(claim_text, ["bariatric", "obesity", "weight loss"]):
        result.decision_hint = DecisionStatus.REJECTED
        result.rejection_reasons.append("EXCLUDED_CONDITION")
        result.notes.append("The diagnosis/treatment matches an exclusion in policy_terms.json.")
        trace.add("policy_engine", "FAIL", "Excluded treatment detected.", rejection_reasons=result.rejection_reasons, claim_text=claim_text)
        return result

    if member and member.get("join_date"):
        join_date = claim.treatment_date.fromisoformat(member["join_date"])
        specific_waits = policy["waiting_periods"]["specific_conditions"]
        for condition, days in specific_waits.items():
            aliases = [condition.replace("_", " ")]
            if condition == "diabetes":
                aliases += ["diabetes", "t2dm", "type 2 diabetes"]
            if _contains_any(claim_text, aliases):
                eligible_from = join_date + timedelta(days=int(days))
                if claim.treatment_date < eligible_from:
                    result.decision_hint = DecisionStatus.REJECTED
                    result.rejection_reasons.append("WAITING_PERIOD")
                    result.notes.append(
                        f"{condition.replace('_', ' ').title()} has a {days}-day waiting period. "
                        f"Eligible from {eligible_from.isoformat()}."
                    )
                    trace.add(
                        "policy_engine",
                        "FAIL",
                        "Specific-condition waiting period failed.",
                        condition=condition,
                        waiting_period_days=days,
                        member_join_date=member["join_date"],
                        eligible_from=eligible_from.isoformat(),
                    )
                    return result

    if claim.claim_category.value == "CONSULTATION" and claim.claimed_amount > policy["coverage"]["per_claim_limit"]:
        result.decision_hint = DecisionStatus.REJECTED
        result.rejection_reasons.append("PER_CLAIM_EXCEEDED")
        result.notes.append(
            f"Claimed amount INR {claim.claimed_amount:.0f} exceeds the per-claim limit of INR {policy['coverage']['per_claim_limit']:.0f}."
        )
        trace.add(
            "policy_engine",
            "FAIL",
            "Per-claim limit exceeded.",
            claimed_amount=claim.claimed_amount,
            per_claim_limit=policy["coverage"]["per_claim_limit"],
        )
        return result

    if claim.claim_category.value == "DIAGNOSTIC":
        high_value_tests = category.get("high_value_tests_requiring_pre_auth", [])
        threshold = category.get("pre_auth_threshold", 0)
        needs_pre_auth = claim.claimed_amount > threshold and _contains_any(claim_text, high_value_tests)
        has_pre_auth = any("pre_auth" in str(doc.content or {}).casefold() for doc in claim.documents)
        if needs_pre_auth and not has_pre_auth:
            result.decision_hint = DecisionStatus.REJECTED
            result.rejection_reasons.append("PRE_AUTH_MISSING")
            result.notes.append(
                "Pre-authorization was required for this diagnostic claim. Please resubmit with a valid pre-auth approval."
            )
            trace.add(
                "policy_engine",
                "FAIL",
                "Diagnostic pre-authorization is required and missing.",
                threshold=threshold,
                tests=extracted.test_names,
            )
            return result

    payable_base = float(extracted.total_amount or claim.claimed_amount)
    hospital_name = extracted.hospital_name or claim.hospital_name or ""
    if hospital_name in policy["network_hospitals"] and category.get("network_discount_percent"):
        discount_percent = float(category["network_discount_percent"])
        discounted = payable_base * (1 - discount_percent / 100)
        result.notes.append(
            f"Network discount ({discount_percent:.0f}%) applied first on INR {payable_base:.0f} = INR {discounted:.0f}."
        )
        payable_base = discounted
        trace.add("policy_engine", "PASS", "Network discount applied before co-pay.", hospital_name=hospital_name, discounted_amount=payable_base)

    copay = float(category.get("copay_percent", 0))
    approved = payable_base * (1 - copay / 100)
    if copay:
        result.notes.append(f"Co-pay ({copay:.0f}%) deducted from INR {payable_base:.0f}; final payable INR {approved:.0f}.")
    result.approved_amount = round(approved, 2)
    result.decision_hint = DecisionStatus.APPROVED
    trace.add(
        "policy_engine",
        "PASS",
        "Policy rules applied successfully.",
        category=claim.claim_category.value,
        approved_amount=result.approved_amount,
        notes=result.notes,
    )
    return result
