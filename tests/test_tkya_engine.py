from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.tkya.engine import get_engine
from repobrain.topocore_lite import TopoCoreLite
from repobrain.tky_engine import EngineCandidate, EngineQuery, EngineRequest


def _sample_request() -> EngineRequest:
    return EngineRequest(
        task_type="ask",
        query=EngineQuery(text="where is provider logic", signature=[1, 2, 3]),
        candidates=[
            EngineCandidate(
                chunk_id="c1",
                score_local=0.22,
                signature=[1, 2],
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=20,
            ),
            EngineCandidate(
                chunk_id="c2",
                score_local=0.04,
                signature=[3, 4],
                file_path="repobrain/ask.py",
                line_start=1,
                line_end=40,
            ),
        ],
        limits={"max_sources": 6, "min_score_keep": 0.02},
        policy={"corelocked": True},
    )


def _write_v5_stub_module(path: Path, *, call_remote: bool = False) -> None:
    remote_block = (
        "\n".join(
            [
                f"MARKER = {repr((path.parent / 'remote-called.txt').as_posix())}",
                "",
                "def _write_marker():",
                "    with open(MARKER, 'w', encoding='utf-8') as f:",
                "        f.write('1')",
                "",
                "def _remote_call():",
                "    _write_marker()",
                "",
            ]
        )
        if call_remote
        else ""
    )
    decide_body = (
        "\n".join(
            [
                "        try:",
                "            self.remote_call()",
                "        except Exception:",
                "            pass",
            ]
        )
        if call_remote
        else ""
    )
    remote_method = (
        "\n".join(
            [
                "",
                "    def remote_call(self):",
                "        _remote_call()",
                "        return 'ok'",
            ]
        )
        if call_remote
        else ""
    )

    path.write_text(
        "\n".join(
            [
                "from repobrain.tky_engine import EngineDecision, EngineSecurity",
                "",
                remote_block,
                "class TopoCoreTCXv5AdvanceCASGit:",
                "    def decide(self, req):",
                decide_body,
                "        return EngineDecision(",
                "            route='FAST',",
                "            selected_chunk_ids=['c1'],",
                "            compression_stats={'retrieved': len(req.candidates), 'selected': 1},",
                "            security=EngineSecurity(",
                "                blocked=False,",
                "                injection_risk='low',",
                "                exfiltration_risk='low',",
                "                signals=[],",
                "            ),",
                "            rationale='ok',",
                "            stable_tokens=['s1'],",
                "        )",
                remote_method,
            ]
        ),
        encoding="utf-8",
    )


def test_explicit_lite_backend_is_lite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "lite")
    monkeypatch.delenv("RB_TKYA_V5_PATH", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT_V5", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT", raising=False)
    monkeypatch.delenv("RB_TKYA_V5_CANARY_PERCENT", raising=False)
    monkeypatch.delenv("RB_TKYA_CANARY_KEY", raising=False)
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_default_backend_prefers_v5_when_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    _write_v5_stub_module(module_path, call_remote=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(module_path))
    monkeypatch.delenv("RB_TKYA_STRICT", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT_V5", raising=False)
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    decision = engine.decide(_sample_request())
    assert decision.route == "FAST"


def test_default_backend_falls_back_to_lite_when_v5_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(missing_path))
    monkeypatch.delenv("RB_TKYA_STRICT", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT_V5", raising=False)

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_v5_backend_loads_via_importlib_when_file_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    _write_v5_stub_module(module_path, call_remote=False)

    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "1")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(module_path))
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    decision = engine.decide(_sample_request())
    assert decision.route == "FAST"
    assert decision.selected_chunk_ids == ["c1"]


def test_v5_backend_missing_file_fallbacks_to_lite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "0")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(missing_path))

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_v5_backend_missing_file_strict_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "1")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(missing_path))

    with pytest.raises(RuntimeError):
        get_engine()


def test_v5_backend_missing_file_common_strict_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT", "1")
    monkeypatch.delenv("RB_TKYA_STRICT_V5", raising=False)
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(missing_path))

    with pytest.raises(RuntimeError):
        get_engine()


def test_unsupported_backend_value_falls_back_to_lite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TKYA_BACKEND", "legacy")
    monkeypatch.delenv("RB_TKYA_V5_PATH", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT_V5", raising=False)

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_remote_disabled_by_default_for_v5(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    marker_path = tmp_path / "remote-called.txt"
    _write_v5_stub_module(module_path, call_remote=True)

    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "1")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(module_path))
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    decision = engine.decide(_sample_request())

    assert decision.route == "FAST"
    assert not marker_path.exists()


def test_v5_canary_percent_zero_falls_back_to_lite(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    _write_v5_stub_module(module_path, call_remote=False)

    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "1")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(module_path))
    monkeypatch.setenv("RB_TKYA_V5_CANARY_PERCENT", "0")
    monkeypatch.setenv("RB_TKYA_CANARY_KEY", "stable-key")

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_v5_canary_percent_hundred_uses_v5(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v5-Advance_CAS+Git.py"
    _write_v5_stub_module(module_path, call_remote=False)

    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TKYA_STRICT_V5", "1")
    monkeypatch.setenv("RB_TKYA_V5_PATH", str(module_path))
    monkeypatch.setenv("RB_TKYA_V5_CANARY_PERCENT", "100")
    monkeypatch.setenv("RB_TKYA_CANARY_KEY", "stable-key")

    engine = get_engine()
    decision = engine.decide(_sample_request())
    assert decision.route == "FAST"
