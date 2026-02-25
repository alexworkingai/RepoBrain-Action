from repobrain.ask import answer_question, make_provider
from repobrain.tky_baseline import BaselineTKYProvider
from repobrain.tky_provider import CandidateChunk


def test_make_provider_baseline() -> None:
    provider = make_provider("baseline")
    assert isinstance(provider, BaselineTKYProvider)


def test_answer_question_returns_evidence() -> None:
    provider = make_provider("baseline")
    candidates = [
        CandidateChunk(
            chunk_id="repobrain/tky_provider.py:1-10",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=10,
            score=0.9,
            text="class TKYProvider",
        ),
        CandidateChunk(
            chunk_id="repobrain/ask.py:1-10",
            file_path="repobrain/ask.py",
            line_start=1,
            line_end=10,
            score=0.1,
            text="def answer_question",
        ),
    ]

    result = answer_question(
        question="provider",
        candidates=candidates,
        provider=provider,
        limits={"max_sources": 1},
    )

    assert result.evidence
    assert result.evidence[0].file_path == "repobrain/tky_provider.py"
    assert result.audit_summary["retrieved"] == 2
    assert result.audit_summary["selected"] == 1
    assert result.next_steps == "Open evidence links and verify logic"
