from repobrain.retrieve_pro import retrieve_topk_pro
from repobrain.tky_provider import CandidateChunk


def test_retrieve_topk_pro_limits_candidates_per_file() -> None:
    chunks: list[CandidateChunk] = []
    for index in range(5):
        chunks.append(
            CandidateChunk(
                chunk_id=f"repobrain/a.py:{index}-x",
                file_path="repobrain/a.py",
                line_start=index * 10 + 1,
                line_end=index * 10 + 10,
                score=0.0,
                signature=[1, 2, 3],
            )
        )
    for index in range(5):
        chunks.append(
            CandidateChunk(
                chunk_id=f"repobrain/b.py:{index}-x",
                file_path="repobrain/b.py",
                line_start=index * 10 + 1,
                line_end=index * 10 + 10,
                score=0.0,
                signature=[1, 2, 3],
            )
        )

    ranked = retrieve_topk_pro("provider", chunks, topk=10, task_type="ask", max_per_file=2)

    per_file: dict[str, int] = {}
    for item in ranked:
        per_file[item.file_path] = per_file.get(item.file_path, 0) + 1

    assert per_file["repobrain/a.py"] <= 2
    assert per_file["repobrain/b.py"] <= 2
