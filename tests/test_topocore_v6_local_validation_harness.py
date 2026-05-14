from __future__ import annotations

import importlib.util
import json
from io import StringIO
from pathlib import Path
import sys
import types

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _ROOT / "scripts" / "validate_topocore_v6_local.py"
_SPEC = importlib.util.spec_from_file_location(
    "validate_topocore_v6_local_test_module",
    _SCRIPT_PATH,
)
assert _SPEC is not None
assert _SPEC.loader is not None
validate_topocore_v6_local = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validate_topocore_v6_local)


def _run_main(env: dict[str, str]) -> tuple[int, str]:
    buffer = StringIO()
    code = validate_topocore_v6_local.main(env=env, stdout=buffer)
    return code, buffer.getvalue()


def _build_fake_topocore_v6_module() -> types.ModuleType:
    class FakeEngineQuery:
        def __init__(self, *, text: str, task_type: str) -> None:
            self.text = text
            self.task_type = task_type

    class FakeEngineCandidate:
        def __init__(self, *, chunk_id: str, score_local: float, metadata: dict[str, object]) -> None:
            self.chunk_id = chunk_id
            self.score_local = score_local
            self.metadata = metadata

    class FakeEngineRequest:
        def __init__(
            self,
            *,
            query: FakeEngineQuery,
            candidates: list[FakeEngineCandidate],
            limits: dict[str, object],
            policy: dict[str, object],
        ) -> None:
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

    class FakeCore:
        @property
        def decide_raw(self) -> object:
            raise AssertionError("raw decision access should never be attempted")

        def decide(self, request: FakeEngineRequest) -> dict[str, str]:
            task_type = request.query.task_type
            if task_type == "fix":
                return {"status": "ready", "route": "proceed"}
            if "missing context" in request.query.text.lower():
                return {"status": "wait", "route": "needs_more_information"}
            if "blocked safety" in request.query.text.lower():
                return {"status": "blocked", "route": "blocked"}
            return {"status": "ready", "route": "proceed"}

        def decide_external(self, request: FakeEngineRequest) -> dict[str, str]:
            task_type = request.query.task_type
            if task_type == "fix":
                return {
                    "status": "ready",
                    "action": "proceed",
                    "safe_reason_code": "fix_ready",
                    "confidence_hint": "medium",
                }
            if "missing context" in request.query.text.lower():
                return {
                    "status": "needs_more_information",
                    "action": "investigate",
                    "needs_more_information_reason": "missing_context",
                    "confidence_hint": "low",
                }
            if "blocked safety" in request.query.text.lower():
                return {
                    "status": "blocked",
                    "action": "manual_only",
                    "blocked_reason_code": "policy_block",
                    "confidence_hint": "high",
                }
            return {
                "status": "ready",
                "action": "respond",
                "safe_reason_code": "ready",
                "confidence_hint": "medium",
            }

    fake_module = types.ModuleType("topocore_v6")
    fake_module.EngineQuery = FakeEngineQuery
    fake_module.EngineCandidate = FakeEngineCandidate
    fake_module.EngineRequest = FakeEngineRequest
    fake_module.create_topocore = lambda: FakeCore()
    return fake_module


def test_disabled_default_behavior_remains_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_VALIDATE", raising=False)
    sys.modules.pop("topocore_v6", None)

    code, output = _run_main({})

    assert code == 0
    assert "TopoCore v6 local validation skipped" in output
    assert "RB_TOPOCORE_V6_LOCAL_VALIDATE=1" in output
    assert "schema_version" not in output
    assert "go_no_go" not in output
    assert "topocore_v6" not in sys.modules


def test_fake_topocore_v6_produces_decision_diff_artifacts_in_manual_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "topocore_v6", _build_fake_topocore_v6_module())

    code, output = _run_main({"RB_TOPOCORE_V6_LOCAL_VALIDATE": "1"})

    assert code == 0
    assert "TopoCore v6 local validation starting." in output
    assert "fixture=minimal_ask" in output
    assert "diff_severity=" in output
    assert "go_no_go=" in output
    for forbidden in (
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
    ):
        assert forbidden not in output


