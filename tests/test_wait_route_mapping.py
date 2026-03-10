from types import SimpleNamespace

import repobrain.github_flow as github_flow
from repobrain.tky_provider import CandidateChunk, TKYResult


class WaitProvider:
    def __init__(self) -> None:
        self.calls = 0

    def compress_context(self, *, question: str, candidates: list[CandidateChunk], limits: dict) -> TKYResult:
        self.calls += 1
        return TKYResult(
            selected_chunk_ids=[],
            route="WAIT",
            compression_stats={"retrieved": len(candidates), "selected": 0},
            rationale="verification pending",
        )


def test_wait_route_does_not_trigger_second_pass(monkeypatch) -> None:
    retrieve_calls = {"n": 0}

    def fake_retrieve_topk(question: str, chunks: list[CandidateChunk], topk: int) -> list[CandidateChunk]:
        retrieve_calls["n"] += 1
        return [CandidateChunk("c1", "repobrain/a.py", 1, 10, 0.12)]

    monkeypatch.setattr(github_flow, "retrieve_topk", fake_retrieve_topk)
    provider = WaitProvider()
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
        question="needs verification",
        cmd="ask",
        chunks=[],
        provider=provider,
        cfg=cfg,
        tky_mode_requested="baseline",
    )

    assert provider.calls == 1
    assert retrieve_calls["n"] == 1
    assert result.tky.route == "WAIT"
    assert "Verification is pending" in result.answer_text
    assert audit["pass_count"] == 1
    assert audit["route_final"] == "WAIT"
