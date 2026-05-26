from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_removed_mutation_helpers_are_absent_from_github_flow() -> None:
    text = _read("repobrain/github_flow.py")

    assert "_maybe_apply_patch" not in text
    assert "_maybe_create_patch_pr" not in text


def test_no_active_production_call_sites_for_removed_mutation_helpers() -> None:
    combined = "\n".join(
        _read(path.relative_to(ROOT).as_posix())
        for path in (ROOT / "repobrain").rglob("*.py")
    )

    assert "_maybe_apply_patch(" not in combined
    assert "_maybe_create_patch_pr(" not in combined


def test_fix_and_safety_docs_preserve_no_mutation_truth() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/commands/REPOBRAIN_COMMANDS.md",
            "docs/release/FINAL_COMMAND_SURFACE_MATRIX.md",
            "docs/security/GITHUB_ACTIONS_PERMISSION_MODEL.md",
        )
    ).lower()

    assert "no patch/autofix" in combined
    assert "no repobrain-created branch, commit, or pr" in combined
    assert "proposal/governance only" in combined
