from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db, list_claims, save_response
from app.models import ClaimSubmission, DecisionResponse
from app.policy_loader import load_policy
from app.workflow import process_claim

app = FastAPI(title="Plum Claims AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/policy")
def policy() -> dict:
    return load_policy()


@app.post("/claims", response_model=DecisionResponse)
def submit_claim(claim: ClaimSubmission) -> DecisionResponse:
    response = process_claim(claim)
    save_response(claim.member_id, response)
    return response


@app.get("/claims")
def recent_claims() -> list[dict]:
    return list_claims()
