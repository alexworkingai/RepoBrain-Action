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

    assert "### ✅ Answer" in text
    assert "### 📌 Evidence" in text
    assert "### ✅ Next steps" in text
    assert "### 🧾 Audit summary" in text
