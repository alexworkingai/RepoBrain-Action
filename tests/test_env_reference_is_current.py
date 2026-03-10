from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_env_reference_up_to_date.py"
    spec = spec_from_file_location("repobrain_check_env_reference", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_env_reference_is_current() -> None:
    module = _load_module()
    ok, _message = module.check_current()
    assert ok is True
