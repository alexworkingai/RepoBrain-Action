from __future__ import annotations

from pathlib import Path
import zipfile

import orjson

from repobrain.index_store import CHUNKS_NAME, MANIFEST_NAME, TOPO_MAP_NAME, build_index


def test_index_zip_contains_manifest_and_topo(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "app.py").write_text(
        "def run():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (repo_root / "README.md").write_text("# Repo\n", encoding="utf-8")

    zip_path = tmp_path / "repobrain-index-test.zip"
    build_index(root=repo_root, out_zip=zip_path, store_text=False)

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        names = set(zf.namelist())
        assert MANIFEST_NAME in names
        assert TOPO_MAP_NAME in names
        assert CHUNKS_NAME in names

        manifest = orjson.loads(zf.read(MANIFEST_NAME))
        assert manifest["format_version"] == "1.0"
        assert manifest["producer_version"]
        assert manifest["tkya_backend"]
        assert manifest["files_indexed"] >= 1
        assert manifest["chunks"] >= 1
        assert "tool_versions" in manifest

        topo_map = orjson.loads(zf.read(TOPO_MAP_NAME))
        assert topo_map["format_version"] == "1.0"
        assert topo_map["graph"]["file_nodes"] >= 1
        assert topo_map["graph"]["chunk_nodes"] >= 1
