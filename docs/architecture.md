# Architecture

## Overview

The system is a FastAPI backend, a Next.js demo UI, and a LangGraph-orchestrated claims pipeline. The backend treats `policy_terms.json` as the source of truth for members, document requirements, exclusions, waiting periods, network hospitals, fraud thresholds, and financial rules. The eval runner uses the same API-level models and workflow as the web app.

## Runtime Flow

1. `Document Verification Agent` validates required document types for the claim category, unreadable uploads, and patient-name consistency. It can stop the pipeline before a claim decision.
2. `Extraction Agent` normalizes structured fields from document metadata/content. For real files, `app/llm.py` provides an optional Gemini 2.5 Flash adapter after OCR or text extraction.
3. `Policy Engine Agent` dynamically reads `policy_terms.json` and applies waiting periods, exclusions, pre-auth, network discounts, co-pay, and line-item adjudication.
4. `Fraud Agent` checks same-day claim patterns, high-value claims, and alteration signals. Component failure can be simulated and is reflected in trace/confidence.
5. `Decision Agent` converts policy and fraud outputs into `APPROVED`, `PARTIAL`, `REJECTED`, or `MANUAL_REVIEW`.
6. `Trace Builder` records every step with status, message, timestamp, and structured data.

## Why This Design

LangGraph keeps each agent independently testable while making the end-to-end control flow visible. Early document failures short-circuit before extraction and policy evaluation, which matches the member experience requirement. Deterministic fixture extraction makes the evaluation reproducible; Gemini is isolated behind an adapter so LLM failures do not compromise policy correctness.

## Graceful Degradation

Agent failures are represented as trace events instead of uncaught exceptions. In TC011 the fraud component is skipped, the claim still receives a decision, confidence is reduced, and manual review is recommended in the final message.

## Scaling Notes

At 10x load, the API should move long-running extraction into a queue, persist workflow state in Postgres, store documents in object storage, and add distributed tracing. The policy engine is stateless and can scale horizontally. LLM calls should use timeout budgets, retries, provider circuit breakers, and response-schema validation.

## Limitations

The demo does not include binary OCR ingestion by default; uploaded file extraction is represented by structured document metadata for repeatable evals. The optional Gemini adapter is ready for an OCR/text input path, but production-grade PDF/image preprocessing would be the next investment.
