from repobrain.review import build_pr_review


def test_review_patch_scan_detects_merge_conflicts_as_high_risk() -> None:
    files = [
        {
            "filename": "repobrain/github_flow.py",
            "status": "modified",
            "additions": 5,
            "deletions": 1,
            "patch": "@@ -1,1 +1,5 @@\n<<<<<<< HEAD\nfoo\n=======\nbar\n>>>>>>> branch\n",
        }
    ]
    report = build_pr_review(files, head_sha="abc123", repo="owner/repo")

    assert report["risk_level"] == "high"
    assert any("Merge conflict markers" in item for item in report["risks"])
    assert report["suggested_tests"][0] == "Resolve merge conflict markers and re-run /repobrain review"


def test_review_patch_scan_docs_security_wording_is_not_secret_leak_high() -> None:
    files = [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 3,
            "deletions": 1,
            "patch": "@@ -1,2 +1,3 @@\n+Please do not share secrets or system prompt details.\n",
        }
    ]
    report = build_pr_review(files, head_sha="abc123", repo="owner/repo")

    assert not any("secret leakage" in item.lower() for item in report["risks"])
    assert any("security-related wording" in note.lower() for note in report["notes"])


def test_review_patch_scan_detects_private_key_marker() -> None:
    files = [
        {
            "filename": "config/secrets.txt",
            "status": "modified",
            "additions": 2,
            "deletions": 0,
            "patch": "+BEGIN PRIVATE KEY\n+abc\n",
        }
    ]
    report = build_pr_review(files, head_sha="abc123", repo="owner/repo")

    assert report["risk_level"] == "high"
    assert any("secret leakage" in item.lower() for item in report["risks"])


def test_review_patch_scan_detects_token_assignment_pattern() -> None:
    files = [
        {
            "filename": "config/app.env",
            "status": "modified",
            "additions": 1,
            "deletions": 0,
            "patch": "+API_KEY='abcd1234zzzz'\n",
        }
    ]
    report = build_pr_review(files, head_sha="abc123", repo="owner/repo")

    assert report["risk_level"] == "high"
    assert any("secret leakage" in item.lower() for item in report["risks"])
