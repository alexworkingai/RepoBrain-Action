from repobrain.links import make_line_link


def test_make_line_link_absolute() -> None:
    value = make_line_link(
        "owner/repo",
        "abc123",
        "repobrain/tky_provider.py",
        1,
        10,
    )
    assert "https://github.com/owner/repo/blob/abc123/repobrain/tky_provider.py#L1-L10" in value
    assert "repobrain/tky_provider.py:L1-L10" in value


def test_make_line_link_relative() -> None:
    value = make_line_link(None, None, "repobrain/tky_provider.py", 2, 3)
    assert "(repobrain/tky_provider.py#L2-L3)" in value
