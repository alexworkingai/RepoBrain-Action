from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from repobrain.tky_engine import EngineCandidate, EngineQuery, EngineRequest


def _load_v4_module():
    path = Path("repobrain/tkya/vendor/TopoCore_TCX_v4-CAS+Git.py").resolve()
    spec = importlib.util.spec_from_file_location("repobrain_tkya_v4_vendor", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v4_decide_review_includes_verification_and_topology() -> None:
    module = _load_v4_module()
    core = module.TopoCoreTCXv4CASGit()
    req = EngineRequest(
        task_type="review",
        query=EngineQuery(text="review PR topology risks", signature=[1, 2]),
        candidates=[
            EngineCandidate(
                chunk_id="c1",
                score_local=0.7,
                signature=[11, 12],
                file_path="repobrain/github_flow.py",
                line_start=30,
                line_end=80,
            )
        ],
        limits={"max_sources": 3, "analytics_context": {"series": [1, 2, 3, 4]}},
        policy={"github_context": {"is_pr": True, "changed_files": ["repobrain/github_flow.py"]}},
    )
    decision = core.decide(req)
    assert decision.route == "REVIEW"
    assert decision.selected_chunk_ids
    assert isinstance(decision.compression_stats.get("verified"), list)
    assert isinstance(decision.compression_stats.get("not_run"), list)
    assert decision.compression_stats.get("topology_mode") in {"analytics", "generic"}


def test_v4_remote_is_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_v4_module()
    core = module.TopoCoreTCXv4CASGit()
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)
    with pytest.raises(RuntimeError):
        core.remote_call({"q": "x"})


def test_v4_topological_calculation_returns_summary() -> None:
    module = _load_v4_module()
    core = module.TopoCoreTCXv4CASGit()
    result = core.run_topological_calculation(
        {
            "series": [1, 2, 3, 5, 8, 13],
            "vectors": [[0, 0], [0.5, 0.5], [2.0, 2.0]],
        }
    )
    assert "series_summary" in result
    assert "graph_stats" in result
    assert "signature" in result
