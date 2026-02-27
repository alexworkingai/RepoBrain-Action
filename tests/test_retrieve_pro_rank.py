from pathlib import Path

from repobrain.index_store import build_index, load_index
from repobrain.retrieve_pro import retrieve_topk_pro


def test_retrieve_topk_pro_ranks_tky_provider_first(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True)
    (repo_root / "repobrain" / "tky_provider.py").write_text(
        "class TKYProvider:\n    pass\n",
        encoding="utf-8",
    )
    (repo_root / "repobrain" / "other_module.py").write_text(
        "def helper():\n    return 1\n",
        encoding="utf-8",
    )

    zip_path = tmp_path / "index.zip"
    build_index(repo_root, zip_path, store_text=False)
    chunks = load_index(zip_path)

    ranked = retrieve_topk_pro("Где реализована логика TKYProvider?", chunks, topk=5, task_type="ask")

    assert ranked
    assert "repobrain/tky_provider.py" in ranked[0].file_path
    assert len(ranked) > 1
    assert ranked[0].score > ranked[1].score
