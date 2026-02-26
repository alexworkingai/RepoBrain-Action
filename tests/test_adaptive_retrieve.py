from pathlib import Path

from repobrain.config import RepoBrainConfig
from repobrain.index_store import build_index, load_index
from repobrain.retrieve import retrieve_adaptive


def _build_mini_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True)
    (repo_root / "README.md").write_text("# RepoBrain\n", encoding="utf-8")
    (repo_root / "repobrain" / "tky_provider.py").write_text(
        "class TKYProvider:\n"
        "    pass\n",
        encoding="utf-8",
    )
    (repo_root / "repobrain" / "other_module.py").write_text(
        "def helper():\n"
        "    return 'ok'\n",
        encoding="utf-8",
    )
    return repo_root


def test_retrieve_adaptive_fast_for_tkyprovider_query(tmp_path: Path) -> None:
    repo_root = _build_mini_repo(tmp_path)
    zip_path = tmp_path / "index.zip"
    build_index(repo_root, zip_path, store_text=False)
    chunks = load_index(zip_path)

    candidates, mode = retrieve_adaptive(
        "Где реализована логика TKYProvider?",
        chunks,
        RepoBrainConfig(),
    )

    assert mode == "FAST"
    assert candidates
    assert "repobrain/tky_provider.py" in candidates[0].file_path
    assert candidates[0].score > 0


def test_retrieve_adaptive_deep_for_low_relevance_query(tmp_path: Path) -> None:
    repo_root = _build_mini_repo(tmp_path)
    zip_path = tmp_path / "index.zip"
    build_index(repo_root, zip_path, store_text=False)
    chunks = load_index(zip_path)

    candidates, mode = retrieve_adaptive(
        "Какой сегодня курс доллара?",
        chunks,
        RepoBrainConfig(),
    )

    assert mode == "DEEP"
    assert isinstance(candidates, list)
