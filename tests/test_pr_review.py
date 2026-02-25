from repobrain.formatting import format_pr_review_comment
from repobrain.review import build_pr_review


def test_build_pr_review_returns_risks_and_next_steps() -> None:
    files = [
        {
            "filename": ".github/workflows/repobrain.yml",
            "status": "modified",
            "additions": 10,
            "deletions": 2,
            "changes": 12,
        },
        {
            "filename": "scripts/run_github.py",
            "status": "modified",
            "additions": 20,
            "deletions": 5,
            "changes": 25,
        },
        {
            "filename": "tests/test_pr_review.py",
            "status": "added",
            "additions": 30,
            "deletions": 0,
            "changes": 30,
        },
    ]

    review = build_pr_review(files)

    assert review["risks"]
    assert review["next_steps"]
    assert review["audit_summary"]["route"] == "REVIEW"


def test_format_pr_review_comment_sections() -> None:
    review = build_pr_review(
        [
            {
                "filename": "pyproject.toml",
                "status": "modified",
                "additions": 1,
                "deletions": 1,
                "changes": 2,
            }
        ]
    )
    text = format_pr_review_comment(review)

    assert "PR Review" in text
    assert "Files changed" in text
    assert "Risks" in text
    assert "Next steps" in text
