from __future__ import annotations

from typing import TypedDict
from uuid import uuid4

try:
    from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - local fallback keeps eval usable without installed deps.
    END = "__end__"
    StateGraph = None

from app.agents.decision import make_decision
from app.agents.document_verification import verify_documents
from app.agents.extraction import extract_claim_fields
from app.agents.fraud import detect_fraud
from app.agents.policy_engine import apply_policy
from app.models import ClaimSubmission, DecisionResponse, ExtractedClaim, FraudResult, PolicyResult
from app.policy_loader import load_policy
from app.trace import TraceBuilder


class ClaimState(TypedDict, total=False):
    claim: ClaimSubmission
    policy: dict
    trace: TraceBuilder
    claim_id: str
    stopped_response: DecisionResponse | None
    extracted: ExtractedClaim
    policy_result: PolicyResult
    fraud_result: FraudResult
    response: DecisionResponse


def _load(state: ClaimState) -> ClaimState:
    state["policy"] = load_policy()
    state["trace"] = TraceBuilder()
    state["claim_id"] = f"CLM-{uuid4().hex[:10].upper()}"
    state["trace"].add("trace_builder", "INFO", "Trace initialized for claim pipeline.", claim_id=state["claim_id"])
    return state


def _verify(state: ClaimState) -> ClaimState:
    stopped = verify_documents(state["claim"], state["policy"], state["trace"])
    if stopped:
        stopped.claim_id = state["claim_id"]
        state["stopped_response"] = stopped
        state["response"] = stopped
    return state


def _route_after_verify(state: ClaimState) -> str:
    return "stop" if state.get("stopped_response") else "extract"


def _extract(state: ClaimState) -> ClaimState:
    state["extracted"] = extract_claim_fields(state["claim"], state["trace"])
    return state


def _policy(state: ClaimState) -> ClaimState:
    state["policy_result"] = apply_policy(state["claim"], state["extracted"], state["policy"], state["trace"])
    return state


def _fraud(state: ClaimState) -> ClaimState:
    state["fraud_result"] = detect_fraud(state["claim"], state["extracted"], state["policy"], state["trace"])
    return state


def _decide(state: ClaimState) -> ClaimState:
    state["response"] = make_decision(
        state["claim_id"],
        state["claim"],
        state["extracted"],
        state["policy_result"],
        state["fraud_result"],
        state["trace"],
    )
    return state


def build_graph():
    if StateGraph is None:
        return None
    graph = StateGraph(ClaimState)
    graph.add_node("load_context", _load)
    graph.add_node("document_verification_agent", _verify)
    graph.add_node("extraction_agent", _extract)
    graph.add_node("policy_engine_agent", _policy)
    graph.add_node("fraud_agent", _fraud)
    graph.add_node("decision_agent", _decide)
    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "document_verification_agent")
    graph.add_conditional_edges(
        "document_verification_agent",
        _route_after_verify,
        {"stop": END, "extract": "extraction_agent"},
    )
    graph.add_edge("extraction_agent", "policy_engine_agent")
    graph.add_edge("policy_engine_agent", "fraud_agent")
    graph.add_edge("fraud_agent", "decision_agent")
    graph.add_edge("decision_agent", END)
    return graph.compile()


CLAIMS_GRAPH = build_graph()


def process_claim(claim: ClaimSubmission) -> DecisionResponse:
    if CLAIMS_GRAPH is None:
        state: ClaimState = {"claim": claim}
        for node in (_load, _verify):
            state = node(state)
        if state.get("stopped_response"):
            return state["response"]
        for node in (_extract, _policy, _fraud, _decide):
            state = node(state)
        return state["response"]
    state = CLAIMS_GRAPH.invoke({"claim": claim})
    return state["response"]
