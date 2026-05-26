from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
    load_topocore_v6_public_api,
    resolve_topocore_v6_runtime_mode,
)
from repobrain.topocore_v6_advisory_artifact import build_advisory_artifact
from repobrain.topocore_v6_decision_diff import build_decision_diff_report

_FORBIDDEN_OUTPUT_TOKENS = (
    "decide_raw",
    "compression_stats",
    "raw_trace",
    "governance_internals",
    "event_internals",
    "artifact_internals",
    "raw_query",
    "raw_code",
    "raw_diff",
    "secret",
    "token",
    "api_key",
    "private_key",
    "dotenv",
    ".env",
)


def _env_flag(name: str, default: str = "0", env: Mapping[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    return str(source.get(name, default) or default).strip()


def _is_enabled(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_LOCAL_VALIDATE", env=env) == "1"


def _requires_local(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_REQUIRE_LOCAL", env=env) == "1"


def _allow_decide_raw(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_ALLOW_DECIDE_RAW", env=env) == "1"


def _json_mode(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON", env=env) == "1"


def _runtime_mode(env: Mapping[str, str] | None = None) -> str:
    return _env_flag("RB_TOPOCORE_V6_RUNTIME_MODE", default="auto", env=env)


def _local_path(env: Mapping[str, str] | None = None) -> str:
    return _env_flag("RB_TOPOCORE_V6_LOCAL_PATH", default="", env=env)


def _print_line(message: str, stdout: TextIO | None = None) -> None:
    stream = stdout if stdout is not None else sys.stdout
    stream.write(f"{message}\n")


def _load_topocore_v6_module(env: Mapping[str, str] | None = None) -> tuple[Any | None, Exception | None]:
    local_path = _local_path(env) or None
    runtime_mode = _runtime_mode(env)
    try:
        return load_topocore_v6_public_api(local_path=local_path, runtime_mode=runtime_mode), None
    except Exception as exc:  # pragma: no cover - exercised through tests
        return None, exc


def _sanitize_text(value: Any) -> str:
    return str(value or "").strip()


def _sanitize_output_line(text: str) -> str:
    sanitized = " ".join(str(text or "").split())
    for token in _FORBIDDEN_OUTPUT_TOKENS:
        sanitized = sanitized.replace(token, "[redacted]")
    return sanitized


def _build_fixture_definitions() -> list[dict[str, Any]]:
    base_candidates = (
        RepoBrainV6CandidateRef(
            chunk_id="chunk-a",
            score_local=0.9,
            metadata={"path": "repobrain/review.py", "kind": "diff"},
        ),
    )
    return [
        {
            "label": "minimal_ask",
            "bundle": RepoBrainV6SummaryBundle(
                query="Summarize the current project state.",
                intent_summary={
                    "command": "ask",
                    "task_type_candidate": "ask",
                    "user_goal": "summarize current state",
                },
                candidates=base_candidates,
                evidence_summary={"confirmed_facts": ["one bounded candidate available"]},
            ),
            "v5_snapshot": {
                "command": "ask",
                "route": "proceed",
                "selected_chunk_ids": ["chunk-a"],
                "execution_mode": "manual_local_fixture",
                "llm_intent": "answer_question",
                "llm_decision_reason_code": "baseline_proceed",
                "verification_gate_decision": "pass",
                "verification_gate_reason": "fixture_safe",
                "safe_reason_code": "ask_proceed",
                "has_patch_candidate": False,
                "no_patch_reason": "",
            },
        },
        {
            "label": "review_like",
            "bundle": RepoBrainV6SummaryBundle(
                query="Review the pull request.",
                intent_summary={
                    "command": "review",
                    "task_type_candidate": "review",
                    "user_goal": "review diff safely",
                },
                candidates=base_candidates,
                pr_context_summary={"pr_state": "OPEN", "diff_scope": "narrow"},
                evidence_summary={"confirmed_facts": ["tests passed"]},
                risk_items=({"risk_area": "runtime", "severity_hint": "low"},),
                verification_results={"checks": ["test: pass", "ruff: pass"]},
            ),
            "v5_snapshot": {
                "command": "review",
                "route": "proceed",
                "selected_chunk_ids": ["chunk-a"],
                "execution_mode": "manual_local_fixture",
                "llm_intent": "review_changes",
                "llm_decision_reason_code": "review_ready",
                "verification_gate_decision": "pass",
                "verification_gate_reason": "checks_green",
                "safe_reason_code": "review_proceed",
                "has_patch_candidate": False,
                "no_patch_reason": "",
            },
        },
        {
            "label": "weak_context",
            "bundle": RepoBrainV6SummaryBundle(
                query="Review the pull request with missing context.",
                intent_summary={
                    "command": "review",
                    "task_type_candidate": "review",
                    "user_goal": "review but acknowledge gaps",
                },
                candidates=base_candidates,
                unknowns_summary={"unknowns": ["missing benchmark", "missing deployment context"]},
                evidence_summary={"confirmed_facts": []},
            ),
            "v5_snapshot": {
                "command": "review",
                "route": "needs_more_information",
                "selected_chunk_ids": ["chunk-a"],
                "execution_mode": "manual_local_fixture",
                "llm_intent": "review_changes",
                "llm_decision_reason_code": "missing_context",
                "verification_gate_decision": "wait",
                "verification_gate_reason": "insufficient_context",
                "safe_reason_code": "needs_more_information",
                "has_patch_candidate": False,
                "no_patch_reason": "",
            },
        },
        {
            "label": "blocked_safety",
            "bundle": RepoBrainV6SummaryBundle(
                query="Assess an intentionally blocked safety scenario.",
                intent_summary={
                    "command": "review",
                    "task_type_candidate": "review",
                    "user_goal": "test blocked safety handling",
                    "safety_notes": ["blocked scenario fixture"],
                },
                candidates=base_candidates,
                risk_items=({"risk_area": "policy", "severity_hint": "high"},),
                unknowns_summary={"unknowns": ["safety policy details hidden"]},
            ),
            "v5_snapshot": {
                "command": "review",
                "route": "blocked",
                "selected_chunk_ids": ["chunk-a"],
                "execution_mode": "manual_local_fixture",
                "llm_intent": "review_changes",
                "llm_decision_reason_code": "policy_block",
                "verification_gate_decision": "blocked",
                "verification_gate_reason": "policy_block",
                "safe_reason_code": "policy_block",
                "has_patch_candidate": False,
                "no_patch_reason": "",
            },
        },
        {
            "label": "fix_like_governance",
            "bundle": RepoBrainV6SummaryBundle(
                query="Prepare a bounded fix governance summary.",
                intent_summary={
                    "command": "fix",
                    "task_type_candidate": "fix",
                    "user_goal": "summarize safe fix options",
                },
                candidates=base_candidates,
                fix_draft_summary={
                    "localized_target_hint": "repobrain/patch_validator.py",
                    "no_patch_reason": "insufficient localized evidence",
                    "patch_safety_notes": ["manual-only", "no patch applied"],
                    "grounding_notes": ["needs more evidence"],
                },
            ),
            "v5_snapshot": {
                "command": "fix",
                "route": "no_patch",
                "selected_chunk_ids": ["chunk-a"],
                "execution_mode": "manual_local_fixture",
                "llm_intent": "suggest_fix",
                "llm_decision_reason_code": "no_localized_evidence",
                "verification_gate_decision": "blocked",
                "verification_gate_reason": "no_localized_evidence",
                "safe_reason_code": "no_patch",
                "has_patch_candidate": False,
                "no_patch_reason": "insufficient localized evidence",
            },
        },
    ]


def _build_engine_objects(module: Any, preview: Mapping[str, Any]) -> Any:
    try:
        engine_query = module.EngineQuery(
            text=preview["query"],
            task_type=preview["task_type"],
        )
        engine_candidates = [
            module.EngineCandidate(
                chunk_id=item["chunk_id"],
                score_local=item["score_local"],
                metadata=item.get("metadata", {}),
            )
            for item in preview["candidates"]
        ]
        return module.EngineRequest(
            query=engine_query,
            candidates=engine_candidates,
            limits=preview["limits"],
            policy=preview["policy"],
        )
    except Exception as exc:
        raise RuntimeError("platform_semantic_gap") from exc


def _extract_safe_decision_value(decision: Any, name: str) -> str:
    if isinstance(decision, Mapping):
        return _sanitize_text(decision.get(name))
    return _sanitize_text(getattr(decision, name, ""))


def _build_v6_advisory_snapshot(
    *,
    request: Any,
    preview: Mapping[str, Any],
    external_result: Any,
) -> dict[str, Any]:
    status = _extract_safe_decision_value(external_result, "status")
    action = _extract_safe_decision_value(external_result, "action")
    confidence_hint = _extract_safe_decision_value(external_result, "confidence_hint")
    safe_reason_code = _extract_safe_decision_value(external_result, "safe_reason_code")
    blocked_reason_code = _extract_safe_decision_value(external_result, "blocked_reason_code")
    needs_more_information_reason = _extract_safe_decision_value(
        external_result,
        "needs_more_information_reason",
    )

    if not safe_reason_code:
        if status == "blocked":
            safe_reason_code = blocked_reason_code or "policy_block"
        elif status == "needs_more_information":
            safe_reason_code = needs_more_information_reason or "needs_more_information"
        else:
            safe_reason_code = "advisory_ready"

    return {
        "status": status,
        "action": action,
        "selected_chunk_ids": [item.chunk_id for item in getattr(request, "candidates", [])],
        "safe_reason_code": safe_reason_code,
        "needs_more_information_reason": needs_more_information_reason,
        "blocked_reason_code": blocked_reason_code,
        "confidence_hint": confidence_hint or "unknown",
        "task_type": _sanitize_text(preview.get("task_type")),
    }


def _classify_failure(exc: Exception) -> str:
    message = _sanitize_text(exc).lower()
    if "adapter" in message:
        return "adapter_contract_issue"
    if "policy" in message or "security" in message:
        return "policy_security_block"
    if "platform" in message or "semantic" in message:
        return "platform_semantic_gap"
    if "dependency" in message or "install" in message or "module" in message:
        return "private_dependency_install_issue"
    if "forbidden" in message:
        return "forbidden_output_issue"
    return "local_validation_issue"


def _build_compact_summary(
    *,
    label: str,
    decide_result: Any,
    external_result: Any,
    artifact: Mapping[str, Any],
) -> str:
    status = _extract_safe_decision_value(decide_result, "status") or _extract_safe_decision_value(decide_result, "route")
    external_status = _extract_safe_decision_value(external_result, "status")
    external_action = _extract_safe_decision_value(external_result, "action")
    classification = artifact.get("classification", {})
    severity = _sanitize_text(classification.get("overall_severity"))
    hint = _sanitize_text(classification.get("go_no_go_hint"))
    category = _sanitize_text(classification.get("failure_category"))

    parts = [
        f"fixture={label}",
        f"decide={status or 'unknown'}",
        f"external={external_status or 'unknown'}",
    ]
    if external_action:
        parts.append(f"action={external_action}")
    if severity:
        parts.append(f"diff_severity={severity}")
    if hint:
        parts.append(f"go_no_go={hint}")
    if category:
        parts.append(f"category={category}")
    return _sanitize_output_line(" ".join(parts))


def _emit_artifact_output(
    *,
    artifact: Mapping[str, Any],
    label: str,
    decide_result: Any,
    external_result: Any,
    json_mode: bool,
    stdout: TextIO | None,
) -> None:
    if json_mode:
        _print_line(json.dumps(artifact, separators=(",", ":"), sort_keys=True), stdout)
        return
    _print_line(
        _build_compact_summary(
            label=label,
            decide_result=decide_result,
            external_result=external_result,
            artifact=artifact,
        ),
        stdout,
    )


def main(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
) -> int:
    del argv

    if not _is_enabled(env):
        _print_line(
            "TopoCore v6 local validation skipped: set RB_TOPOCORE_V6_LOCAL_VALIDATE=1 to run.",
            stdout,
        )
        return 0

    json_mode = _json_mode(env)
    runtime_details = resolve_topocore_v6_runtime_mode(env)
    if _allow_decide_raw(env):
        _print_line(
            "Warning: raw decision validation is intentionally unsupported in this harness.",
            stdout,
        )

    try:
        module, _import_error = _load_topocore_v6_module(env)
    except TypeError:
        module, _import_error = _load_topocore_v6_module()
    if module is None:
        if runtime_details["disabled"]:
            _print_line(
                "TopoCore v6 local validation skipped: runtime mode disabled.",
                stdout,
            )
            return 0
        if _requires_local(env):
            _print_line(
                "TopoCore v6 local validation failed: private_dependency_install_issue.",
                stdout,
            )
            return 1
        _print_line(
            "TopoCore v6 local validation skipped: topocore_v6 is not available in the requested runtime mode.",
            stdout,
        )
        return 0

    try:
        create_topocore = getattr(module, "create_topocore")
        getattr(module, "EngineRequest")
        getattr(module, "EngineQuery")
        getattr(module, "EngineCandidate")
    except AttributeError:
        _print_line(
            "TopoCore v6 local validation failed: platform_semantic_gap.",
            stdout,
        )
        return 1

    try:
        core = create_topocore()
    except Exception:
        _print_line(
            "TopoCore v6 local validation failed: platform_semantic_gap.",
            stdout,
        )
        return 1

    adapter = RepoBrainTopoCoreV6Adapter()
    if not json_mode:
        _print_line("TopoCore v6 local validation starting.", stdout)
        _print_line(
            _sanitize_output_line(
                " ".join(
                    [
                        f"runtime_mode_requested={runtime_details['requested_mode']}",
                        f"local_path_configured={'yes' if runtime_details['local_path_configured'] else 'no'}",
                        f"local_path_kind={runtime_details['local_path_kind']}",
                    ]
                )
            ),
            stdout,
        )

    for fixture in _build_fixture_definitions():
        label = fixture["label"]
        bundle = fixture["bundle"]
        v5_snapshot = fixture["v5_snapshot"]
        try:
            preview = adapter.build_request_preview(bundle).to_dict()
            request_bundle = adapter.build_real_engine_request(
                bundle,
                topocore_public_api=module,
            )
            request = request_bundle.engine_request
            decide_result = core.decide(request)
            external_result = core.decide_external(request)
            v6_snapshot = _build_v6_advisory_snapshot(
                request=request,
                preview=preview,
                external_result=external_result,
            )
            diff_report = build_decision_diff_report(
                v5_snapshot=v5_snapshot,
                v6_advisory_snapshot=v6_snapshot,
            )
            artifact = build_advisory_artifact(
                v5_primary_snapshot=v5_snapshot,
                v6_advisory_snapshot=v6_snapshot,
                decision_diff=diff_report,
                metadata={
                    "mode": "manual_local",
                    "command": _sanitize_text(v5_snapshot.get("command")) or "unknown",
                    "fixture_name": label,
                    "validation_run_label": "manual_local_validation",
                },
            ).to_dict()
        except Exception as exc:
            category = _classify_failure(exc)
            _print_line(
                _sanitize_output_line(f"fixture={label} result=failed category={category}"),
                stdout,
            )
            return 1

        _emit_artifact_output(
            artifact=artifact,
            label=label,
            decide_result=decide_result,
            external_result=external_result,
            json_mode=json_mode,
            stdout=stdout,
        )

    if not json_mode:
        _print_line("TopoCore v6 local validation passed.", stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
