from __future__ import annotations

from repobrain.github_flow import (
    _count_confirmed_localized_findings,
    _should_block_fix_patch_without_localized_evidence,
)


def test_fix_blocks_patch_without_confirmed_localized_evidence() -> None:
    review = {
        "confirmed_risk_items": [],
    }
    count = _count_confirmed_localized_findings(
        review=review,
        selected_files=["repobrain/github_flow.py"],
    )

    assert count == 0
    assert _should_block_fix_patch_without_localized_evidence(
        require_localized_evidence=True,
        selected_files=["repobrain/github_flow.py"],
        confirmed_localized_findings=count,
    )


def test_fix_allows_patch_with_confirmed_localized_evidence() -> None:
    review = {
        "confirmed_risk_items": [
            {
                "message": "Merge conflict markers present",
                "severity": "high",
                "evidence_paths": ["repobrain/github_flow.py"],
            }
        ]
    }
    count = _count_confirmed_localized_findings(
        review=review,
        selected_files=["repobrain/github_flow.py"],
    )

    assert count == 1
    assert not _should_block_fix_patch_without_localized_evidence(
        require_localized_evidence=True,
        selected_files=["repobrain/github_flow.py"],
        confirmed_localized_findings=count,
    )
