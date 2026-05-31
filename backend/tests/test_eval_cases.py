import json
from pathlib import Path

from app.models import ClaimSubmission
from app.workflow import process_claim


ROOT = Path(__file__).resolve().parents[2]


def test_all_supplied_cases_match_expected_decisions():
    cases = json.loads((ROOT / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]
    for case in cases:
        response = process_claim(ClaimSubmission(**case["input"]))
        expected_decision = case["expected"].get("decision")
        if expected_decision is None:
            assert response.stopped_early, case["case_id"]
            assert response.decision is None, case["case_id"]
        else:
            assert response.decision.value == expected_decision, case["case_id"]
        if "approved_amount" in case["expected"]:
            assert response.approved_amount == case["expected"]["approved_amount"], case["case_id"]
