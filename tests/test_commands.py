from repobrain.commands import parse_command


def test_parse_help() -> None:
    assert parse_command("/repobrain help") == {"cmd": "help", "query": ""}


def test_parse_ask_with_text() -> None:
    assert parse_command("/repobrain ask provider selection") == {
        "cmd": "ask",
        "query": "provider selection",
    }


def test_parse_incomplete_returns_help() -> None:
    assert parse_command("/repobrain explain") == {"cmd": "help", "query": ""}


def test_parse_review_without_text() -> None:
    assert parse_command("/repobrain review") == {"cmd": "review", "query": ""}
