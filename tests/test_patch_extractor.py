from __future__ import annotations

from repobrain.github_flow import _extract_patch_candidate, _extract_patch_from_llm_text


def test_patch_extractor_handles_diff_fence() -> None:
    text = (
        "Here is patch\n"
        "```diff\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,1 +1,1 @@\n"
        "-old\n"
        "+new\n"
        "```\n"
    )
    patch = _extract_patch_from_llm_text(text)
    assert patch.startswith("--- a/app.py")
    assert "+++ b/app.py" in patch


def test_patch_extractor_handles_plain_unified_diff() -> None:
    text = (
        "Some intro text\n"
        "--- a/module.py\n"
        "+++ b/module.py\n"
        "@@ -3,2 +3,2 @@\n"
        "-bad\n"
        "+good\n"
    )
    patch = _extract_patch_from_llm_text(text)
    assert patch.startswith("--- a/module.py")
    assert "@@ -3,2 +3,2 @@" in patch


def test_patch_extractor_handles_json_envelope() -> None:
    text = (
        '{'
        '"result":"patch",'
        '"diff":"--- a/a.py\\n+++ b/a.py\\n@@ -1 +1 @@\\n-old\\n+new\\n"'
        "}"
    )
    patch = _extract_patch_from_llm_text(text)
    assert patch.startswith("--- a/a.py")
    assert "+++ b/a.py" in patch


def test_patch_extractor_recognizes_no_patch() -> None:
    patch, has_fence, has_raw, has_json, has_no_patch, extraction_path, _chars = _extract_patch_candidate(
        "NO_PATCH"
    )
    assert patch == ""
    assert has_fence is False
    assert has_raw is False
    assert has_json is False
    assert has_no_patch is True
    assert extraction_path == "no_patch"