def test_optional_json_artifact_mode_emits_sanitized_json_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "topocore_v6", _build_fake_topocore_v6_module())

    code, output = _run_main(
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON": "1",
        }
    )

    assert code == 0
    lines = [line for line in output.splitlines() if line.strip()]
    assert lines
    parsed = [json.loads(line) for line in lines]
    assert all(item["schema_version"] == "topocore-v6-advisory-artifact/v1" for item in parsed)
    assert all(item["artifact_kind"] == "topocore_v6_advisory" for item in parsed)
    for item in parsed:
        serialized = json.dumps(item)
        for forbidden in (
            "compression_stats",
            "raw_trace",
            "governance_internals",
            "event_internals",
            "artifact_internals",
            "raw_diff",
            "api_key",
            "private_key",
            "dotenv",
            ".env",
        ):
            assert forbidden not in serialized
        assert "raw_query" not in item["v5_primary_snapshot"]
        assert "raw_query" not in item["v6_advisory_snapshot"]
        assert "raw_query" not in item["decision_diff"]
        assert "raw_code" not in item["v5_primary_snapshot"]
        assert "raw_code" not in item["v6_advisory_snapshot"]
        assert "raw_code" not in item["decision_diff"]


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "topocore_v6", _build_fake_topocore_v6_module())

    code, output = _run_main(
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_ALLOW_DECIDE_RAW": "1",
        }
    )

    assert code == 0
    assert "raw decision validation is intentionally unsupported" in output
    assert "decide_raw" not in output


def test_fix_like_fixture_stays_conservative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "topocore_v6", _build_fake_topocore_v6_module())

    code, output = _run_main(
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON": "1",
        }
    )

    assert code == 0
    artifacts = [json.loads(line) for line in output.splitlines() if line.strip()]
    fix_artifact = next(item for item in artifacts if item.get("fixture_name") == "fix_like_governance")
    assert fix_artifact["command"] == "fix"
    assert fix_artifact["classification"]["go_no_go_hint"] != "go_candidate"
    serialized = json.dumps(fix_artifact)
    assert "apply_patch" not in serialized
    assert "commit" not in serialized
    assert "branch" not in serialized
    assert "create_pr" not in serialized


def test_forbidden_output_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "topocore_v6", _build_fake_topocore_v6_module())

    code, output = _run_main({"RB_TOPOCORE_V6_LOCAL_VALIDATE": "1"})

    assert code == 0
    for forbidden in (
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
    ):
        assert forbidden not in output


def test_missing_dependency_behavior_remains_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.modules.pop("topocore_v6", None)
    monkeypatch.setattr(
        validate_topocore_v6_local,
        "_load_topocore_v6_module",
        lambda: (None, ModuleNotFoundError("missing")),
    )

    code, output = _run_main(
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "0",
        }
    )

    assert code == 0
    assert "skipped" in output.lower()
    assert "topocore_v6 is not installed locally" in output


def test_missing_dependency_strict_mode_still_fails_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.modules.pop("topocore_v6", None)
    monkeypatch.setattr(
        validate_topocore_v6_local,
        "_load_topocore_v6_module",
        lambda: (None, ModuleNotFoundError("missing")),
    )

    code, output = _run_main(
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        }
    )

    assert code != 0
    assert "private_dependency_install_issue" in output


def test_no_runtime_wiring_introduced() -> None:
    target_paths = [
        _ROOT / "repobrain" / "github_flow.py",
        _ROOT / "repobrain" / "tky_local.py",
        _ROOT / "repobrain" / "tky_engine.py",
        _ROOT / "repobrain" / "tkya" / "engine.py",
        _ROOT / "action.yml",
        _ROOT / ".github" / "workflows" / "repobrain.yml",
    ]

    for path in target_paths:
        content = path.read_text(encoding="utf-8")
        assert "validate_topocore_v6_local" not in content, path.as_posix()
        assert "topocore_v6_advisory_artifact" not in content, path.as_posix()
        assert "RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON" not in content, path.as_posix()


def test_no_production_topocore_v6_import() -> None:
    target_paths = [
        _ROOT / "repobrain" / "topocore_v6_adapter.py",
        _ROOT / "repobrain" / "topocore_v6_decision_diff.py",
        _ROOT / "repobrain" / "topocore_v6_advisory_artifact.py",
        _ROOT / "repobrain" / "github_flow.py",
        _ROOT / "repobrain" / "tky_local.py",
        _ROOT / "repobrain" / "tky_engine.py",
        _ROOT / "repobrain" / "tkya" / "engine.py",
    ]

    for path in target_paths:
        content = path.read_text(encoding="utf-8")
        assert "import topocore_v6" not in content, path.as_posix()
        assert "from topocore_v6" not in content, path.as_posix()
