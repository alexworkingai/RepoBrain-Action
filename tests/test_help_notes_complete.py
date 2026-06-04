from repobrain.github_flow import HELP_TEXT


def test_help_notes_cover_all_supported_commands() -> None:
    for command in (
        "/repobrain help",
        "/repobrain ask",
        "/repobrain locate",
        "/repobrain explain",
        "/repobrain review",
        "/repobrain verify",
        "/repobrain fix",
        "/repobrain audit",
        "/repobrain score",
        "/repobrain doctor",
        "/repobrain status",
    ):
        assert command in HELP_TEXT
    assert "### /repobrain help" in HELP_TEXT
    assert "### /repobrain audit" in HELP_TEXT
    assert "fix-lite" not in HELP_TEXT
