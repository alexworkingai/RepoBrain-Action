from pathlib import Path

from repobrain.index_store import MAX_FILE_SIZE_BYTES, build_index, load_index


def test_safe_indexing_skips_binary_large_and_env_files(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True)

    # Included normal file
    (repo_root / "repobrain" / "safe.py").write_text("def ok():\n    return 1\n", encoding="utf-8")
    # Included by path pattern but should be skipped as binary
    (repo_root / "repobrain" / "binary.md").write_bytes(b"abc\x00def")
    # Included by path pattern but should be skipped by size
    (repo_root / "repobrain" / "large.md").write_text(
        "x" * (MAX_FILE_SIZE_BYTES + 1),
        encoding="utf-8",
    )
    # Should be excluded by denylist path
    (repo_root / ".env").write_text("API_KEY=secret\n", encoding="utf-8")

    zip_path = tmp_path / "index.zip"
    build_index(repo_root, zip_path, store_text=False)
    chunks = load_index(zip_path)

    file_paths = {chunk.file_path for chunk in chunks}
    assert "repobrain/safe.py" in file_paths
    assert "repobrain/binary.md" not in file_paths
    assert "repobrain/large.md" not in file_paths
    assert ".env" not in file_paths
