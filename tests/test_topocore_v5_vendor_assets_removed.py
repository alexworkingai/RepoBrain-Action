from __future__ import annotations

from pathlib import Path

from repobrain.topocore_backend import TopoCoreBackendError, resolve_backend
from repobrain.topocore_deprecation import TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON

_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding='utf-8')


def _joined(*parts: str) -> str:
    return ''.join(parts)


def test_tkya_vendor_directory_is_absent() -> None:
    assert not (_ROOT / 'repobrain' / 'tkya' / 'vendor').exists()


def test_no_active_runtime_file_imports_vendor_package() -> None:
    combined = '\n'.join(
        _read(path)
        for path in (
            'repobrain/tkya/__init__.py',
            'repobrain/tkya/engine.py',
            'repobrain/topocore_backend.py',
            'repobrain/tky_local.py',
            'repobrain/tky_stub_server.py',
        )
    ).lower()

    dotted = _joined('repobrain', '.', 'tkya', '.', 'vendor')
    slashy = _joined('tkya', '/', 'vendor')
    assert dotted not in combined
    assert slashy not in combined


def test_no_legacy_vendor_execution_tests_remain() -> None:
    removed_vendor_test = _joined('test_', 'topocore_', 'v5', '_vendor.py')
    removed_engine_test = _joined('test_', 'tkya', '_engine.py')
    assert not (_ROOT / 'tests' / removed_vendor_test).exists()
    assert not (_ROOT / 'tests' / removed_engine_test).exists()


def test_action_and_workflows_do_not_advertise_legacy_backends() -> None:
    action_text = _read('action.yml').lower()
    workflow_text = _read('.github/workflows/repobrain.yml').lower()
    local_test_text = _read('.github/workflows/repobrain_local_test.yml').lower()

    assert 'auto or v6' in action_text
    assert 'legacy v5/lite envs are unsupported' in action_text
    assert '- v5' not in workflow_text
    assert '- lite' not in workflow_text
    assert '- v5' not in local_test_text
    assert '- lite' not in local_test_text


def test_legacy_canary_workflow_is_removed() -> None:
    canary_name = _joined('canary', '_', 'v5', '.yml')
    assert not (_ROOT / '.github' / 'workflows' / canary_name).exists()


def test_tkya_engine_stub_contains_no_vendor_execution_markers() -> None:
    text = _read('repobrain/tkya/engine.py').lower()

    assert 'importlib' not in text
    assert 'vendor' not in text
    assert 'topocore_tcx' not in text
    assert 'deprecated topocore v5/lite runtime execution was removed' in text


def test_allow_env_does_not_reenable_execution() -> None:
    try:
        resolve_backend(
            env={
                'RB_TOPOCORE_BACKEND': 'v5',
                'RB_TOPOCORE_ALLOW_DEPRECATED_V5': '1',
            }
        )
    except TopoCoreBackendError as exc:
        assert TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON in str(exc)
    else:  # pragma: no cover
        raise AssertionError('legacy runtime should remain unsupported')


def test_simulation_env_is_documented_as_obsolete_after_runtime_removal() -> None:
    env_ref = _read('docs/env_reference.md').lower()
    removal_note = _read('docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md').lower()

    simulate_key = _joined('rb_topocore_', 'v5', '_simulate_disabled')
    assert simulate_key in removal_note
    assert 'obsolete compatibility input' in removal_note
    assert 'rb_tkya_backend' in env_ref
    assert 'unsupported and fail safely' in env_ref


def test_changed_runtime_files_do_not_introduce_decide_raw_or_patch_behavior() -> None:
    combined = '\n'.join(
        _read(path)
        for path in (
            'repobrain/topocore_backend.py',
            'repobrain/tky_local.py',
            'repobrain/tkya/engine.py',
        )
    )
    assert 'decide_raw(' not in combined
    assert 'apply_patch' not in combined
    assert 'gh pr create' not in combined
