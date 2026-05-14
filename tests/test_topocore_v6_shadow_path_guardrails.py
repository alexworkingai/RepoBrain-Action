from __future__ import annotations

import builtins
import importlib
import importlib.util
import json
from io import StringIO
from pathlib import Path

import pytest

from repobrain.topocore_v6_shadow_path import (
    TopoCoreV6ShadowError,
    TopoCoreV6ShadowStatus,
    assert_shadow_result_safe,
    normalize_shadow_failure_category,
    run_topocore_v6_shadow_path,
)

_ROOT = Path(__file__).resolve().parents[1]


def _load_manual_harness_module():
    script_path = _ROOT / "scripts" / "validate_topocore_v6_local.py"
    spec = importlib.util.spec_from_file_location("validate_topocore_v6_local_guard_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_noop_is_stable_and_product_safe() -> None:
    result = run_topocore_v6_shadow_path(env={})
    payload = assert_shadow_result_safe(result)

    assert payload["enabled"] is False
    assert payload["status"] == TopoCoreV6ShadowStatus.DISABLED.value
    assert payload["artifact_generated"] is False
    assert payload["safety_flags"] == {
        "contains_raw_query": False,
        "contains_raw_code": False,
        "contains_decide_raw": False,
        "contains_secrets": False,
    }
    json.dumps(payload)


def test_explicit_disabled_noop_overrides_artifact_flag() -> None:
    result = run_topocore_v6_shadow_path(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "0",
            "RB_TOPOCORE_V6_SHADOW_ARTIFACTS": "1",
        },
        input_value={"command": "review", "task_type": "review"},
    )
    payload = assert_shadow_result_safe(result)

    assert payload["enabled"] is False
    assert payload["status"] == TopoCoreV6ShadowStatus.DISABLED.value
    assert payload["artifact_generated"] is False
    assert "publish" not in json.dumps(payload)
    assert "persist" not in json.dumps(payload)


def test_enabled_skeleton_remains_non_operational() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "ask", "task_type": "ask"},
    )
    payload = assert_shadow_result_safe(result)

    assert payload["enabled"] is True
    assert payload["status"] == TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED.value
    assert payload["artifact_generated"] is False


def test_artifact_flag_cannot_publish_or_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_open(*args, **kwargs):
        raise AssertionError("disk write must not be attempted")

    monkeypatch.setattr(builtins, "open", _fail_open)

    result = run_topocore_v6_shadow_path(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_ARTIFACTS": "1",
        },
        input_value={"command": "review", "task_type": "review"},
    )
    payload = assert_shadow_result_safe(result)

    assert payload["status"] == TopoCoreV6ShadowStatus.ARTIFACT_UNAVAILABLE.value
    assert payload["artifact_generated"] is False
    assert "upload" not in json.dumps(payload)
    assert "publish" not in json.dumps(payload)


def test_fail_closed_flag_cannot_change_live_behavior_in_skeleton() -> None:
    result = run_topocore_v6_shadow_path(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED": "1",
        },
        input_value={"command": "verify", "task_type": "verify"},
    )
    payload = assert_shadow_result_safe(result)

    assert payload["fail_closed"] is True
    assert payload["status"] == TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED.value
    assert "blocked runtime" not in json.dumps(payload).lower()


@pytest.mark.parametrize(
    "field_name",
    [
        "raw_query",
        "raw_code",
        "raw_diff",
        "prompt",
        "system_prompt",
        "hidden_prompt",
        "secret",
        "token",
        "api_key",
        "password",
        "private_key",
        "env",
        "dotenv",
        ".env",
        "compression_stats",
        "trace",
        "raw_trace",
        "governance_internals",
        "event_internals",
        "artifact_internals",
        "decide_raw",
    ],
)
def test_forbidden_input_fields_are_rejected_consistently(field_name: str) -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "ask", "task_type": "ask", field_name: "unsafe"},
    )
    payload = assert_shadow_result_safe(result)

    assert payload["status"] == TopoCoreV6ShadowStatus.INVALID_INPUT.value
    assert payload["failure_category"] == "invalid_input"
    if field_name not in {"raw_query", "raw_code", "secret", "decide_raw"}:
        assert field_name not in json.dumps(payload)


