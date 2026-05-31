from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import ClaimSubmission  # noqa: E402
from app.workflow import process_claim  # noqa: E402


def _matches(response, expected: dict) -> bool:
    expected_decision = expected.get("decision")
    if expected_decision is None:
        return response.stopped_early and response.decision is None
    if not response.decision or response.decision.value != expected_decision:
        return False
    if "approved_amount" in expected and response.approved_amount != expected["approved_amount"]:
        return False
    return True


def main() -> int:
    cases = json.loads((ROOT / "test_cases.json").read_text(encoding="utf-8"))["test_cases"]
    results = []
    passed = 0
    for case in cases:
        response = process_claim(ClaimSubmission(**case["input"]))
        matched = _matches(response, case["expected"])
        passed += int(matched)
        results.append(
            {
                "case_id": case["case_id"],
                "case_name": case["case_name"],
                "matched_expected": matched,
                "expected": case["expected"],
                "response": response.model_dump(mode="json"),
            }
        )
        status = "PASS" if matched else "FAIL"
        decision = response.decision.value if response.decision else "STOPPED"
        print(f"{status} {case['case_id']}: {decision} amount={response.approved_amount} confidence={response.confidence_score}")

    report = {"summary": {"passed": passed, "total": len(cases)}, "results": results}
    out_path = ROOT / "eval" / "eval_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    print(f"Passed {passed}/{len(cases)}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
