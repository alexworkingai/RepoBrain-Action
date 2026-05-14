from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

from repobrain.topocore_v6_shadow_path import (
    TopoCoreV6ShadowStatus,
    load_shadow_config_from_env,
    run_topocore_v6_shadow_path,
)

_ROOT = Path(__file__).resolve().parents[1]


def test_disabled_by_default_returns_noop() -> None:
    result = run_topocore_v6_shadow_path(env={})
    payload = result.to_dict()

    json.dumps(payload)
    assert payload["enabled"] is False
    assert payload["status"] == TopoCoreV6ShadowStatus.DISABLED.value
    assert payload["artifact_generated"] is False
    assert "raw_query" not in payload


def test_explicit_disabled_flag_returns_noop() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "0"},
        input_value={"command": "ask", "task_type": "ask"},
    )

    payload = result.to_dict()
    assert payload["enabled"] is False
    assert payload["status"] == "disabled"
    assert payload["command"] == "ask"


def test_enabled_flag_does_not_call_v6() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "review", "task_type": "review"},
    )

    payload = result.to_dict()
    assert payload["enabled"] is True
    assert payload["status"] == TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED.value
    assert payload["failure_category"] == "enabled_not_implemented"


def test_artifact_flag_is_safe() -> None:
    result = run_topocore_v6_shadow_path(
        env={
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_ARTIFACTS": "1",
        },
        input_value={"command": "review", "task_type": "review"},
    )

    payload = result.to_dict()
    json.dumps(payload)
    assert payload["status"] == TopoCoreV6ShadowStatus.ARTIFACT_UNAVAILABLE.value
    assert payload["artifact_generated"] is False
    assert "publish" not in json.dumps(payload)


def test_fail_closed_flag_recorded_but_safe() -> None:
    config = load_shadow_config_from_env(
        {
            "RB_TOPOCORE_V6_SHADOW_ENABLED": "1",
            "RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED": "1",
        }
    )
    result = run_topocore_v6_shadow_path(
        config=config,
        input_value={"command": "verify", "task_type": "verify"},
    )

    payload = result.to_dict()
    assert payload["fail_closed"] is True
    assert payload["status"] == TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED.value


@pytest.mark.parametrize(
    "field_name",
    [
        "raw_query",
        "raw_code",
        "raw_diff",
        "prompt",
        "system_prompt",
        "secret",
        "token",
        "api_key",
        "private_key",
        "dotenv",
        "compression_stats",
        "trace",
        "decide_raw",
    ],
)
def test_forbidden_input_fields_are_rejected(field_name: str) -> None:
    payload = {
        "command": "ask",
        "task_type": "ask",
        field_name: "unsafe",
    }

    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value=payload,
    )

    result_payload = result.to_dict()
    serialized = json.dumps(result_payload)
    assert result.status == TopoCoreV6ShadowStatus.INVALID_INPUT
    if field_name not in {"raw_query", "raw_code", "secret", "decide_raw"}:
        assert field_name not in serialized
    assert "reason" in result_payload
    assert "failure_category" in result_payload


def test_safety_flags_remain_false() -> None:
    result = run_topocore_v6_shadow_path(
        env={"RB_TOPOCORE_V6_SHADOW_ENABLED": "1"},
        input_value={"command": "ask", "task_type": "ask"},
    )

    flags = result.to_dict()["safety_flags"]
    assert flags["contains_raw_query"] is False
    assert flags["contains_raw_code"] is False
    assert flags["contains_decide_raw"] is False
    assert flags["contains_secrets"] is False


def test_no_runtime_wiring_introduced() -> None:
    paths = [
        _ROOT / "repobrain" / "github_flow.py",
        _ROOT / "repobrain" / "tky_local.py",
        _ROOT / "repobrain" / "tky_engine.py",
        _ROOT / "repobrain" / "tkya" / "engine.py",
        _ROOT / "action.yml",
        _ROOT / ".github" / "workflows" / "repobrain.yml",
    ]

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "topocore_v6_shadow_path" not in text, path.as_posix()
        assert "run_topocore_v6_shadow_path" not in text, path.as_posix()


def test_no_topocore_v6_dependency_required() -> None:
    module = importlib.import_module("repobrain.topocore_v6_shadow_path")
    assert hasattr(module, "run_topocore_v6_shadow_path")


def test_disabled_default_harness_remains_unchanged() -> None:
    script_path = _ROOT / "scripts" / "validate_topocore_v6_local.py"
    spec = importlib.util.spec_from_file_location("validate_topocore_v6_local_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from io import StringIO

    buffer = StringIO()
    code = module.main(env={}, stdout=buffer)

    assert code == 0
    assert "TopoCore v6 local validation skipped" in buffer.getvalue()
