#!/usr/bin/env python3
"""Validate the static workflow eval contract for api-test-E10."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_MODES = {
    "new/capture_driven",
    "new/reference_case",
    "new/curl_manual",
    "new/java_controller",
    "maintenance/capture_driven",
    "maintenance/reference_case",
    "maintenance/curl_manual",
    "maintenance/pytest_driven",
    "utility/url_dedup",
    "utility/encoding_fix",
    "utility/pytest_inventory",
}
VALID_CATEGORIES = {"new", "maintenance", "utility", "negative"}


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read JSON: {exc}"]

    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        return errors + ["cases must be a non-empty list"]

    seen: set[str] = set()
    branches: set[str] = set()
    for index, case in enumerate(payload["cases"], start=1):
        prefix = f"case {index}"
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"{prefix}: id must be a non-empty string")
        elif case_id in seen:
            errors.append(f"{prefix}: duplicate id {case_id!r}")
        else:
            seen.add(case_id)
        category = case.get("category")
        if category not in VALID_CATEGORIES:
            errors.append(f"{prefix}: invalid category {category!r}")
        if case.get("expected_task_type") != category:
            errors.append(f"{prefix}: expected_task_type must match category")
        branch = case.get("branch")
        if not isinstance(branch, str) or not branch:
            errors.append(f"{prefix}: branch is required")
        else:
            branches.add(branch)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{prefix}: prompt must be non-empty")
        if not isinstance(case.get("expected_trigger"), bool):
            errors.append(f"{prefix}: expected_trigger must be boolean")
        elif category in {"new", "maintenance", "utility"} and not case["expected_trigger"]:
            errors.append(f"{prefix}: {category} case must trigger")
        if not isinstance(case.get("must_read"), list):
            errors.append(f"{prefix}: must_read must be a list")
        else:
            for relative in case["must_read"]:
                if not (path.parent.parent / relative).is_file():
                    errors.append(f"{prefix}: missing must_read file {relative!r}")
        for field in ("expected_outputs", "must", "must_not"):
            if not isinstance(case.get(field), list) or not case[field]:
                errors.append(f"{prefix}: {field} must be a non-empty list")
        if category in {"new", "maintenance"} and not case.get("expected_mode"):
            errors.append(f"{prefix}: expected_mode required for {category}")
        if case.get("expected_mode") and branch != f"{category}/{case['expected_mode']}":
            errors.append(f"{prefix}: branch and expected_mode do not match")
        if category == "negative" and case.get("expected_trigger") is not False:
            errors.append(f"{prefix}: negative case must not trigger")

    missing = sorted(REQUIRED_MODES - branches)
    if missing:
        errors.append(f"missing required branches: {', '.join(missing)}")
    if not any(case.get("category") == "negative" for case in payload["cases"]):
        errors.append("at least one negative case is required")
    return errors


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("workflow_eval_set.json")
    errors = validate(path)
    if errors:
        print("workflow eval validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    print(f"workflow eval validation passed: {len(payload['cases'])} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