def test_nested_forbidden_fields_are_blocked() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={
            "command": "review",
            "task_type": "review",
            "summary_bundle": {
                "safe": "ok",
                "items": [{"kind": "note"}, {"raw_code": "unsafe"}],
            },
        },
    )
    payload = assert_shadow_result_safe(result)

    assert payload["status"] == TopoCoreV6ShadowStatus.INVALID_INPUT.value
    serialized = json.dumps(payload)
    assert '"raw_code": "unsafe"' not in serialized


def test_forbidden_output_scan_catches_unsafe_result_like_structures() -> None:
    with pytest.raises(TopoCoreV6ShadowError):
        assert_shadow_result_safe(
            {
                "enabled": False,
                "status": "disabled",
                "reason": "noop",
                "command": "ask",
                "task_type": "ask",
                "artifacts_enabled": False,
                "fail_closed": False,
                "failure_category": "disabled",
                "artifact_generated": False,
                "safety_flags": {
                    "contains_raw_query": False,
                    "contains_raw_code": False,
                    "contains_decide_raw": False,
                    "contains_secrets": False,
                },
                "artifact_internals": {"unsafe": True},
            }
        )


def test_failure_categories_are_sanitized() -> None:
    assert normalize_shadow_failure_category("invalid_input") == "invalid_input"
    assert normalize_shadow_failure_category("artifact_unavailable") == "artifact_unavailable"
    assert normalize_shadow_failure_category("enabled_not_implemented") == "enabled_not_implemented"
    assert normalize_shadow_failure_category("forbidden_output_issue") == "forbidden_output_issue"
    assert normalize_shadow_failure_category("unexpected_stacktrace_blob") == "configuration_error"


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"RB_TOPOCORE_V6_SHADOW_ENABLED": "0"},
        {"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        {"RB_TOPOCORE_V6_SHADOW_ENABLED": "1", "RB_TOPOCORE_V6_SHADOW_ARTIFACTS": "1"},
        {"RB_TOPOCORE_V6_SHADOW_ENABLED": "1", "RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED": "1"},
    ],
)
def test_safety_flags_remain_false_across_modes(env: dict[str, str]) -> None:
    result = run_topocore_v6_shadow_path(env=env, input_value={"command": "ask", "task_type": "ask"})
    flags = result.to_dict()["safety_flags"]

    assert flags["contains_raw_query"] is False
    assert flags["contains_raw_code"] is False
    assert flags["contains_decide_raw"] is False
    assert flags["contains_secrets"] is False


def test_no_runtime_wiring_introduced() -> None:
    for rel_path in (
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
        "action.yml",
        ".github/workflows/repobrain.yml",
    ):
        text = (_ROOT / rel_path).read_text(encoding="utf-8")
        assert "topocore_v6_shadow_path" not in text
        assert "run_topocore_v6_shadow_path" not in text


def test_no_topocore_v6_dependency_required() -> None:
    for module_name in (
        "repobrain.topocore_v6_shadow_path",
        "repobrain.topocore_v6_adapter",
        "repobrain.topocore_v6_decision_diff",
        "repobrain.topocore_v6_advisory_artifact",
    ):
        module = importlib.import_module(module_name)
        assert module is not None


def test_manual_local_harness_remains_unchanged() -> None:
    module = _load_manual_harness_module()
    buffer = StringIO()
    code = module.main(env={}, stdout=buffer)

    assert code == 0
    assert (
        buffer.getvalue().strip()
        == "TopoCore v6 local validation skipped: set RB_TOPOCORE_V6_LOCAL_VALIDATE=1 to run."
    )


def test_fix_command_remains_conservative() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={
            "command": "fix",
            "task_type": "fix",
            "v5_primary_snapshot": {"safe_reason_code": "no_patch", "no_patch_reason": "insufficient localized evidence"},
        },
    )
    payload = assert_shadow_result_safe(result)
    serialized = json.dumps(payload)

    assert payload["status"] in {
        TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED.value,
        TopoCoreV6ShadowStatus.ARTIFACT_UNAVAILABLE.value,
        TopoCoreV6ShadowStatus.DISABLED.value,
    }
    assert "apply_patch" not in serialized
    assert "commit" not in serialized
    assert "branch" not in serialized
    assert "create_pr" not in serialized


def test_json_serialization_is_stable() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "review", "task_type": "review"},
    )
    payload = result.to_dict()
    round_trip = json.loads(json.dumps(payload))

    assert round_trip["status"] == payload["status"]
    assert round_trip["failure_category"] == payload["failure_category"]
