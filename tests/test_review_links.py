from repobrain.review import build_pr_review


def test_build_pr_review_generates_links_from_repo_and_sha() -> None:
    report = build_pr_review(
        [
            {
                "filename": "repobrain/review.py",
                "status": "modified",
                "additions": 10,
                "deletions": 2,
            }
        ],
        head_sha="deadbeef",
        repo="owner/repo",
    )

    files_changed = report["files_changed"]
    assert files_changed
    assert files_changed[0]["link"] == "https://github.com/owner/repo/blob/deadbeef/repobrain/review.py"
    assert any("https://github.com/owner/repo/blob/deadbeef/repobrain/review.py" in line for line in report["files_block"])
