from repobrain.formatting import format_github_comment


def test_local_formatting_uses_remote_tky_label_and_local_audit_note(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    text = format_github_comment(
        "Answer body",
        [],
        {
            "tky_engine": "remote",
            "tky_mode_used": "remote",
            "remote_used": True,
            "fallback_reason_code": None,
        },
        "Open evidence links and verify logic",
    )

    assert "TKY: remote (ok)" in text
    assert "Audit: local run (no workflow artifacts)." in text
    assert "Audit: workflow artifact `repobrain-audit` (hash-only)." not in text


def test_local_formatting_uses_topocore_v5_label(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    text = format_github_comment(
        "Answer body",
        [],
        {
            "tky_engine": "topocore_v5",
            "tky_mode_used": "local",
            "remote_used": False,
        },
        "Open evidence links and verify logic",
    )

    assert "TKY: topocore_v5" in text
    assert "Audit: local run (no workflow artifacts)." in text
