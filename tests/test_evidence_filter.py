from __future__ import annotations

from repobrain.evidence_filter import filter_candidate_evidence
from repobrain.tky_provider import CandidateChunk


def _candidate(path: str, score: float, line_start: int = 1, line_end: int = 20) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"{path}:{line_start}-{line_end}",
        file_path=path,
        line_start=line_start,
        line_end=line_end,
        score=score,
        text=None,
    )


def test_filter_drops_duplicates_and_low_scores() -> None:
    candidates = [
        _candidate("repobrain/github_flow.py", 0.9, 10, 18),
        _candidate("repobrain/github_flow.py", 0.88, 11, 19),
        _candidate("repobrain/output_md.py", 0.12, 20, 28),
        _candidate("repobrain/review_validator.py", 0.08, 30, 40),
    ]

    result = filter_candidate_evidence(
        candidates,
        command="ask",
        query="where review validation happens",
    )

    assert result.filtered_count >= 1
    assert len(result.candidates) < len(candidates)
    assert "duplicate_region" in result.reason_codes or "low_score" in result.reason_codes


def test_filter_drops_docs_noise_for_fix_without_doc_request() -> None:
    candidates = [
        _candidate("docs/security.md", 0.8),
        _candidate("repobrain/github_flow.py", 0.82),
        _candidate("repobrain/patch_validator.py", 0.81),
    ]

    result = filter_candidate_evidence(
        candidates,
        command="fix",
        query="generate patch for patch validator",
    )

    kept_paths = {item.file_path for item in result.candidates}
    assert "docs/security.md" not in kept_paths
    assert "docs_noise" in result.reason_codes
