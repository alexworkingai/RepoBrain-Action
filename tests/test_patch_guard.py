from __future__ import annotations

from repobrain.fix.patch_guard import evaluate_patch_payload


def test_patch_guard_detects_placeholder_payload() -> None:
    decision = evaluate_patch_payload("Here is patch: update path/to/file and apply placeholder changes")
    assert decision.triggered is True
    assert decision.reason_code == "PATCH_PLACEHOLDER_DETECTED"


def test_patch_guard_allows_real_diff_payload() -> None:
    decision = evaluate_patch_payload(
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n"
    )
    assert decision.triggered is False
