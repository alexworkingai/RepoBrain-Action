from __future__ import annotations

import sys
import types

import pytest

from repobrain.topocore_v6_adapter import inspect_topocore_v6_runtime_import


def _fake_topocore_module() -> types.ModuleType:
    module = types.ModuleType("topocore_v6")
    module.__version__ = "0.0.test"

    class EngineQuery:
        def __init__(self, *, text: str, signature: list[int] | None = None) -> None:
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class EngineRequest:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class ExternalDecisionView:
        pass

    class FakeFacade:
        audit_score_contract_version = "topocore.audit_score.v1"

        def health(self) -> dict[str, str]:
            return {"release_stage": "test", "api_stability": "foundation"}

        def decide_external(self, *_args: object, **_kwargs: object) -> dict[str, object]:
            return {"status": "pass"}

        def run_audit_score_v1(self, request: dict[str, object]) -> dict[str, object]:
            return {"contract_version": "topocore.audit_score.v1"}

    module.EngineQuery = EngineQuery
    module.EngineCandidate = EngineCandidate
    module.EngineRequest = EngineRequest
    module.ExternalDecisionView = ExternalDecisionView
    module.create_topocore = lambda: FakeFacade()
    return module


@pytest.fixture(autouse=True)
def _clean_topocore(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("RB_TOPOCORE_V6_RUNTIME_MODE", "RB_TOPOCORE_V6_LOCAL_PATH"):
        monkeypatch.delenv(name, raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def test_installed_package_mode_ignores_local_path_when_package_is_importable() -> None:
    sys.modules["topocore_v6"] = _fake_topocore_module()

    diagnostics = inspect_topocore_v6_runtime_import(
        local_path="D:/hidden/private/topocore/src",
        runtime_mode="installed_package",
    )

    assert diagnostics.ok is True
    assert diagnostics.used_mode == "installed_package"
    assert diagnostics.audit_score_v1_present is True
    assert "topocore_v6_import_failed" not in diagnostics.failure_category


def test_installed_package_mode_fails_safely_without_using_private_checkout_path() -> None:
    diagnostics = inspect_topocore_v6_runtime_import(
        local_path="D:/hidden/private/topocore/src",
        runtime_mode="installed_package",
    )

    assert diagnostics.ok is False
    assert diagnostics.requested_mode == "installed_package"
    assert diagnostics.used_mode == "not_available"
    assert diagnostics.failure_category in {
        "topocore_v6_import_failed",
        "topocore_v6_runtime_unknown",
    }
    assert "D:/hidden/private/topocore/src" not in diagnostics.error_message_sanitized
