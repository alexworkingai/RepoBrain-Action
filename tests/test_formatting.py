from repobrain.evidence import EvidenceItem
from repobrain.formatting import format_github_comment


def test_format_github_comment_has_required_sections() -> None:
    text = format_github_comment(
        "Answer body",
        [
            EvidenceItem(
                file_path="repobrain/ask.py",
                line_start=1,
                line_end=10,
                score=0.9,
            )
        ],
        {"retrieved": 10, "selected": 2, "route": "FAST"},
        "Open evidence links and verify logic",
    )

    assert "Answer" in text
    assert "Evidence" in text
    assert "Next steps" in text
    assert "Audit summary" in text
    assert "score=0.9000" in text


def test_format_github_comment_locate_omits_answer_section() -> None:
    text = format_github_comment(
        "",
        [
            EvidenceItem(
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=10,
                score=0.1234,
            )
        ],
        {"route": "FAST"},
        "",
        command="locate",
    )

    assert "Evidence" in text
    assert "Audit summary" in text
    assert "Answer" not in text
    assert "Next steps" not in text
