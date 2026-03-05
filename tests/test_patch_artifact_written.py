from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _extract_patch_from_stats, _write_patch_artifact
from repobrain.output_md import enforce_comment_limit


def test_patch_artifact_written_from_suggested_patches(tmp_path: Path) -> None:
    stats = {
        "suggested_patches": [
            {"unified_diff": "--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-print('a')\n+print('b')\n"}
        ]
    }
    patch = _extract_patch_from_stats(stats)
    assert patch.startswith("--- a/a.py")

    path = _write_patch_artifact(tmp_path, patch)
    assert path == tmp_path / "artifacts" / "patch.diff"
    assert path.exists()
    assert "+++ b/a.py" in path.read_text(encoding="utf-8")


def test_enforce_comment_limit_truncates_large_patch_comment() -> None:
    huge = "\n".join(f"line {idx}" for idx in range(30000))
    rendered, truncated = enforce_comment_limit(huge, max_bytes=1024)
    assert truncated is True
    assert "Output truncated" in rendered
