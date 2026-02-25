from pathlib import Path

from repobrain.index_store import build_index, load_index
from repobrain.retrieve import retrieve_topk


def test_build_load_and_retrieve_index(tmp_path: Path) -> None:
    zip_path = tmp_path / "index-package.zip"

    build_index(root=Path("repobrain"), out_zip=zip_path, store_text=False)
    chunks = load_index(zip_path)
    results = retrieve_topk("provider", chunks, topk=10)

    assert zip_path.exists()
    assert chunks
    assert results
