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


def test_retrieve_topk_pro_prefers_workflow_file_for_workflow_query(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / ".github" / "workflows").mkdir(parents=True)
    (repo_root / "docs").mkdir(parents=True)
    (repo_root / ".topocore-v6" / "docs").mkdir(parents=True)

    (repo_root / ".github" / "workflows" / "repobrain.yml").write_text(
        "name: RepoBrain\non:\n  issue_comment:\n    types: [created]\n",
        encoding="utf-8",
    )
    (repo_root / "docs" / "repobrain_pilot.md").write_text(
        "RepoBrain pilot install and workflow overview.\n",
        encoding="utf-8",
    )
    (repo_root / ".topocore-v6" / "docs" / "CONNECT_APPLICATION_TO_TOPOCORE_V6.md").write_text(
        "Connect the application to TopoCore v6 with private checkout instructions.\n",
        encoding="utf-8",
    )

    zip_path = tmp_path / "index.zip"
    build_index(repo_root, zip_path, store_text=False)
    chunks = load_index(zip_path)

    ranked = retrieve_topk_pro(
        "Where is the RepoBrain workflow configured and how does it connect to RepoBrain-Action?",
        chunks,
        topk=5,
        task_type="ask",
    )

    assert ranked
    assert ranked[0].file_path == ".github/workflows/repobrain.yml"
