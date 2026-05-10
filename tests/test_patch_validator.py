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


def test_generic_prose_patch_payload_is_invalid() -> None:
    payload = validate_patch_grounding(
        patch_text="Here is the patch you can apply to fix the problem.",
        pr_changed_files=["repobrain/github_flow.py"],
        command_type="fix",
    )

    assert payload["status"] == "patch_validation_failed"
    assert payload["reason_code"] == "INVALID_PATCH_FORMAT"
    assert payload["valid"] is False
    assert payload["touched_files"] == []
    assert payload["placeholder_detected"] is False


def test_diff_like_payload_without_touched_files_is_rejected() -> None:
    payload = validate_patch_grounding(
        patch_text=(
            "--- a/repobrain/github_flow.py\n"
            "+++ /dev/null\n"
            "@@ -10 +0,0 @@\n"
            "-legacy\n"
        ),
        pr_changed_files=["repobrain/github_flow.py"],
        command_type="fix",
    )

    assert payload["status"] == "patch_validation_failed"
    assert payload["reason_code"] == "PATCH_WITHOUT_TOUCHED_FILES"
    assert payload["valid"] is False
    assert payload["touched_files"] == []


def test_non_fix_command_can_validate_grounded_diff_without_pr_changed_files() -> None:
    payload = validate_patch_grounding(
        patch_text=(
            "--- a/repobrain/github_flow.py\n"
            "+++ b/repobrain/github_flow.py\n"
            "@@ -10 +10 @@\n"
            "-old\n"
            "+new\n"
        ),
        pr_changed_files=[],
        command_type="review",
    )

    assert payload["status"] == "valid_patch"
    assert payload["reason_code"] == "PATCH_GROUNDED"
    assert payload["valid"] is True
    assert payload["touched_files"] == ["repobrain/github_flow.py"]
    assert payload["grounded"] is True
