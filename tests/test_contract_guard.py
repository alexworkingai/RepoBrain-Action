from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_tkya_contract_guard.py"
    spec = spec_from_file_location("repobrain_tkya_contract_guard", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tkya_contract_guard_passes() -> None:
    module = _load_module()
    ok, errors = module.check_contract()
    assert ok is True, errors
