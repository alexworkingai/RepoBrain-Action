from __future__ import annotations

import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECK_SCRIPT = ROOT / 'scripts' / 'check_topocore_v6_runtime_import.py'
PROBE_SCRIPT = ROOT / 'scripts' / 'probe_topocore_v6_contract.py'
VALIDATE_SCRIPT = ROOT / 'scripts' / 'validate_topocore_v6_local.py'


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_fake_topocore(parent: Path) -> Path:
    pkg = parent / 'topocore_v6'
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / '__init__.py').write_text(
        "__version__='0.0.test'\n"
        "class EngineQuery:\n    def __init__(self, *, text, signature=None, task_type=None, **kwargs):\n        self.text=text\n        self.signature=signature\n        self.task_type=task_type\n\n"
        "class EngineCandidate:\n    def __init__(self, *, chunk_id, score_local, metadata=None, **kwargs):\n        self.chunk_id=chunk_id\n        self.score_local=score_local\n        self.metadata=metadata or {}\n\n"
        "class EngineRequest:\n    def __init__(self, *, task_type=None, query=None, candidates=None, limits=None, policy=None, **kwargs):\n        self.task_type=task_type\n        self.query=query\n        self.candidates=candidates or []\n        self.limits=limits or {}\n        self.policy=policy or {}\n\n"
        "class ExternalDecisionView:\n    pass\n\n"
        "class _Facade:\n"
        "    audit_score_contract_version='topocore.audit_score.v1'\n"
        "    def health(self):\n        return {'release_stage':'test','api_stability':'foundation'}\n"
        "    def decide(self, request):\n        return {'status':'ok'}\n"
        "    def decide_external(self, request):\n        return type('R', (), {'status':'ready','action':'proceed','confidence_band':'high','confidence_hint':'high','message_code':'READY','safe_reason_code':'advisory_ready'})()\n"
        "    def run_audit_score_v1(self, request):\n        return {'contract_version':'topocore.audit_score.v1'}\n\n"
        "def create_topocore():\n    return _Facade()\n",
        encoding='utf-8',
    )
    return parent


def test_runtime_import_script_reports_requested_and_used_modes(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore(tmp_path)
    env = dict(os.environ)
    env['RB_TOPOCORE_V6_RUNTIME_MODE'] = 'local_path'
    env['RB_TOPOCORE_V6_LOCAL_PATH'] = str(fake_parent)

    result = subprocess.run([sys.executable, str(CHECK_SCRIPT)], cwd=ROOT, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert 'TOPOCORE_V6_RUNTIME_MODE_REQUESTED=local_path' in result.stdout
    assert 'TOPOCORE_V6_RUNTIME_MODE_USED=local_path' in result.stdout
    assert 'TOPOCORE_V6_AUDIT_SCORE_V1_PRESENT=yes' in result.stdout
    assert str(fake_parent) not in result.stdout


def test_runtime_import_script_disabled_mode_skips_safely() -> None:
    env = dict(os.environ)
    env['RB_TOPOCORE_V6_RUNTIME_MODE'] = 'disabled'

    result = subprocess.run([sys.executable, str(CHECK_SCRIPT)], cwd=ROOT, env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 0
    assert 'TOPOCORE_V6_RUNTIME_IMPORT=skipped' in result.stdout
    assert 'TOPOCORE_V6_FAILURE_CATEGORY=topocore_v6_runtime_disabled' in result.stdout


def test_contract_probe_reports_runtime_mode_without_private_path(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore(tmp_path)
    module = _load_module(PROBE_SCRIPT, 'probe_topocore_v6_contract_runtime_test')
    buffer = io.StringIO()
    code = module.main(env={
        'RB_TOPOCORE_V6_CONTRACT_PROBE': '1',
        'RB_TOPOCORE_V6_REQUIRE_LOCAL': '1',
        'RB_TOPOCORE_V6_RUNTIME_MODE': 'local_path',
        'RB_TOPOCORE_V6_LOCAL_PATH': str(fake_parent),
    }, stdout=buffer)
    output = buffer.getvalue()

    assert code == 0
    assert 'runtime_mode_requested=local_path' in output
    assert 'runtime_mode_used=local_path' in output
    assert str(fake_parent) not in output


def test_local_validation_script_reports_runtime_mode_without_private_path(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore(tmp_path)
    module = _load_module(VALIDATE_SCRIPT, 'validate_topocore_v6_local_runtime_test')
    buffer = io.StringIO()
    code = module.main(env={
        'RB_TOPOCORE_V6_LOCAL_VALIDATE': '1',
        'RB_TOPOCORE_V6_RUNTIME_MODE': 'local_path',
        'RB_TOPOCORE_V6_LOCAL_PATH': str(fake_parent),
    }, stdout=buffer)
    output = buffer.getvalue()

    assert code == 0
    assert 'runtime_mode_requested=local_path' in output
    assert 'local_path_configured=yes' in output
    assert str(fake_parent) not in output
