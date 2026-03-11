from __future__ import annotations

from repobrain.patch_validator import validate_patch_grounding


def test_placeholder_patch_is_rejected() -> None:
    payload = validate_patch_grounding(
        patch_text=(
            "--- a/path/to/file.py\n"
            "+++ b/path/to/file.py\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+new\n"
        ),
        pr_changed_files=["repobrain/github_flow.py"],
        command_type="fix",
    )

    assert payload["status"] == "patch_validation_failed"
    assert payload["reason_code"] == "PLACEHOLDER_PATCH"
    assert payload["valid"] is False


def test_unrelated_file_patch_is_rejected() -> None:
    payload = validate_patch_grounding(
        patch_text=(
            "--- a/repobrain/review.py\n"
            "+++ b/repobrain/review.py\n"
            "@@ -1 +1 @@\n"
            "-x\n"
            "+y\n"
        ),
        pr_changed_files=["repobrain/github_flow.py"],
        command_type="fix",
    )

    assert payload["status"] == "patch_validation_failed"
    assert payload["reason_code"] == "PATCH_NOT_GROUNDED_IN_PR_FILES"
    assert payload["valid"] is False


def test_grounded_patch_is_accepted() -> None:
    payload = validate_patch_grounding(
        patch_text=(
            "--- a/repobrain/github_flow.py\n"
            "+++ b/repobrain/github_flow.py\n"
            "@@ -10 +10 @@\n"
            "-old\n"
            "+new\n"
        ),
        pr_changed_files=["repobrain/github_flow.py", "README.md"],
        command_type="fix",
    )

    assert payload["status"] == "valid_patch"
    assert payload["reason_code"] == "PATCH_GROUNDED"
    assert payload["valid"] is True


def test_no_patch_outcome_remains_valid_classification() -> None:
    payload = validate_patch_grounding(
        patch_text="",
        pr_changed_files=["repobrain/github_flow.py"],
        command_type="fix",
    )

    assert payload["status"] == "no_patch"
    assert payload["reason_code"] == "NO_PATCH"
    assert payload["valid"] is False

