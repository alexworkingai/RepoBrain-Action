from __future__ import annotations

from pathlib import Path


def test_external_foundation_docs_point_to_direct_repobrain_action_host() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    external_mode = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")
    packaging = Path("docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md").read_text(encoding="utf-8")
    onboarding = Path("docs/onboarding/EXTERNAL_REPOSITORY_PILOT_INSTALL.md").read_text(encoding="utf-8")

    assert "docs/examples/repobrain_external_pilot_workflow.yml" in readme
    assert "docs/examples/repobrain_external_pilot_workflow.yml" in external_mode
    assert "docs/examples/repobrain_external_pilot_workflow.yml" in packaging
    assert "alexworkingai/RepoBrain-Action@main" in external_mode
    assert "alexworkingai/RepoBrain-Action@main" in packaging
    assert "repobrain-community" in onboarding
    assert "not required" in onboarding


def test_external_mode_doc_describes_current_direct_pilot_boundary() -> None:
    text = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")

    assert "External Repository Pilot (Direct GitHub Path)" in text
    assert "workflow uses `alexworkingai/RepoBrain-Action@main`" in text
    assert "the old `repobrain-community` bridge is retired" in text.lower()
    assert "no autofix" in text.lower()


def test_packaging_doc_describes_current_direct_pilot_install_shape() -> None:
    text = Path("docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md").read_text(encoding="utf-8")
    workflow = Path("docs/examples/repobrain_external_pilot_workflow.yml").read_text(encoding="utf-8")
    instructions = Path("docs/examples/repobrain.instructions.md").read_text(encoding="utf-8")

    assert "RepoBrain-Action is now the direct product host" in text
    assert "example workflow: `docs/examples/repobrain_external_pilot_workflow.yml`" in text
    assert "example repo guidance: `docs/examples/repobrain.instructions.md`" in text
    assert "No patch was applied. No files were modified." in text
    assert "uses: alexworkingai/RepoBrain-Action@main" in workflow
    assert "repobrain-community" not in workflow
    assert "TOPOCORE_V6_REPO_TOKEN" in workflow
    assert "Treat `/repobrain fix` output as manual-only guidance" in instructions
