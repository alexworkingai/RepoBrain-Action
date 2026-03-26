from __future__ import annotations

from repobrain.review_delta_memory import compute_review_delta_and_store

# Validation PR for post-merge review delta acceptance check.

def _review_with_verdicts(items: list[tuple[str, list[str], str, str, str]]) -> dict[str, object]:
    verdicts = []
    for claim, anchors, confidence, impact, patchability in items:
        verdicts.append(
            {
                "claim": claim,
                "evidence_anchors": anchors,
                "confidence": confidence,
                "impact": impact,
                "patchability": patchability,
            }
        )
    return {"evidence_verdicts": verdicts, "confirmed_findings": [item[0] for item in items]}

# Repeated-run delta memory must stay deterministic for the same PR state.

def test_review_delta_memory_distinguishes_first_run_then_persisted_new_resolved(
    tmp_path,
) -> None:
    first = compute_review_delta_and_store(
        repo_root=tmp_path,
        pr_number=17,
        command="review",
        review=_review_with_verdicts(
            [("Merge conflict markers present", ["repobrain/github_flow.py"], "high", "high", "patchable")]
        ),
        head_sha="sha-1",
        run_id="1001",
        persist_state=True,
    )
    assert first["review_delta_memory_active"] is True
    assert first["review_delta_prior_state_available"] is False
    assert first["review_delta_status"] == "first_run"
    assert first["review_delta_new_count"] == 1
    assert first["review_delta_persisted_count"] == 0
    assert first["review_delta_resolved_count"] == 0

    second = compute_review_delta_and_store(
        repo_root=tmp_path,
        pr_number=17,
        command="review",
        review=_review_with_verdicts(
            [
                ("Merge conflict markers present", ["repobrain/github_flow.py"], "high", "high", "patchable"),
                ("Unchecked env var usage", ["repobrain/output_md.py"], "medium", "medium", "review_only"),
            ]
        ),
        head_sha="sha-2",
        run_id="1002",
        persist_state=True,
    )
    assert second["review_delta_prior_state_available"] is True
    assert second["review_delta_status"] == "prior_state_present"
    assert second["review_delta_new_count"] == 1
    assert second["review_delta_persisted_count"] == 1
    assert second["review_delta_resolved_count"] == 0

    third = compute_review_delta_and_store(
        repo_root=tmp_path,
        pr_number=17,
        command="review",
        review=_review_with_verdicts(
            [("Unchecked env var usage", ["repobrain/output_md.py"], "medium", "medium", "review_only")]
        ),
        head_sha="sha-3",
        run_id="1003",
        persist_state=True,
    )
    assert third["review_delta_prior_state_available"] is True
    assert third["review_delta_new_count"] == 0
    assert third["review_delta_persisted_count"] == 1
    assert third["review_delta_resolved_count"] == 1


def test_review_delta_memory_tracks_reclassified_when_identity_matches(tmp_path) -> None:
    compute_review_delta_and_store(
        repo_root=tmp_path,
        pr_number=17,
        command="review",
        review=_review_with_verdicts(
            [("Unchecked env var usage", ["repobrain/output_md.py"], "medium", "medium", "review_only")]
        ),
        head_sha="sha-1",
        run_id="2001",
        persist_state=True,
    )
    second = compute_review_delta_and_store(
        repo_root=tmp_path,
        pr_number=17,
        command="review",
        review=_review_with_verdicts(
            [("Unchecked env var usage", ["repobrain/output_md.py"], "high", "high", "blocked")]
        ),
        head_sha="sha-2",
        run_id="2002",
        persist_state=True,
    )
    assert second["review_delta_reclassified_count"] == 1
    assert second["review_delta_persisted_count"] == 0
