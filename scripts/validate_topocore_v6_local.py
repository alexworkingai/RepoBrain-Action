from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)

_FORBIDDEN_OUTPUT_TOKENS = (
    "decide_raw",
    "compression_stats",
    "raw_trace",
    "governance_internals",
    "event_internals",
    "artifact_internals",
    "raw_query",
    "raw_code",
    "secret",
    "token",
    "api_key",
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


def _print_line(message: str, stdout: TextIO | None = None) -> None:
    stream = stdout if stdout is not None else sys.stdout
    stream.write(f"{message}\n")


def _load_topocore_v6_module() -> tuple[Any | None, Exception | None]:
    try:
        return importlib.import_module("topocore_v6"), None
    except Exception as exc:  # pragma: no cover - exercised through tests
        return None, exc


def _sanitize_text(value: Any) -> str:
    return str(value or "").strip()


def _sanitize_output_line(text: str) -> str:
    sanitized = " ".join(str(text or "").split())
    for token in _FORBIDDEN_OUTPUT_TOKENS:
        sanitized = sanitized.replace(token, "[redacted]")
    return sanitized


def _build_fixture_bundles() -> list[tuple[str, RepoBrainV6SummaryBundle]]:
    base_candidates = (
        RepoBrainV6CandidateRef(
            chunk_id="chunk-a",
            score_local=0.9,
            metadata={"path": "repobrain/review.py", "kind": "diff"},
        ),
    )
    return [
        (
            "minimal_ask",
            RepoBrainV6SummaryBundle(
                query="Summarize the current project state.",
                intent_summary={
                    "command": "ask",
                    "task_type_candidate": "ask",
                    "user_goal": "summarize current state",
                },
                candidates=base_candidates,
                evidence_summary={"confirmed_facts": ["one bounded candidate available"]},
            ),
        ),
        (
            "review_like",
            RepoBrainV6SummaryBundle(
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
        ),
        (
            "weak_context",
            RepoBrainV6SummaryBundle(
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
        ),
        (
            "blocked_safety",
            RepoBrainV6SummaryBundle(
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
        ),
        (
            "fix_like_governance",
            RepoBrainV6SummaryBundle(
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
        ),
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
        raise RuntimeError("TopoCore v6 platform issue: request compatibility mismatch.") from exc


def _extract_safe_decision_summary(label: str, decision: Any) -> str:
    if isinstance(decision, Mapping):
        status = _sanitize_text(decision.get("status"))
        action = _sanitize_text(decision.get("action"))
        route = _sanitize_text(decision.get("route"))
    else:
        status = _sanitize_text(getattr(decision, "status", ""))
        action = _sanitize_text(getattr(decision, "action", ""))
        route = _sanitize_text(getattr(decision, "route", ""))

    parts = [f"fixture={label}"]
    if status:
        parts.append(f"status={status}")
    if action:
        parts.append(f"action={action}")
    if route:
        parts.append(f"route={route}")
    return _sanitize_output_line(" ".join(parts))


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

    if _allow_decide_raw(env):
        _print_line(
            "Warning: RB_TOPOCORE_V6_ALLOW_DECIDE_RAW=1 is ignored. decide_raw validation is intentionally unsupported in this harness.",
            stdout,
        )

    module, import_error = _load_topocore_v6_module()
    if module is None:
        if _requires_local(env):
            _print_line(
                "TopoCore v6 local validation failed: private dependency/install issue.",
                stdout,
            )
            return 1
        _print_line(
            "TopoCore v6 local validation skipped: topocore_v6 is not installed locally.",
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
            "TopoCore v6 local validation failed: TopoCore v6 platform issue.",
            stdout,
        )
        return 1

    try:
        core = create_topocore()
    except Exception:
        _print_line(
            "TopoCore v6 local validation failed: TopoCore v6 platform issue.",
            stdout,
        )
        return 1

    adapter = RepoBrainTopoCoreV6Adapter()
    _print_line("TopoCore v6 local validation starting.", stdout)
    for label, bundle in _build_fixture_bundles():
        try:
            preview = adapter.build_request_preview(bundle).to_dict()
            request = _build_engine_objects(module, preview)
            decide_result = core.decide(request)
            external_result = core.decide_external(request)
        except Exception as exc:
            message = _sanitize_text(exc)
            if "policy" in message.lower() or "security" in message.lower():
                category = "policy/security block"
            elif "need" in message.lower() and "information" in message.lower():
                category = "insufficient GitHub data"
            else:
                category = "TopoCore v6 platform issue"
            _print_line(
                _sanitize_output_line(f"fixture={label} result=failed category={category}"),
                stdout,
            )
            return 1

        _print_line(_extract_safe_decision_summary(f"{label}:decide", decide_result), stdout)
        _print_line(
            _extract_safe_decision_summary(f"{label}:external", external_result),
            stdout,
        )

    _print_line("TopoCore v6 local validation passed.", stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
