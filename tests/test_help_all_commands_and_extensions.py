from repobrain.github_flow import HELP_TEXT


def test_help_documents_profiles_and_audit_extensions() -> None:
    for phrase in (
        "--profile cheap",
        "--profile balanced",
        "--profile premium",
        "--narrative",
        "--executive",
        "How options change the command",
        "Options / extensions: none.",
        "RB_REPOBRAIN_ENABLE_ISSUE_LLM=1",
    ):
        assert phrase in HELP_TEXT


def test_help_documents_audit_premium_semantics_and_safety() -> None:
    assert "implies a premium narrative/explanation layer" in HELP_TEXT
    assert "LLM never modifies final score" in HELP_TEXT
    assert "Partners consume RepoBrain-Action as a public action; they do not need write/admin access" in HELP_TEXT
    assert "No patch/autofix." in HELP_TEXT
    assert "fix-lite" not in HELP_TEXT
