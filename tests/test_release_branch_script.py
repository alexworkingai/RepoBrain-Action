from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "release" / "create_release_branch.py"
    spec = spec_from_file_location("repobrain_create_release_branch", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_release_branch_name() -> None:
    module = _load_module()
    assert module.build_release_branch_name("0.5.0-rc.1") == "release/0.5.0-rc.1"


def test_build_commands_uses_version_and_base_branch() -> None:
    module = _load_module()
    commands = module.build_commands(version="0.5.0-rc.1", base_branch="main")
    assert commands == [
        ["git", "checkout", "main"],
        ["git", "pull"],
        ["git", "checkout", "-b", "release/0.5.0-rc.1"],
    ]


def test_main_dry_run_prints_plan(tmp_path: Path, capsys) -> None:
    module = _load_module()
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    exit_code = module.main(["--version-file", str(version_file)])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "git checkout -b release/1.2.3" in out
    assert "Dry-run mode" in out
