from repobrain.github_flow import HELP_TEXT


def test_help_uses_four_block_manual_structure() -> None:
    assert "## 1. Command list" in HELP_TEXT
    assert "## 2. Command reference" in HELP_TEXT
    assert "## 3. Environment / policy" in HELP_TEXT
    assert "## 4. Safety notes" in HELP_TEXT


def test_help_includes_reference_block_for_every_supported_command() -> None:
    for command in (
        "### /repobrain help",
        "### /repobrain ask",
        "### /repobrain locate",
        "### /repobrain explain",
        "### /repobrain review",
        "### /repobrain verify",
        "### /repobrain fix",
        "### /repobrain audit",
        "### /repobrain score",
        "### /repobrain doctor",
        "### /repobrain status",
    ):
        assert command in HELP_TEXT
