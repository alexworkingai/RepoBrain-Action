from __future__ import annotations

import builtins
import importlib
import importlib.util
import json
from io import StringIO
from pathlib import Path

import pytest

from repobrain.topocore_v6_advisory_boundary import (
    TopoCoreV6AdvisoryBoundaryStatus,
    assert_advisory_boundary_result_safe,
    normalize_advisory_boundary_failure_category,
    run_disabled_advisory_boundary,
)
from repobrain.topocore_v6_shadow_path import TopoCoreV6ShadowResult, TopoCoreV6ShadowStatus

_ROOT = Path(__file__).resolve().parents[1]


def _load_manual_harness_module():
    script_path = _ROOT / "scripts" / "validate_topocore_v6_local.py"
    spec = importlib.util.spec_from_file_location("validate_topocore_v6_local_boundary_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_boundary_disabled_by_default_returns_noop() -> None:
    result = run_disabled_advisory_boundary(env={})
    payload = assert_advisory_boundary_result_safe(result)

    json.dumps(payload)
    assert payload["enabled"] is False
    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.DISABLED.value
    assert payload["boundary_mode"] == "still_disabled"
    assert payload["shadow_status"] == "disabled"
    assert payload["safety_flags"] == {
        "contains_raw_query": False,
        "contains_raw_code": False,
        "contains_decide_raw": False,
        "contains_secrets": False,
    }


def test_explicit_disabled_returns_noop() -> None:
    result = run_disabled_advisory_boundary(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "0"},
        input_value={"command": "ask", "task_type": "ask"},
    )
    payload = assert_advisory_boundary_result_safe(result)

    assert payload["enabled"] is False
    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.DISABLED.value
    assert payload["command"] == "ask"
    assert "artifact" not in payload["reason"] or "disabled" in payload["reason"]


def test_enabled_flag_remains_non_operational() -> None:
    result = run_disabled_advisory_boundary(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "review", "task_type": "review"},
    )
    payload = assert_advisory_boundary_result_safe(result)

    assert payload["enabled"] is True
    assert payload["status"] in {
        TopoCoreV6AdvisoryBoundaryStatus.ENABLED_NOT_IMPLEMENTED.value,
        TopoCoreV6AdvisoryBoundaryStatus.ADVISORY_BOUNDARY_NOOP.value,
    }
    assert payload["shadow_status"] == "enabled_not_implemented"


def test_artifact_flag_cannot_persist_or_publish(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_open(*args, **kwargs):
        raise AssertionError("disk write must not be attempted")

    monkeypatch.setattr(builtins, "open", _fail_open)
    result = run_disabled_advisory_boundary(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_ARTIFACTS": "1",
        },
        input_value={"command": "review", "task_type": "review"},
    )
    payload = assert_advisory_boundary_result_safe(result)
    serialized = json.dumps(payload)

    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.ADVISORY_BOUNDARY_NOOP.value
    assert payload["shadow_status"] == "artifact_unavailable"
    assert "publish" not in serialized
    assert "upload" not in serialized


def test_fail_closed_flag_does_not_change_live_behavior() -> None:
    result = run_disabled_advisory_boundary(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED": "1",
        },
        input_value={"command": "verify", "task_type": "verify"},
    )
    payload = assert_advisory_boundary_result_safe(result)

    assert payload["fail_closed"] is True
    assert payload["status"] in {
        TopoCoreV6AdvisoryBoundaryStatus.ENABLED_NOT_IMPLEMENTED.value,
        TopoCoreV6AdvisoryBoundaryStatus.ADVISORY_BOUNDARY_NOOP.value,
    }


