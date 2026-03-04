from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.tkya.engine import OriginalEngineAdapter, get_engine
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


def test_default_backend_is_lite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_ORIGINAL_PATH", raising=False)
    monkeypatch.delenv("RB_TKYA_STRICT_ORIGINAL", raising=False)
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_original_backend_loads_via_importlib_when_file_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module_path = tmp_path / "TopoCore_TCX_v2-CAS.py"
    module_path.write_text(
        "\n".join(
            [
                "class TopoCoreResponse:",
                "    def __init__(self, summary='', answer='') -> None:",
                "        self.summary = summary",
                "        self.answer = answer",
                "        self.next_steps = []",
                "        self.risks = []",
                "",
                "class TopoCoreTCXv2CAS:",
                "    def handle_request(self, user_text, **kwargs):",
                "        return TopoCoreResponse(summary='narrow retrieval', answer='ok')",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("RB_TKYA_BACKEND", "original")
    monkeypatch.setenv("RB_TKYA_STRICT_ORIGINAL", "1")
    monkeypatch.setenv("RB_TKYA_ORIGINAL_PATH", str(module_path))
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    assert isinstance(engine, OriginalEngineAdapter)
    decision = engine.decide(_sample_request())
    assert decision.selected_chunk_ids


def test_original_backend_missing_file_fallbacks_to_lite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v2-CAS.py"
    monkeypatch.setenv("RB_TKYA_BACKEND", "original")
    monkeypatch.setenv("RB_TKYA_STRICT_ORIGINAL", "0")
    monkeypatch.setenv("RB_TKYA_ORIGINAL_PATH", str(missing_path))

    engine = get_engine()
    assert isinstance(engine, TopoCoreLite)


def test_original_backend_missing_file_strict_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    missing_path = tmp_path / "missing" / "TopoCore_TCX_v2-CAS.py"
    monkeypatch.setenv("RB_TKYA_BACKEND", "original")
    monkeypatch.setenv("RB_TKYA_STRICT_ORIGINAL", "1")
    monkeypatch.setenv("RB_TKYA_ORIGINAL_PATH", str(missing_path))

    with pytest.raises(RuntimeError):
        get_engine()


def test_remote_disabled_by_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    marker_path = tmp_path / "remote-called.txt"
    module_path = tmp_path / "TopoCore_TCX_v2-CAS.py"
    module_path.write_text(
        "\n".join(
            [
                f"MARKER = {repr(marker_path.as_posix())}",
                "",
                "class TopoCoreResponse:",
                "    def __init__(self, summary='', answer='') -> None:",
                "        self.summary = summary",
                "        self.answer = answer",
                "        self.next_steps = []",
                "        self.risks = []",
                "",
                "class TopoCoreTCXv2CAS:",
                "    def remote_call(self):",
                "        with open(MARKER, 'w', encoding='utf-8') as f:",
                "            f.write('1')",
                "        return 'ok'",
                "",
                "    def handle_request(self, user_text, **kwargs):",
                "        self.remote_call()",
                "        return TopoCoreResponse(summary='expand search', answer='ok')",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("RB_TKYA_BACKEND", "original")
    monkeypatch.setenv("RB_TKYA_STRICT_ORIGINAL", "1")
    monkeypatch.setenv("RB_TKYA_ORIGINAL_PATH", str(module_path))
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    engine = get_engine()
    decision = engine.decide(_sample_request())

    assert decision.route in {"FAST", "DEEP"}
    assert not marker_path.exists()
