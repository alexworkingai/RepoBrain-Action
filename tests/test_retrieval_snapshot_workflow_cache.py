from __future__ import annotations

from pathlib import Path


def test_workflow_uses_restore_and_save_for_retrieval_snapshot_cache() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")

    assert "Restore RepoBrain retrieval snapshot cache" in workflow
    assert "uses: actions/cache/restore@v4" in workflow
    assert "path: artifacts/.repobrain_cache" in workflow
    assert "repobrain-snapshot-${{ github.run_id }}-${{ github.run_attempt }}" in workflow
    assert "Save RepoBrain retrieval snapshot cache" in workflow
    assert "hashFiles('artifacts/.repobrain_cache/*') != ''" in workflow
    assert "uses: actions/cache/save@v4" in workflow
    assert "steps.snapshot_cache_restore.outputs.cache-primary-key" in workflow


def test_workflow_generates_and_uploads_stability_benchmark_artifact() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")

    assert "Generate RepoBrain stability benchmark artifacts" in workflow
    assert "python scripts/gen_stability_benchmark.py \\" in workflow
    assert "--audit-dir artifacts/audit \\" in workflow
    assert "--output-json artifacts/benchmarks/repobrain_stability_benchmark.json \\" in workflow
    assert "--output-md artifacts/benchmarks/repobrain_stability_benchmark.md" in workflow
    assert "Upload RepoBrain stability benchmark artifacts" in workflow
    assert "name: repobrain-stability-benchmark" in workflow
    assert "artifacts/benchmarks/repobrain_stability_benchmark.json" in workflow
    assert "artifacts/benchmarks/repobrain_stability_benchmark.md" in workflow


def test_workflow_generates_and_uploads_install_readiness_artifact() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")

    assert "Generate RepoBrain install readiness artifacts" in workflow
    assert "python scripts/check_install_readiness.py \\" in workflow
    assert "--workflow .github/workflows/repobrain.yml \\" in workflow
    assert "--output-json artifacts/onboarding/repobrain_install_readiness.json \\" in workflow
    assert "--output-md artifacts/onboarding/repobrain_install_readiness.md" in workflow
    assert "Upload RepoBrain install readiness artifacts" in workflow
    assert "name: repobrain-install-readiness" in workflow
    assert "artifacts/onboarding/repobrain_install_readiness.json" in workflow
    assert "artifacts/onboarding/repobrain_install_readiness.md" in workflow


def test_issue_comment_workflow_resolves_same_repo_pr_head_checkout_ref() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")

    assert "id: checkout_ref" in workflow
    assert "github.rest.pulls.get" in workflow
    assert "same_repo_pr_head_sha" in workflow
    assert "fork_pr_uses_default_branch_runtime" in workflow
    assert "ref: ${{ steps.checkout_ref.outputs.ref }}" in workflow
