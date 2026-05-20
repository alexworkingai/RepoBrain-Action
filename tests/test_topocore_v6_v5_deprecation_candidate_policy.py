from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding="utf-8")


def test_deprecation_candidate_document_exists_and_states_current_policy() -> None:
    path = _ROOT / "docs" / "architecture" / "TOPOCORE_V6_V5_DEPRECATION_CANDIDATE.md"

    assert path.exists()

    text = path.read_text(encoding="utf-8").lower()
    assert "v6 `issue_comment` lab mode is now the active lab default".lower() in text
    assert "rb_enable_issue_comment_v6_lab=1" in text
    assert "fallback-only" in text
    assert "deprecation candidate" in text
    assert "v5 removal is not approved" in text
    assert "sprint 65 advances the candidate state to runtime removal" in text
    assert "no patch application" in text
    assert "no commit, branch, or pr creation by repobrain" in text


def test_indexes_reference_v5_deprecation_candidate_policy() -> None:
    migration_index = _read("docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md")
    coverage_index = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md").lower()

    assert "docs/architecture/TOPOCORE_V6_V5_DEPRECATION_CANDIDATE.md" in migration_index
    assert "docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md" in migration_index
    assert "docs/architecture/topocore_v6_v5_runtime_removal.md" in coverage_index
    assert "docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md" in migration_index
    assert "docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md" in migration_index


def test_sprint_62_prep_note_exists_and_removal_is_still_not_approved() -> None:
    text = _read("docs/architecture/TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md").lower()

    assert "v6 is the active `issue_comment` lab default".lower() in text
    assert "rb_enable_issue_comment_v6_lab=1" in text
    assert "v5 fallback-only" in text
    assert "v5 removal not approved" in text
    assert "rb_topocore_v5_simulate_disabled=1" in text
    assert "rb_topocore_allow_deprecated_v5=1" in text
    assert "sprint 65 completes runtime removal" in text


def test_sprint_does_not_change_runtime_files() -> None:
    runtime_paths = [
        "repobrain/github_flow.py",
        "repobrain/output_md.py",
        "repobrain/topocore_backend.py",
        ".github/workflows/repobrain.yml",
        "action.yml",
    ]

    combined = "\n".join(_read(path) for path in runtime_paths)

    assert "decide_raw(" not in combined
