from __future__ import annotations

from repobrain.github_publisher import build_check_run_payload


def test_check_run_payload_annotation_limit_and_fields() -> None:
    annotations = [
        {
            "path": "repobrain/github_flow.py",
            "start_line": idx + 1,
            "end_line": idx + 1,
            "annotation_level": "warning",
            "message": f"m{idx}",
            "title": "RepoBrain",
        }
        for idx in range(70)
    ]
    payload = build_check_run_payload(
        name="RepoBrain Review",
        head_sha="abc123",
        conclusion="neutral",
        summary_md="Summary",
        text_md="Body",
        annotations=annotations,
    )
    assert payload["name"] == "RepoBrain Review"
    assert payload["head_sha"] == "abc123"
    output = payload["output"]
    assert isinstance(output, dict)
    emitted = output["annotations"]
    assert isinstance(emitted, list)
    assert len(emitted) == 50
    first = emitted[0]
    assert first["path"] == "repobrain/github_flow.py"
    assert first["start_line"] == 1
    assert first["end_line"] == 1
