from __future__ import annotations

from pathlib import Path


def test_external_github_foundation_docs_point_to_public_community_host() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    external_mode = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")
    packaging = Path("docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md").read_text(encoding="utf-8")

    assert "repobrain-community/templates/repobrain.yml" in readme
    assert "repobrain-community/templates/repobrain.yml" in external_mode
    assert "repobrain-community/templates/repobrain.yml" in packaging
    assert "alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main" in external_mode
    assert "alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main" in packaging


def test_external_mode_doc_describes_current_github_foundation_boundary() -> None:
    text = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")

    assert "External GitHub Mode Foundation (Third-Party)" in text
    assert "supported: `/repobrain help`, `/repobrain doctor`, `/repobrain ask ...`, `/repobrain review` (bounded read-only Review Candidate), `/repobrain fix` (bounded Fix-Lite Candidate manual-only patch suggestion)" in text
    assert "unsupported (explicit block): out-of-contract commands" in text
    assert "repobrain-community/templates/repobrain.yml" in text


def test_packaging_doc_describes_review_candidate_and_fix_lite_candidate() -> None:
    text = Path("docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md").read_text(encoding="utf-8")

    assert "/repobrain review" in text
    assert "bounded read-only Review Candidate" in text
    assert "/repobrain fix" in text
    assert "bounded Fix-Lite Candidate manual-only patch suggestion" in text
    assert "RepoBrain-Action is not the public runtime or install-template host" in text
    assert "No patch was applied. No files were modified." in text
