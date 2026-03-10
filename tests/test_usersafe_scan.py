from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "usersafe_scan.py"
    spec = spec_from_file_location("repobrain_usersafe_scan", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_usersafe_scan_detects_strong_secret_pattern(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "artifact.json"
    target.write_text('{"token":"ghp_abcdefghijklmnopqrstuvwxyz123456"}', encoding="utf-8")
    issues = module.scan_paths([target])
    assert issues


def test_usersafe_scan_passes_safe_template(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "output_md.py"
    target.write_text('print("usersafe output")\n', encoding="utf-8")
    issues = module.scan_paths([target])
    assert issues == []
