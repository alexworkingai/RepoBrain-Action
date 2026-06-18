from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_PATH = ROOT / "docs" / "release" / "SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md"

PRIMARY_REPO = "alexworkingai/Elen-MCP-v.2.2.0"
SECONDARY_REPO = "alexworkingai/repobrain-community"
REQUIRED_COMMANDS = (
    "/repobrain score",
    "/repobrain audit",
    "/repobrain audit --profile premium",
)
FORBIDDEN_STATUSES = (
    "PUBLIC_DEVELOPER_BETA_READY",
    "MARKETPLACE_READY",
    "PRODUCTION_APPROVED",
    "SECURITY_CERTIFIED",
)
PLACEHOLDERS = ("tbd", "todo", "pending", "n/a", "not run", "stub", "missing")


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_status_line(text: str) -> str:
    match = re.search(r"^Sprint status:\s*`?([A-Z0-9_]+)`?\s*$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_structured_block(text: str) -> dict[str, Any]:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise ValueError("structured_evidence_block_missing")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError("structured_evidence_block_invalid_json") from exc
    if not isinstance(payload, dict):
        raise ValueError("structured_evidence_block_invalid_shape")
    return payload


def _has_placeholder(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_placeholder(item) for item in value)
    normalized = str(value or "").strip().lower()
    return not normalized or any(token == normalized or token in normalized for token in PLACEHOLDERS)


def _result_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        command = str(row.get("command", "") or "").strip()
        if command:
            lookup[command] = row
    return lookup


def check_evidence(text: str) -> list[str]:
    errors: list[str] = []
    status = _extract_status_line(text)
    if not status:
        errors.append("sprint_status_missing")

    for forbidden in FORBIDDEN_STATUSES:
        if forbidden in text:
            errors.append(f"forbidden_status_present:{forbidden}")

    try:
        payload = _extract_structured_block(text)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    structured_status = str(payload.get("sprint_status", "") or "").strip()
    if structured_status != status:
        errors.append("structured_status_mismatch")

    if PRIMARY_REPO not in text:
        errors.append("primary_repo_missing")
    if SECONDARY_REPO not in text:
        errors.append("secondary_repo_missing")

    env = payload.get("validation_environment", {})
    if not isinstance(env, dict):
        errors.append("validation_environment_invalid")
        return errors

    mcp_results = payload.get("mcp_results", [])
    community_results = payload.get("community_results", [])
    if not isinstance(mcp_results, list) or not isinstance(community_results, list):
        errors.append("validation_results_invalid")
        return errors

    for command in REQUIRED_COMMANDS:
        if command not in text:
            errors.append(f"required_command_missing:{command}")

    if status == "TRUSTED_PARTNER_BETA_READY":
        if str(env.get("topocore_mode", "")).strip() != "real_private_entrypoint":
            errors.append("trusted_ready_requires_real_private_entrypoint")
        if str(env.get("hosted_api_used", "")).strip().lower() != "no":
            errors.append("trusted_ready_requires_hosted_api_no")
        if str(env.get("marketplace_used", "")).strip().lower() != "no":
            errors.append("trusted_ready_requires_marketplace_no")
        if _has_placeholder(payload):
            errors.append("trusted_ready_contains_placeholders")

        checklist = payload.get("leakage_scan_checklist", {})
        if not isinstance(checklist, dict):
            errors.append("leakage_scan_checklist_invalid")
        else:
            if any(str(value or "").strip().lower() != "yes" for value in checklist.values()):
                errors.append("trusted_ready_requires_leakage_scan_yes")

        for repo_name, rows in ((PRIMARY_REPO, mcp_results), (SECONDARY_REPO, community_results)):
            lookup = _result_lookup(rows)
            for command in REQUIRED_COMMANDS:
                row = lookup.get(command)
                if row is None:
                    errors.append(f"trusted_ready_missing_row:{repo_name}:{command}")
                    continue
                if str(row.get("repository", "")).strip() != repo_name:
                    errors.append(f"trusted_ready_repository_mismatch:{repo_name}:{command}")
                if str(row.get("topocore_mode", "")).strip() != "real_private_entrypoint":
                    errors.append(f"trusted_ready_stub_or_missing_topocore_mode:{repo_name}:{command}")
                if str(row.get("idempotency_pass", "")).strip().lower() != "yes":
                    errors.append(f"trusted_ready_idempotency_missing:{repo_name}:{command}")
                if str(row.get("leakage_scan_pass", "")).strip().lower() != "yes":
                    errors.append(f"trusted_ready_leakage_scan_missing:{repo_name}:{command}")
                for key in ("queue_comment_url", "final_result_url", "request_id", "control_worker_run_ref"):
                    if _has_placeholder(row.get(key)):
                        errors.append(f"trusted_ready_missing_field:{repo_name}:{command}:{key}")
    elif status == "SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING":
        if str(env.get("topocore_mode", "")).strip() == "real_private_entrypoint":
            errors.append("stub_pending_should_not_claim_real_topocore")
    elif status == "SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING":
        pass
    else:
        errors.append(f"unsupported_sprint_status:{status}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Sprint 94E validation evidence for false readiness claims.")
    parser.add_argument("--path", type=Path, default=DEFAULT_EVIDENCE_PATH)
    args = parser.parse_args()

    text = _load_text(args.path)
    errors = check_evidence(text)
    if errors:
        print("SPRINT94E_EVIDENCE_CHECK=FAIL")
        for error in errors:
            print(error)
        return 1
    print("SPRINT94E_EVIDENCE_CHECK=PASS")
    print(f"EVIDENCE_PATH={args.path}")
    print(f"SPRINT_STATUS={_extract_status_line(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
