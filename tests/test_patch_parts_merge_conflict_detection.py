from __future__ import annotations

from repobrain.github_flow import _merge_patch_parts


def test_patch_parts_conflict_detection_on_overlap() -> None:
    part_a = {
        "batch_id": "a",
        "patch": "\n".join(
            [
                "diff --git a/app.py b/app.py",
                "--- a/app.py",
                "+++ b/app.py",
                "@@ -1,3 +10,3 @@",
                "-old",
                "+new",
            ]
        ),
    }
    part_b = {
        "batch_id": "b",
        "patch": "\n".join(
            [
                "diff --git a/app.py b/app.py",
                "--- a/app.py",
                "+++ b/app.py",
                "@@ -1,3 +11,4 @@",
                "-old2",
                "+new2",
            ]
        ),
    }

    merged, has_conflict, details = _merge_patch_parts([part_a, part_b])

    assert merged
    assert has_conflict is True
    assert details