def test_boundary_delegates_only_to_disabled_shadow_skeleton(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []

    def _fake_shadow(*, input_value=None, config=None, env=None):
        calls.append(
            {
                "input_value": input_value,
                "config": config,
                "env": env,
            }
        )
        return TopoCoreV6ShadowResult(
            enabled=True,
            status=TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED,
            reason="fake_shadow",
            command="ask",
            task_type="ask",
            artifacts_enabled=False,
            fail_closed=False,
            failure_category="enabled_not_implemented",
            safety_flags={
                "contains_raw_query": False,
                "contains_raw_code": False,
                "contains_decide_raw": False,
                "contains_secrets": False,
            },
            artifact_generated=False,
        )

    monkeypatch.setattr(
        "repobrain.topocore_v6_advisory_boundary.run_topocore_v6_shadow_path",
        _fake_shadow,
    )
    result = run_disabled_advisory_boundary(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={
            "command": "ask",
            "task_type": "ask",
            "safe_query_summary": "safe",
            "request_id_safe": "req-1",
        },
    )
    payload = assert_advisory_boundary_result_safe(result)

    assert calls
    delegated_input = calls[0]["input_value"]
    assert delegated_input is not None
    assert getattr(delegated_input, "command") == "ask"
    assert getattr(delegated_input, "task_type") == "ask"
    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.ENABLED_NOT_IMPLEMENTED.value


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
def test_forbidden_input_fields_are_rejected(field_name: str) -> None:
    result = run_disabled_advisory_boundary(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "ask", "task_type": "ask", field_name: "unsafe"},
    )
    payload = assert_advisory_boundary_result_safe(result)
    serialized = json.dumps(payload)

    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.INVALID_INPUT.value
    assert payload["failure_category"] == "invalid_input"
    if field_name not in {"raw_query", "raw_code", "secret", "decide_raw"}:
        assert field_name not in serialized


def test_nested_forbidden_fields_are_blocked() -> None:
    result = run_disabled_advisory_boundary(
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
    payload = assert_advisory_boundary_result_safe(result)

    assert payload["status"] == TopoCoreV6AdvisoryBoundaryStatus.INVALID_INPUT.value
    assert '"raw_code": "unsafe"' not in json.dumps(payload)


def test_failure_categories_are_sanitized() -> None:
    assert normalize_advisory_boundary_failure_category("disabled") == "disabled"
    assert (
        normalize_advisory_boundary_failure_category("advisory_boundary_noop")
        == "advisory_boundary_noop"
    )
    assert (
        normalize_advisory_boundary_failure_category("enabled_not_implemented")
        == "enabled_not_implemented"
    )
    assert normalize_advisory_boundary_failure_category("invalid_input") == "invalid_input"
    assert (
        normalize_advisory_boundary_failure_category("forbidden_output_issue")
        == "forbidden_output_issue"
    )
    assert (
        normalize_advisory_boundary_failure_category("shadow_path_unavailable")
        == "shadow_path_unavailable"
    )
    assert normalize_advisory_boundary_failure_category("raw traceback blob") == "configuration_error"


def test_fix_command_remains_conservative() -> None:
    result = run_disabled_advisory_boundary(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={
            "command": "fix",
            "task_type": "fix",
            "v5_primary_snapshot": {
                "safe_reason_code": "no_patch",
                "no_patch_reason": "insufficient localized evidence",
            },
        },
    )
    payload = assert_advisory_boundary_result_safe(result)
    serialized = json.dumps(payload)

    assert payload["status"] in {
        TopoCoreV6AdvisoryBoundaryStatus.ENABLED_NOT_IMPLEMENTED.value,
        TopoCoreV6AdvisoryBoundaryStatus.ADVISORY_BOUNDARY_NOOP.value,
        TopoCoreV6AdvisoryBoundaryStatus.DISABLED.value,
    }
    assert "apply_patch" not in serialized
    assert "commit" not in serialized
    assert "branch" not in serialized
    assert "create_pr" not in serialized


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
        assert "topocore_v6_advisory_boundary" not in text
        assert "run_disabled_advisory_boundary" not in text


def test_no_topocore_v6_dependency_required() -> None:
    for module_name in (
        "repobrain.topocore_v6_advisory_boundary",
        "repobrain.topocore_v6_shadow_path",
        "repobrain.topocore_v6_adapter",
        "repobrain.topocore_v6_decision_diff",
        "repobrain.topocore_v6_advisory_artifact",
    ):
        module = importlib.import_module(module_name)
        assert module is not None


def test_existing_shadow_skeleton_tests_remain_valid() -> None:
    shadow_module = importlib.import_module("repobrain.topocore_v6_shadow_path")
    assert hasattr(shadow_module, "run_topocore_v6_shadow_path")
    assert hasattr(shadow_module, "assert_shadow_result_safe")


def test_manual_local_harness_remains_unchanged() -> None:
    module = _load_manual_harness_module()
    buffer = StringIO()
    code = module.main(env={}, stdout=buffer)

    assert code == 0
    assert (
        buffer.getvalue().strip()
        == "TopoCore v6 local validation skipped: set RB_TOPOCORE_V6_LOCAL_VALIDATE=1 to run."
    )
