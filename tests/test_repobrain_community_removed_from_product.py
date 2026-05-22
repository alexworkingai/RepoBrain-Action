from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_ACTION_REF = "alexworkingai/RepoBrain-Action@main"


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def _joined(*parts: str) -> str:
    return "".join(parts)


def test_runtime_python_files_do_not_reference_repobrain_community() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (_ROOT / "repobrain").rglob("*.py")
    ).lower()
    assert "repobrain-community" not in combined


def test_action_and_workflows_do_not_depend_on_repobrain_community() -> None:
    action_text = _read("action.yml").lower()
    workflow_text = _read(".github/workflows/repobrain.yml").lower()
    example_text = _read("docs/examples/repobrain_external_pilot_workflow.yml")
    example_text_lower = example_text.lower()

    assert "repobrain-community" not in action_text
    assert "repobrain-community" not in workflow_text
    assert "repobrain-community" not in example_text_lower
    assert "uses: alexworkingai/repobrain-action@main" not in example_text
    assert f"uses: {_ACTION_REF}" in example_text


def test_active_onboarding_docs_make_community_not_required() -> None:
    active_docs = [
        "README.md",
        "docs/EXTERNAL_MODE.md",
        "docs/USER_GUIDE.md",
        "docs/OPERATOR_QUICKSTART.md",
        "docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md",
        "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
    ]
    combined = "\n".join(_read(path) for path in active_docs)
    combined_lower = combined.lower()

    assert "alexworkingai/repobrain-action@main" not in combined
    assert _ACTION_REF in combined
    assert "repobrain-community/.github/workflows" not in combined_lower
    assert "repobrain-community/templates/repobrain.yml" not in combined_lower
    assert "retired" in combined_lower
    assert "not required" in combined_lower


def test_product_architecture_doc_removes_community_from_working_architecture() -> None:
    text = _read("docs/architecture/REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md").lower()

    assert "repobrain-community" in text
    assert "retired from the working product architecture" in text
    assert "not part of the product" in text
    assert "archive later" in text


def test_no_v5_or_lite_runtime_choices_are_reintroduced() -> None:
    combined = "\n".join(
        _read(path).lower()
        for path in (
            "action.yml",
            ".github/workflows/repobrain.yml",
            "docs/examples/repobrain_external_pilot_workflow.yml",
            "docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
        )
    )

    assert "topocore backend for lab/runtime selection: auto or v6" in combined
    assert "- v5" not in combined
    assert "- lite" not in combined
    assert "legacy v5/lite envs are unsupported" in combined


def test_no_active_runtime_surface_reintroduces_removed_runtime_or_autofix() -> None:
    paths = [
        _ROOT / "action.yml",
        _ROOT / ".github" / "workflows" / "repobrain.yml",
        _ROOT / "docs" / "examples" / "repobrain_external_pilot_workflow.yml",
        _ROOT / "docs" / "onboarding" / "INSTALL_REPOBRAIN_EXTERNAL_REPO.md",
        _ROOT / "docs" / "architecture" / "REPOBRAIN_EXTERNAL_REPO_PRODUCT_ARCHITECTURE.md",
    ]
    combined = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in paths).lower()

    assert _joined("topocore_", "v5") not in combined
    assert "repobrain-community/.github/workflows" not in combined
    assert 'rb_apply_patch: "0"' in combined or 'rb_apply_patch: "0"' in _read("docs/examples/repobrain_external_pilot_workflow.yml").lower()
    assert "patch/autofix by default" in combined


def test_no_private_topocore_source_is_copied_into_repo() -> None:
    assert not (_ROOT / ".topocore-v6").exists()
    assert not (_ROOT / "topocore").exists()
