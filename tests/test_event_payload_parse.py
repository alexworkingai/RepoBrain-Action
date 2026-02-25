from pathlib import Path

from repobrain.github_flow import (
    extract_comment_id_from_event,
    extract_comment_text_from_event,
    extract_comment_user_login_from_event,
    extract_event_context_from_event,
    extract_is_pull_request_from_event,
    extract_issue_number_from_event,
)


def test_extract_issue_comment_payload_fields(tmp_path: Path) -> None:
    payload = """
{
  "action": "created",
  "issue": {
    "number": 42,
    "pull_request": {"url": "https://api.github.com/repos/owner/repo/pulls/42"}
  },
  "comment": {
    "id": 1001,
    "body": "/repobrain ask Where is TKYProvider logic?",
    "user": {"login": "alice"}
  }
}
""".strip()
    event_path = tmp_path / "event.json"
    event_path.write_text(payload, encoding="utf-8")

    assert extract_comment_text_from_event(event_path) == "/repobrain ask Where is TKYProvider logic?"
    assert extract_issue_number_from_event(event_path) == 42
    assert extract_comment_id_from_event(event_path) == 1001
    assert extract_comment_user_login_from_event(event_path) == "alice"
    assert extract_is_pull_request_from_event(event_path) is True

    ctx = extract_event_context_from_event(event_path)
    assert ctx.issue_number == 42
    assert ctx.comment_id == 1001
    assert ctx.comment_user_login == "alice"
    assert ctx.is_pull_request is True
