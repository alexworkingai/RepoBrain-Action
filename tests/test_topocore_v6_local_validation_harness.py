from __future__ import annotations

import importlib.util
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


def _run_main(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> tuple[int, str]:
    buffer = StringIO()
    code = validate_topocore_v6_local.main(env=env, stdout=buffer)
    return code, buffer.getvalue()


def test_script_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_VALIDATE", raising=False)
    sys.modules.pop("topocore_v6", None)

    code, output = _run_main(monkeypatch, {})

    assert code == 0
    assert "TopoCore v6 local validation skipped" in output
    assert "RB_TOPOCORE_V6_LOCAL_VALIDATE=1" in output
    assert "topocore_v6" not in sys.modules


def test_missing_topocore_v6_is_skipped_when_require_flag_not_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.modules.pop("topocore_v6", None)
    monkeypatch.setattr(
        validate_topocore_v6_local,
        "_load_topocore_v6_module",
        lambda: (None, ModuleNotFoundError("missing")),
    )

    code, output = _run_main(
        monkeypatch,
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "0",
        },
    )

    assert code == 0
    assert "skipped" in output.lower()
    assert "topocore_v6 is not installed locally" in output


def test_missing_topocore_v6_fails_when_require_flag_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.modules.pop("topocore_v6", None)
    monkeypatch.setattr(
        validate_topocore_v6_local,
        "_load_topocore_v6_module",
        lambda: (None, ModuleNotFoundError("missing")),
    )

    code, output = _run_main(
        monkeypatch,
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        },
    )

    assert code != 0
    assert "private dependency/install issue" in output


def test_fake_topocore_v6_module_can_validate_harness_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
            raise AssertionError("decide_raw should not be accessed")

        def decide(self, request: FakeEngineRequest) -> dict[str, str]:
            assert request.query.task_type in {"ask", "review", "fix"}
            return {
                "status": "ready",
                "route": "proceed",
            }

        def decide_external(self, request: FakeEngineRequest) -> dict[str, str]:
            if request.query.task_type == "fix":
                return {"status": "blocked", "action": "manual_only"}
            if "missing" in request.query.text.lower():
                return {"status": "needs_more_information", "action": "investigate"}
            return {"status": "ready", "action": "respond"}

    fake_module = types.ModuleType("topocore_v6")
    fake_module.EngineQuery = FakeEngineQuery
    fake_module.EngineCandidate = FakeEngineCandidate
    fake_module.EngineRequest = FakeEngineRequest
    fake_module.create_topocore = lambda: FakeCore()

    monkeypatch.setitem(sys.modules, "topocore_v6", fake_module)

    code, output = _run_main(
        monkeypatch,
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        },
    )

    assert code == 0
    assert "TopoCore v6 local validation starting." in output
    assert "fixture=minimal_ask:decide status=ready route=proceed" in output
    assert "fixture=review_like:external status=ready action=respond" in output
    assert "fixture=fix_like_governance:external status=blocked action=manual_only" in output
    assert "TopoCore v6 local validation passed." in output


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
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
        def __init__(self, *, query: FakeEngineQuery, candidates: list[FakeEngineCandidate], limits: dict[str, object], policy: dict[str, object]) -> None:
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

    class FakeCore:
        @property
        def decide_raw(self) -> object:
            raise AssertionError("decide_raw should never be touched")

        def decide(self, request: FakeEngineRequest) -> dict[str, str]:
            return {"status": "ready", "route": "proceed"}

        def decide_external(self, request: FakeEngineRequest) -> dict[str, str]:
            return {"status": "ready", "action": "respond"}

    fake_module = types.ModuleType("topocore_v6")
    fake_module.EngineQuery = FakeEngineQuery
    fake_module.EngineCandidate = FakeEngineCandidate
    fake_module.EngineRequest = FakeEngineRequest
    fake_module.create_topocore = lambda: FakeCore()
    monkeypatch.setitem(sys.modules, "topocore_v6", fake_module)

    code, output = _run_main(
        monkeypatch,
        {
            "RB_TOPOCORE_V6_LOCAL_VALIDATE": "1",
            "RB_TOPOCORE_V6_ALLOW_DECIDE_RAW": "1",
        },
    )

    assert code == 0
    assert "decide_raw validation is intentionally unsupported" in output


def test_no_forbidden_output_fields(monkeypatch: pytest.MonkeyPatch) -> None:
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
        def __init__(self, *, query: FakeEngineQuery, candidates: list[FakeEngineCandidate], limits: dict[str, object], policy: dict[str, object]) -> None:
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

    class FakeCore:
        def decide(self, request: FakeEngineRequest) -> dict[str, str]:
            return {"status": "ready", "route": "proceed"}

        def decide_external(self, request: FakeEngineRequest) -> dict[str, str]:
            return {"status": "ready", "action": "respond"}

    fake_module = types.ModuleType("topocore_v6")
    fake_module.EngineQuery = FakeEngineQuery
    fake_module.EngineCandidate = FakeEngineCandidate
    fake_module.EngineRequest = FakeEngineRequest
    fake_module.create_topocore = lambda: FakeCore()
    monkeypatch.setitem(sys.modules, "topocore_v6", fake_module)

    code, output = _run_main(monkeypatch, {"RB_TOPOCORE_V6_LOCAL_VALIDATE": "1"})

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
        "secret",
        "token",
        "api_key",
    ):
        assert forbidden not in output


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
        assert "RB_TOPOCORE_V6_LOCAL_VALIDATE" not in content, path.as_posix()
        assert "topocore_v6 local validation" not in content.lower(), path.as_posix()


def test_no_production_topocore_v6_import() -> None:
    target_paths = [
        _ROOT / "repobrain" / "topocore_v6_adapter.py",
        _ROOT / "repobrain" / "github_flow.py",
        _ROOT / "repobrain" / "tky_local.py",
        _ROOT / "repobrain" / "tky_engine.py",
        _ROOT / "repobrain" / "tkya" / "engine.py",
    ]

    for path in target_paths:
        content = path.read_text(encoding="utf-8")
        assert "import topocore_v6" not in content, path.as_posix()
        assert "from topocore_v6" not in content, path.as_posix()

    assert "topocore_v6" not in validate_topocore_v6_local.__dict__
