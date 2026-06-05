from __future__ import annotations

from repobrain.audit_contract import _build_v6_executive_summary


def test_v6_executive_summary_reports_final_score_before_static_baseline() -> None:
    text = _build_v6_executive_summary(
        static_score=84,
        static_band="GOOD",
        merged_score=86,
        merged_band="STRONG",
        adjustments=[{"category": "Governance", "delta": 2}],
        existing_summary="The static RepoBrain baseline score is 84/100 (`GOOD`).",
        pr_context={"is_pr": False},
    )

    assert text.startswith("The final RepoBrain score is `86 / 100` (`STRONG`).")
    assert "Static baseline was `84 / 100` (`GOOD`)" in text
    assert "current score" not in text.lower()


def test_v6_executive_summary_reports_zero_delta_without_false_change_language() -> None:
    text = _build_v6_executive_summary(
        static_score=85,
        static_band="STRONG",
        merged_score=85,
        merged_band="STRONG",
        adjustments=[],
        existing_summary="The static RepoBrain baseline score is 85/100 (`STRONG`).",
        pr_context={"is_pr": True},
    )

    assert text.startswith("The final RepoBrain score with PR context is `85 / 100` (`STRONG`).")
    assert "Static baseline was `85 / 100` (`STRONG`)" in text
    assert "retained the same final score" in text
    assert "no changes to the overall score were needed" not in text.lower()
