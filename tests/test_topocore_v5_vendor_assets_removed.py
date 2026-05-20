from __future__ import annotations

from pathlib import Path

from repobrain.topocore_backend import TopoCoreBackendError, resolve_backend
from repobrain.topocore_deprecation import TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON

_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (_ROOT / relative_path).read_text(encoding='utf-8')


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

    assert 'repobrain.tkya.vendor' not in combined
    assert 'vendor/Topocore'.lower() not in combined


def test_no_v5_vendor_execution_tests_remain() -> None:
    assert not (_ROOT / 'tests' / 'test_topocore_v5_vendor.py').exists()
    assert not (_ROOT / 'tests' / 'test_tkya_engine.py').exists()


def test_action_and_workflows_do_not_advertise_v5_or_lite_as_supported_backends() -> None:
    action_text = _read('action.yml').lower()
    workflow_text = _read('.github/workflows/repobrain.yml').lower()
    local_test_text = _read('.github/workflows/repobrain_local_test.yml').lower()

    assert 'auto or v6' in action_text
    assert 'legacy v5/lite envs are unsupported' in action_text
    assert '- v5' not in workflow_text
    assert '- lite' not in workflow_text
    assert '- v5' not in local_test_text
    assert '- lite' not in local_test_text


def test_canary_v5_workflow_is_removed() -> None:
    assert not (_ROOT / '.github' / 'workflows' / 'canary_v5.yml').exists()


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
        raise AssertionError('legacy v5 runtime should remain unsupported')


def test_simulation_env_is_documented_as_obsolete_after_runtime_removal() -> None:
    env_ref = _read('docs/env_reference.md').lower()
    removal_note = _read('docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md').lower()

    assert 'rb_topocore_v5_simulate_disabled' in removal_note
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
