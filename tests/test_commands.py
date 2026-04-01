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


def test_parse_fix_with_optional_text() -> None:
    assert parse_command("/repobrain fix") == {"cmd": "fix", "query": ""}
    assert parse_command("/repobrain fix tighten null checks") == {
        "cmd": "fix",
        "query": "tighten null checks",
    }


def test_parse_ask_with_profile_flag() -> None:
    assert parse_command("/repobrain ask --profile cheap provider selection") == {
        "cmd": "ask",
        "query": "provider selection",
        "profile": "cheap",
    }


def test_parse_review_with_profile_flag() -> None:
    assert parse_command("/repobrain review --profile premium") == {
        "cmd": "review",
        "query": "",
        "profile": "premium",
    }


def test_parse_fix_with_profile_flag_and_query() -> None:
    assert parse_command("/repobrain fix --profile balanced tighten null checks") == {
        "cmd": "fix",
        "query": "tighten null checks",
        "profile": "balanced",
    }


def test_parse_invalid_profile_value_returns_parse_error() -> None:
    parsed = parse_command("/repobrain ask --profile ultra provider selection")
    assert parsed["cmd"] == "ask"
    assert "provider selection" in parsed["query"]
    assert parsed["error_code"] == "invalid_profile_value"
    assert "Allowed values" in parsed["error_message"]
