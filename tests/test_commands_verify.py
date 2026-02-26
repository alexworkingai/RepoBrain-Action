from repobrain.commands import parse_command


def test_parse_verify_without_text() -> None:
    assert parse_command("/repobrain verify") == {"cmd": "verify", "query": ""}


def test_parse_verify_ignores_extra_text() -> None:
    assert parse_command("/repobrain verify please check ci") == {"cmd": "verify", "query": ""}
