from pathlib import Path

from repobrain.github_flow import resolve_repo_root


def test_repo_root_finds_pyproject(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    nested = root / "a" / "b" / "c"
    nested.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")

    resolved = resolve_repo_root(nested, max_depth=5)
    assert resolved == root.resolve()
