from repobrain.github_flow import HELP_TEXT


def test_help_output_has_authoritative_sections_and_no_fix_lite() -> None:
    assert "## 1. Command list" in HELP_TEXT
    assert "## 2. Command reference" in HELP_TEXT
    assert "## 3. Environment / policy" in HELP_TEXT
    assert "## 4. Safety notes" in HELP_TEXT
    assert "/repobrain fix-lite" not in HELP_TEXT
    assert "/repobrain fix" in HELP_TEXT
