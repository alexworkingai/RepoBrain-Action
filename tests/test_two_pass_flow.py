from types import SimpleNamespace

import repobrain.github_flow as github_flow
from repobrain.tky_provider import CandidateChunk, TKYResult


class FakeProvider:
    def __init__(self) -> None:
        self.calls = 0

    def compress_context(self, *, question: str, candidates: list[CandidateChunk], limits: dict) -> TKYResult:
        self.calls += 1
        if self.calls == 1:
            return TKYResult(
                selected_chunk_ids=[candidates[0].chunk_id],
                route="DEEP",
                compression_stats={"retrieved": len(candidates), "selected": 1},
                rationale="pass1 deep",
            )
        return TKYResult(
            selected_chunk_ids=[candidates[-1].chunk_id],
            route="FAST",
            compression_stats={"retrieved": len(candidates), "selected": 1},
            rationale="pass2 fast",
        )


def test_two_pass_flow_uses_second_pass_selection(monkeypatch) -> None:
    pass1 = [
        CandidateChunk("c1", "repobrain/a.py", 1, 10, 0.12),
        CandidateChunk("c2", "repobrain/b.py", 1, 10, 0.02),
    ]
    pass2 = [
        CandidateChunk("c1", "repobrain/a.py", 1, 10, 0.12),
        CandidateChunk("c3", "repobrain/c.py", 1, 10, 0.08),
    ]
    calls = {"n": 0}

    def fake_retrieve_topk(question: str, chunks: list[CandidateChunk], topk: int) -> list[CandidateChunk]:
        calls["n"] += 1
        return pass1 if calls["n"] == 1 else pass2

    monkeypatch.setattr(github_flow, "retrieve_topk", fake_retrieve_topk)
    provider = FakeProvider()
    cfg = SimpleNamespace(
        topk_fast=30,
        topk_deep=80,
        min_score_fast=0.05,
        min_score_keep=0.02,
        max_sources_fast=6,
        max_sources_deep=12,
        max_sources=8,
        topk=30,
    )

    result, audit = github_flow.run_qa_two_pass(
        question="Where is TKYProvider?",
        cmd="ask",
        chunks=[],
        provider=provider,
        cfg=cfg,
        tky_mode_requested="baseline",
    )

    assert provider.calls == 2
    assert result.tky.selected_chunk_ids == ["c3"]
    assert result.evidence
    assert result.evidence[0].file_path == "repobrain/c.py"
    assert audit["pass_count"] == 2
    assert audit["route_final"] == "FAST"
    assert "pass2.top_score" in audit
