from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding='utf-8')


def _joined(*parts: str) -> str:
    return ''.join(parts)


def test_deleted_standalone_guides_are_absent() -> None:
    guide_a = _joined('topocore_', 'v5', '_architecture.md')
    guide_b = _joined('topocore_', 'v5', '_complete_guide.md')
    assert not (_ROOT / 'docs' / guide_a).exists()
    assert not (_ROOT / 'docs' / guide_b).exists()


def test_no_tracked_file_links_to_deleted_guides() -> None:
    combined = '\n'.join(
        p.read_text(encoding='utf-8', errors='ignore')
        for p in _ROOT.rglob('*')
        if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts
    ).lower()
    assert _joined('topocore_', 'v5', '_architecture') not in combined
    assert _joined('topocore_', 'v5', '_complete_guide') not in combined


def test_vendor_and_canary_artifacts_are_absent() -> None:
    assert not (_ROOT / 'repobrain' / 'tkya' / 'vendor').exists()
    assert not (_ROOT / '.github' / 'workflows' / _joined('canary', '_', 'v5', '.yml')).exists()


def test_active_runtime_surfaces_have_no_lowercase_legacy_runtime_markers() -> None:
    paths = [
        _ROOT / 'action.yml',
        _ROOT / '.github' / 'workflows' / 'repobrain.yml',
        _ROOT / '.github' / 'workflows' / 'repobrain_local_test.yml',
    ]
    paths.extend((_ROOT / 'repobrain').rglob('*.py'))
    paths.extend((_ROOT / 'tests').rglob('*.py'))
    combined = '\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in paths)

    assert _joined('topocore_', 'v5') not in combined
    assert _joined('repobrain', '.', 'tkya', '.', 'vendor') not in combined
    assert _joined('tkya', '/', 'vendor') not in combined
    assert _joined('v5', ' vendor') not in combined.lower()
    assert _joined('canary', '_', 'v5') not in combined


def test_tkya_compatibility_files_remain_non_executable() -> None:
    engine_text = _read('repobrain/tkya/engine.py').lower()
    init_text = _read('repobrain/tkya/__init__.py').lower()

    assert 'topocore_tcx' not in engine_text
    assert 'importlib' not in engine_text
    assert 'vendor' not in engine_text
    assert 'removed' in engine_text
    assert 'vendor' not in init_text


def test_legacy_env_docs_are_marked_obsolete_or_unsupported() -> None:
    env_ref = _read('docs/env_reference.md').lower()
    assert 'supported values: auto or v6' in env_ref
    assert 'obsolete legacy env' in env_ref
    assert 'obsolete legacy simulation env' in env_ref
    assert 'unsupported and fail safely' in env_ref


def test_historical_v5_docs_are_marked_historical_or_superseded() -> None:
    docs = [
        'docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md',
        'docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md',
        'docs/architecture/TOPOCORE_V6_DEFAULT_LAB_RUNTIME_POLICY.md',
        'docs/architecture/TOPOCORE_V6_GITHUB_RUNTIME_LAB_SWITCH.md',
        'docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md',
        'docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_RUNTIME.md',
        'docs/architecture/TOPOCORE_V6_GITHUB_LAB_DEPENDENCY_GATE.md',
        'docs/architecture/TOPOCORE_V6_GITHUB_LAB_TKYA_ARTIFACT_OPTIONALITY.md',
        'docs/architecture/TOPOCORE_V6_WORKFLOW_DISPATCH_MEANINGFUL_DECISION_PATH.md',
    ]
    markers = {'historical', 'superseded', 'removed'}
    for relative in docs:
        head = '\n'.join(_read(relative).lower().splitlines()[:12])
        assert any(marker in head for marker in markers), relative


def test_no_decide_raw_or_patch_autofix_is_reintroduced() -> None:
    combined = '\n'.join(
        _read(path)
        for path in (
            'repobrain/topocore_backend.py',
            'repobrain/tky_local.py',
            'repobrain/tkya/engine.py',
        )
    ).lower()
    assert 'decide_raw(' not in combined
    assert 'apply_patch(' not in combined
    assert 'autofix' not in combined
