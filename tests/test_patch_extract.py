from __future__ import annotations

from repobrain.fix.patch_extract import extract_patch_candidate


def test_extract_patch_from_diff_fence() -> None:
    result = extract_patch_candidate(
        "```diff\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-old\n+new\n```"
    )
    assert result.patch_text.startswith("--- a/a.py")
    assert result.extraction_path == "diff_fence"


def test_extract_patch_from_raw_unified_diff() -> None:
    result = extract_patch_candidate(
        "Some preface\n--- a/m.py\n+++ b/m.py\n@@ -3 +3 @@\n-old\n+new\n"
    )
    assert result.patch_text.startswith("--- a/m.py")
    assert result.extraction_path == "raw_diff"


def test_extract_patch_handles_no_patch_token() -> None:
    result = extract_patch_candidate("NO_PATCH")
    assert result.patch_text == ""
    assert result.has_no_patch is True
    assert result.reason_code == "NO_PATCH"


def test_extract_patch_marks_missing_when_no_diff_present() -> None:
    result = extract_patch_candidate("I suggest improving this function with better naming.")
    assert result.patch_text == ""
    assert result.has_no_patch is False
    assert result.reason_code == "PATCH_MISSING"
