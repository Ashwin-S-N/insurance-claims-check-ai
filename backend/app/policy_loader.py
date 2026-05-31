from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import get_settings


@lru_cache
def load_policy(path: str | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path else get_settings().policy_terms_path
    with policy_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def member_by_id(policy: dict[str, Any], member_id: str) -> dict[str, Any] | None:
    return next((member for member in policy.get("members", []) if member["member_id"] == member_id), None)
