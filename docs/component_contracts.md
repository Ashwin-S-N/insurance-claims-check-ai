# Component Contracts

## Claim Submission API

Input: `ClaimSubmission` JSON with member ID, policy ID, claim category, treatment date, claimed amount, optional history, and documents.

Output: `DecisionResponse` with decision, approved amount, confidence, rejection reasons, fraud signals, extracted fields, and full trace.

Errors: validation errors for malformed JSON; agent-level failures should be returned as degraded decisions, not 500s.

## Document Verification Agent

Input: `ClaimSubmission`, policy document requirements, trace builder.

Output: `None` when validation passes, or an early `DecisionResponse` with `stopped_early=true`.

Failure modes: missing/wrong document type, unreadable document, patient mismatch, invalid member.

## Extraction Agent

Input: verified claim documents.

Output: `ExtractedClaim` containing patient names, diagnosis, treatment, provider, line items, total amount, confidence, warnings, and raw extracted fields.

Failure modes: missing totals or low-quality documents reduce confidence and add warnings; the pipeline continues.

## Policy Engine Agent

Input: claim, extracted fields, `policy_terms.json`.

Output: `PolicyResult` with decision hint, approved amount, rejection reasons, notes, line-item results, and confidence delta.

Rules applied: waiting periods, exclusions, pre-auth, dental/vision exclusions, network discount before co-pay, and configured claim limits.

## Fraud Agent

Input: claim, extracted fields, policy fraud thresholds.

Output: `FraudResult` with fraud score, signals, manual-review flag, and failed flag.

Failure modes: simulated or real component failure emits `FRAUD_AGENT_SKIPPED_DUE_TO_FAILURE`, lowers final confidence, and recommends manual review.

## Decision Agent

Input: claim ID, claim, extraction result, policy result, fraud result, trace.

Output: final `DecisionResponse`.

Decision mapping: policy rejection wins over approval; fraud manual-review routes to `MANUAL_REVIEW`; partial line-item approvals produce `PARTIAL`; otherwise covered claims are `APPROVED`.

## Trace Builder

Input: step name, status, message, structured data.

Output: ordered `TraceEvent[]`.

Contract: every agent must append at least one event; early stops must include the exact member-facing reason.
