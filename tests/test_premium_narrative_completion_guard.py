from __future__ import annotations

from repobrain.github_flow import _apply_premium_narrative_length_guard


def test_premium_narrative_is_shortened_with_explicit_notice_when_too_long() -> None:
    long_text = " ".join(["premium"] * 1100)

    shortened, was_shortened = _apply_premium_narrative_length_guard(long_text)

    assert was_shortened is True
    assert "Premium narrative shortened to stay within response budget." in shortened
    assert len(shortened.split()) < len(long_text.split())
