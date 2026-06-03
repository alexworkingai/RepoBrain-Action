from repobrain.github_flow import HELP_TEXT


def test_help_output_has_authoritative_sections_and_no_fix_lite() -> None:
    assert "RepoBrain supported commands:" in HELP_TEXT
    assert "Examples:" in HELP_TEXT
    assert "Command notes:" in HELP_TEXT
    assert "Execution profiles:" in HELP_TEXT
    assert "Safety notes:" in HELP_TEXT
    assert "/repobrain fix-lite" not in HELP_TEXT
    assert "/repobrain fix" in HELP_TEXT
