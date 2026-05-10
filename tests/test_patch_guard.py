from __future__ import annotations

from repobrain.fix.patch_guard import evaluate_patch_payload


def test_patch_guard_allows_empty_payload_without_triggering() -> None:
    decision = evaluate_patch_payload("")
    assert decision.triggered is False
    assert decision.reason_code == "EMPTY_OUTPUT"


def test_patch_guard_detects_placeholder_payload() -> None:
    decision = evaluate_patch_payload("Here is patch: update path/to/file and apply placeholder changes")
    assert decision.triggered is True
    assert decision.reason_code == "PATCH_PLACEHOLDER_DETECTED"


def test_patch_guard_detects_generic_patch_prose_without_diff() -> None:
    decision = evaluate_patch_payload("Here is the patch. You can fix by renaming the function.")
    assert decision.triggered is True
    assert decision.reason_code == "PATCH_GENERIC_TEXT"


def test_patch_guard_allows_real_diff_payload() -> None:
    decision = evaluate_patch_payload(
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n"
    )
    assert decision.triggered is False


def test_patch_guard_treats_whitespace_only_as_empty_output() -> None:
    decision = evaluate_patch_payload("   \n\t  ")

    assert decision.triggered is False
    assert decision.reason_code == "EMPTY_OUTPUT"
    assert decision.reason_short == "No patch output provided."


def test_patch_guard_keeps_placeholder_detection_even_with_diff_markers() -> None:
    decision = evaluate_patch_payload(
        "```diff\n--- a/path/to/file.py\n+++ b/path/to/file.py\n@@ -1 +1 @@\n-old\n+new\n```"
    )

    assert decision.triggered is True
    assert decision.reason_code == "PATCH_PLACEHOLDER_DETECTED"


def test_patch_guard_allows_generic_intro_when_concrete_diff_is_present() -> None:
    decision = evaluate_patch_payload(
        "Here is the patch.\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n"
    )

    assert decision.triggered is False
    assert decision.reason_code == "PATCH_GUARD_CLEAR"


def test_patch_guard_leaves_malformed_diff_like_text_non_triggering() -> None:
    decision = evaluate_patch_payload("diff --git a/app.py b/app.py\nrename this function maybe")

    assert decision.triggered is False
    assert decision.reason_code == "PATCH_GUARD_CLEAR"


def test_patch_guard_decision_is_deterministic_for_generic_prose() -> None:
    first = evaluate_patch_payload("Apply this patch to make the update.")
    second = evaluate_patch_payload("Apply this patch to make the update.")

    assert first == second
    assert first.reason_code == "PATCH_GENERIC_TEXT"
