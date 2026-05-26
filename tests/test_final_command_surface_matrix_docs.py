from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_final_command_surface_matrix_doc_exists() -> None:
    assert (ROOT / 'docs/release/FINAL_COMMAND_SURFACE_MATRIX.md').exists()


def test_final_command_surface_matrix_lists_supported_commands_and_fix_lite_unsupported() -> None:
    text = _read('docs/release/FINAL_COMMAND_SURFACE_MATRIX.md').lower()

    for command in (
        '/repobrain help',
        '/repobrain ask',
        '/repobrain locate',
        '/repobrain explain',
        '/repobrain review',
        '/repobrain verify',
        '/repobrain fix',
        '/repobrain audit',
        '/repobrain score',
        '/repobrain doctor',
        '/repobrain status',
        '/repobrain fix-lite',
    ):
        assert command in text

    assert 'not a product command' in text
    assert 'use `/repobrain fix`' in text


def test_final_command_surface_matrix_keeps_audit_score_truth_and_no_mutation() -> None:
    text = _read('docs/release/FINAL_COMMAND_SURFACE_MATRIX.md').lower()

    assert 'audit = full `v6`-enriched repository audit when runtime is available' in text
    assert 'score = compact summary of the same guarded audit engine' in text
    assert 'no patch/autofix' in text
    assert 'no repobrain-created branch, commit, or pr' in text
