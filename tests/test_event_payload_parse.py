from pathlib import Path

from repobrain.github_flow import extract_comment_text_from_event, extract_issue_number_from_event


def test_extract_issue_comment_payload_fields(tmp_path: Path) -> None:
    payload = """
{
  "action": "created",
  "issue": {"number": 42},
  "comment": {"body": "/repobrain ask Where is TKYProvider logic?"}
}
""".strip()
    event_path = tmp_path / "event.json"
    event_path.write_text(payload, encoding="utf-8")

    assert extract_comment_text_from_event(event_path) == "/repobrain ask Where is TKYProvider logic?"
    assert extract_issue_number_from_event(event_path) == 42
