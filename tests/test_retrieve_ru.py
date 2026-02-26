from pathlib import Path

from repobrain.index_store import build_index, load_index
from repobrain.retrieve import retrieve_topk


def test_retrieve_ru_query_finds_tky_provider_in_top5(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True)
    (repo_root / "README.md").write_text("# RepoBrain\n", encoding="utf-8")
    (repo_root / "repobrain" / "tky_provider.py").write_text(
        "class TKYProvider:\n"
        "    pass\n",
        encoding="utf-8",
    )
    (repo_root / "repobrain" / "other.py").write_text(
        "def unrelated_function():\n"
        "    return 1\n",
        encoding="utf-8",
    )

    zip_path = tmp_path / "index-package.zip"
    build_index(root=repo_root, out_zip=zip_path, store_text=False)
    chunks = load_index(zip_path)

    results = retrieve_topk("Где реализована логика TKYProvider?", chunks, topk=5)

    assert results
    target = next(
        (chunk for chunk in results if "repobrain/tky_provider.py" in chunk.file_path),
        None,
    )
    assert target is not None
    assert target.score > 0
