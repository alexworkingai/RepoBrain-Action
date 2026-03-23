from __future__ import annotations

from pathlib import Path


def test_workflow_uses_restore_and_save_for_retrieval_snapshot_cache() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")

    assert "Restore RepoBrain retrieval snapshot cache" in workflow
    assert "uses: actions/cache/restore@v4" in workflow
    assert "repobrain-snapshot-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "Save RepoBrain retrieval snapshot cache" in workflow
    assert "uses: actions/cache/save@v4" in workflow
    assert "steps.snapshot_cache_restore.outputs.cache-primary-key" in workflow
