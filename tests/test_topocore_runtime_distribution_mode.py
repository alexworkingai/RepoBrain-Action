from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from repobrain.doctor_status import build_doctor_report, build_status_report
from repobrain.output_md import render_doctor_markdown, render_status_markdown
from repobrain.topocore_v6_adapter import inspect_topocore_v6_runtime_import, resolve_topocore_v6_runtime_mode


ROOT = Path(__file__).resolve().parents[1]


def _fake_topocore_module() -> types.ModuleType:
    class EngineQuery:
        def __init__(self, *, text: str, signature: list[int] | None = None) -> None:
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class EngineRequest:
        def __init__(self, **kwargs: object) -> None:
            self.payload = kwargs

    class ExternalDecisionView:
        pass

    class FakeFacade:
        audit_score_contract_version = 'topocore.audit_score.v1'

        def health(self) -> dict[str, str]:
            return {'release_stage': 'test', 'api_stability': 'foundation'}

        def run_audit_score_v1(self, request: dict[str, object]) -> dict[str, object]:
            return {'contract_version': 'topocore.audit_score.v1'}

    module = types.ModuleType('topocore_v6')
    module.__version__ = '0.0.test'
    module.EngineQuery = EngineQuery
    module.EngineCandidate = EngineCandidate
    module.EngineRequest = EngineRequest
    module.ExternalDecisionView = ExternalDecisionView
    module.create_topocore = lambda: FakeFacade()
    return module


@pytest.fixture(autouse=True)
def _clean_topocore(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ('RB_TOPOCORE_V6_RUNTIME_MODE', 'RB_TOPOCORE_V6_LOCAL_PATH', 'TOPOCORE_V6_REPO_TOKEN'):
        monkeypatch.delenv(name, raising=False)
    sys.modules.pop('topocore_v6', None)
    yield
    sys.modules.pop('topocore_v6', None)


def test_auto_mode_keeps_compatible_default_behavior() -> None:
    details = resolve_topocore_v6_runtime_mode({})

    assert details['requested_mode'] == 'auto'
    assert details['local_path_configured'] is False
    assert details['local_path_kind'] == 'not_configured'


def test_installed_package_mode_does_not_depend_on_local_path(monkeypatch: pytest.MonkeyPatch) -> None:
    sys.modules['topocore_v6'] = _fake_topocore_module()
    diagnostics = inspect_topocore_v6_runtime_import(
        local_path='hidden/private/runtime',
        runtime_mode='installed_package',
    )

    assert diagnostics.ok is True
    assert diagnostics.requested_mode == 'installed_package'
    assert diagnostics.used_mode == 'installed_package'
    assert diagnostics.audit_score_v1_present is True


def test_private_checkout_mode_is_marked_beta_only_in_status_and_doctor(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workflow = tmp_path / '.github' / 'workflows' / 'repobrain.yml'
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text('name: repobrain\npermissions:\n  contents: read\n  issues: write\n', encoding='utf-8')
    monkeypatch.setenv('RB_TOPOCORE_V6_RUNTIME_MODE', 'private_checkout')
    monkeypatch.setenv('RB_TOPOCORE_V6_LOCAL_PATH', 'hidden/private/runtime')

    status_report = build_status_report(repo_root=tmp_path, query='', github_context={})
    doctor_report = build_doctor_report(repo_root=tmp_path, query='', github_context={})
    status_md = render_status_markdown(report=status_report, audit_summary={
        'requested_backend': 'auto', 'resolved_backend': 'not_applicable', 'fallback_used': 'not_applicable', 'fallback_reason': 'status_report_only'
    })
    doctor_md = render_doctor_markdown(report=doctor_report, audit_summary={
        'requested_backend': 'auto', 'resolved_backend': 'not_applicable', 'fallback_used': 'not_applicable', 'fallback_reason': 'doctor_diagnostic_report'
    })

    assert status_report['topocore_dependency_mode'] == 'private_checkout_beta_only'
    assert 'Current run: private runtime checkout path.' in status_md
    assert 'TopoCore dependency mode: `private_checkout_beta_only`' in doctor_md
    assert 'hidden/private/runtime' not in status_md
    assert 'hidden/private/runtime' not in doctor_md


def test_local_path_mode_is_supported_for_local_dev(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('RB_TOPOCORE_V6_RUNTIME_MODE', 'local_path')
    monkeypatch.setenv('RB_TOPOCORE_V6_LOCAL_PATH', 'hidden/local/dev')

    report = build_status_report(repo_root=tmp_path, query='', github_context={})
    assert report['topocore_runtime_mode_requested'] == 'local_path'
    assert report['topocore_dependency_mode'] == 'local_path_dev_only'


def test_disabled_mode_reports_runtime_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('RB_TOPOCORE_V6_RUNTIME_MODE', 'disabled')
    report = build_doctor_report(repo_root=tmp_path, query='', github_context={})
    markdown = render_doctor_markdown(report=report, audit_summary={
        'requested_backend': 'auto', 'resolved_backend': 'not_applicable', 'fallback_used': 'not_applicable', 'fallback_reason': 'doctor_diagnostic_report'
    })

    assert report['topocore_runtime_mode_requested'] == 'disabled'
    assert report['topocore_dependency_mode'] == 'runtime_disabled'
    assert 'runtime mode requested: `disabled`' in markdown.lower()


def test_invalid_runtime_mode_fails_safely() -> None:
    diagnostics = inspect_topocore_v6_runtime_import(runtime_mode='surprise_mode')

    assert diagnostics.ok is False
    assert diagnostics.failure_category == 'topocore_v6_invalid_runtime_mode'


def test_installed_package_mode_reports_unavailable_when_package_is_not_importable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workflow = tmp_path / '.github' / 'workflows' / 'repobrain.yml'
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        'name: repobrain\npermissions:\n  contents: read\n  issues: write\n',
        encoding='utf-8',
    )
    monkeypatch.setenv('RB_TOPOCORE_V6_RUNTIME_MODE', 'installed_package')

    doctor_report = build_doctor_report(repo_root=tmp_path, query='', github_context={})
    status_report = build_status_report(repo_root=tmp_path, query='', github_context={})
    doctor_md = render_doctor_markdown(report=doctor_report, audit_summary={
        'requested_backend': 'auto',
        'resolved_backend': 'not_applicable',
        'fallback_used': 'not_applicable',
        'fallback_reason': 'doctor_diagnostic_report',
    })
    status_md = render_status_markdown(report=status_report, audit_summary={
        'requested_backend': 'auto',
        'resolved_backend': 'not_applicable',
        'fallback_used': 'not_applicable',
        'fallback_reason': 'status_report_only',
    })

    assert doctor_report['topocore_runtime_mode_requested'] == 'installed_package'
    assert doctor_report['topocore_runtime_mode_effective'] == 'installed_package_unavailable'
    assert doctor_report['topocore_dependency_mode'] == 'installed_private_package_unavailable'
    assert doctor_report['overall_status'] == 'WARN'
    assert status_report['topocore_runtime_mode_effective'] == 'installed_package_unavailable'
    assert 'installed private package mode was requested, but the runtime package is not importable' in doctor_md.lower()
    assert 'installed private package requested, but unavailable in this run' in status_md
    assert 'appears available without exposing a checkout path' not in doctor_md.lower()
