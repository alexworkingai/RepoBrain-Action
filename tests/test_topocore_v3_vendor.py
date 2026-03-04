from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from repobrain.tky_engine import EngineCandidate, EngineQuery, EngineRequest


def _load_v3_module():
    path = Path("repobrain/tkya/vendor/TopoCore_TCX_v3-CAS_Git.py").resolve()
    spec = importlib.util.spec_from_file_location("repobrain_tkya_v3_vendor", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_v3_vendor_decide_contract_review() -> None:
    module = _load_v3_module()
    core = module.TopoCoreTCXv3CASGit()
    req = EngineRequest(
        task_type="review",
        query=EngineQuery(text="review PR risks", signature=[1, 2]),
        candidates=[
            EngineCandidate(
                chunk_id="c1",
                score_local=0.8,
                signature=[1],
                file_path="repobrain/github_flow.py",
                line_start=10,
                line_end=40,
            )
        ],
        limits={"max_sources": 3},
        policy={"github_context": {"is_pr": True, "changed_files": ["repobrain/github_flow.py"]}},
    )

    decision = core.decide(req)
    assert decision.route == "REVIEW"
    assert decision.selected_chunk_ids
    assert isinstance(decision.compression_stats.get("verified"), list)
    assert isinstance(decision.compression_stats.get("not_run"), list)
    assert decision.compression_stats.get("not_run")


def test_v3_vendor_remote_blocked_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_v3_module()
    core = module.TopoCoreTCXv3CASGit()
    monkeypatch.delenv("RB_TKYA_ALLOW_REMOTE", raising=False)

    with pytest.raises(RuntimeError):
        core.remote_call({"x": 1})
