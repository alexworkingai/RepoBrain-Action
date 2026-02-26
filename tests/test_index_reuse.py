from pathlib import Path

import repobrain.github_flow as github_flow
from repobrain.index_store import build_index as real_build_index


def test_load_or_build_chunks_reuses_existing_index(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True)
    (repo_root / "repobrain" / "sample.py").write_text(
        "class TKYProvider:\n    pass\n",
        encoding="utf-8",
    )

    index_path = repo_root / "artifacts" / "index-package.zip"
    calls = {"count": 0}

    def wrapped_build_index(root: Path, out_zip: Path, store_text: bool = False) -> None:
        calls["count"] += 1
        real_build_index(root=root, out_zip=out_zip, store_text=store_text)

    monkeypatch.setattr(github_flow, "build_index", wrapped_build_index)

    first = github_flow.load_or_build_chunks(repo_root, index_path)
    second = github_flow.load_or_build_chunks(repo_root, index_path)

    assert calls["count"] == 1
    assert first
    assert second
    assert github_flow.should_build_index(index_path) is False
