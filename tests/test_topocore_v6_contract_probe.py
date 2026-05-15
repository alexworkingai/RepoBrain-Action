from __future__ import annotations

import importlib
import importlib.util
import io
import sys
import types
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT_PATH = _ROOT / "scripts" / "probe_topocore_v6_contract.py"
_SPEC = importlib.util.spec_from_file_location("probe_topocore_v6_contract_test_module", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe_topocore_v6_contract = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(probe_topocore_v6_contract)


def _run_probe(env: dict[str, str]) -> tuple[int, str]:
    buffer = io.StringIO()
    code = probe_topocore_v6_contract.main(env=env, stdout=buffer)
    return code, buffer.getvalue().strip()


def _build_fake_topocore_v6_module(*, missing: set[str] | None = None, decide_raw_raises: bool = False) -> types.ModuleType:
    missing = missing or set()

    class EngineCandidate:
        def __init__(self, chunk_id: str, score_local: float, **kwargs: object) -> None:
            self.chunk_id = chunk_id
            self.score_local = score_local
            self.extra = kwargs

    class EngineQuery:
        def __init__(self, text: str, **kwargs: object) -> None:
            self.text = text
            self.extra = kwargs

    class EngineRequest:
        def __init__(self, task_type: str, query: EngineQuery, candidates: list[EngineCandidate], limits: dict, policy: dict) -> None:
            self.task_type = task_type
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

    class ExternalDecisionView:
        def __init__(self) -> None:
            self.status = "ready"
            self.action = "proceed"
            self.confidence_band = "high"
            self.message_code = "DECISION_READY"

    class FakeFacade:
        def health(self) -> dict[str, object]:
            return {
                "status": "ok",
                "version": "0.0.fake",
                "release_stage": "local-private-rc",
                "api_stability": "foundation",
            }

        def decide(self, request: EngineRequest) -> object:
            return {"status": "ok", "request_seen": bool(request.query.text)}

        def decide_external(self, request: EngineRequest) -> ExternalDecisionView:
            return ExternalDecisionView()

        def decide_raw(self, request: EngineRequest) -> object:
            if decide_raw_raises:
                raise AssertionError("decide_raw should not be called")
            return {"unsafe": True}

    fake_module = types.ModuleType("topocore_v6")
    fake_module.__version__ = "0.0.fake"
    fake_module.ExternalDecisionView = ExternalDecisionView

    if "create_topocore" not in missing:
        fake_module.create_topocore = lambda: FakeFacade()
    if "EngineRequest" not in missing:
        fake_module.EngineRequest = EngineRequest
    if "EngineQuery" not in missing:
        fake_module.EngineQuery = EngineQuery
    if "EngineCandidate" not in missing:
        fake_module.EngineCandidate = EngineCandidate

    return fake_module


@pytest.fixture(autouse=True)
def _clear_topocore_module() -> None:
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_disabled_by_default() -> None:
    code, output = _run_probe(env={})
    assert code == 0
    assert output == "TopoCore v6 contract probe skipped: set RB_TOPOCORE_V6_CONTRACT_PROBE=1 to run."
    assert "topocore_v6" not in sys.modules


def test_missing_dependency_non_strict() -> None:
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "0",
        }
    )
    assert code == 0
    assert "skipped" in output.lower()
    assert "error_category=private_dependency_import_unavailable" in output


def test_missing_dependency_strict() -> None:
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        }
    )
    assert code != 0
    assert "failed" in output.lower()
    assert "error_category=private_dependency_import_unavailable" in output
    assert ":" not in output.splitlines()[-1]
    assert "[redacted-path]" not in output or "path" in output


def test_fake_public_api_passes() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        }
    )
    assert code == 0
    assert "TopoCore v6 contract probe passed." in output
    assert "create_topocore" in output
    assert "decide_raw_used=no" in output
    assert "external_status=ready" in output


def test_fake_api_missing_symbols_is_reported() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(missing={"EngineCandidate"})
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        }
    )
    assert code != 0
    assert "missing_symbols=EngineCandidate" in output
    assert "error_category=public_api_symbol_missing" in output


def test_decide_raw_never_called() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
        }
    )
    assert code == 0
    assert "decide_raw_used=no" in output


def test_local_path_handling_is_sanitized() -> None:
    code, output = _run_probe(
        env={
            "RB_TOPOCORE_V6_CONTRACT_PROBE": "1",
            "RB_TOPOCORE_V6_REQUIRE_LOCAL": "1",
            "RB_TOPOCORE_V6_LOCAL_PATH": r"C:\Secret\Private\TopoCore",
        }
    )
    assert code == 2
    assert "configuration error" in output.lower()
    assert r"C:\Secret\Private\TopoCore" not in output


def test_no_runtime_wiring_introduced() -> None:
    for relative_path in (
        "repobrain/github_flow.py",
        "repobrain/tky_local.py",
        "repobrain/tky_engine.py",
        "repobrain/tkya/engine.py",
        "action.yml",
        ".github/workflows/repobrain.yml",
    ):
        text = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert "probe_topocore_v6_contract" not in text
        assert "RB_TOPOCORE_V6_CONTRACT_PROBE" not in text


def test_existing_manual_harness_remains_unchanged() -> None:
    script_path = _ROOT / "scripts" / "validate_topocore_v6_local.py"
    spec = importlib.util.spec_from_file_location("validate_topocore_v6_local_contract_probe_test", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    buffer = io.StringIO()
    code = module.main(env={}, stdout=buffer)
    assert code == 0
    assert (
        buffer.getvalue().strip()
        == "TopoCore v6 local validation skipped: set RB_TOPOCORE_V6_LOCAL_VALIDATE=1 to run."
    )
