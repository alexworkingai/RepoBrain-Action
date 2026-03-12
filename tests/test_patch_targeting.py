from __future__ import annotations

from repobrain.patch_targeting import select_patch_targets


def test_broad_pr_without_localized_evidence_returns_no_patch_target() -> None:
    files = [
        {
            "filename": "docs/architecture.md",
            "status": "modified",
            "changes": 240,
            "patch": "@@ -1,2 +1,2 @@\n-old\n+new",
        },
        {
            "filename": ".github/workflows/ci.yml",
            "status": "modified",
            "changes": 480,
            "patch": "@@ -3,4 +3,4 @@\n-old\n+new",
        },
    ]
    targeting = select_patch_targets(
        files=files,
        review={"risk_items": []},
        query="apply broad cleanup",
        max_target_files=5,
        max_target_hunks=12,
        require_localized_evidence=True,
    )

    assert targeting["patch_target_files_selected"] == 0
    assert targeting["patch_targeting_mode"] == "none"
    assert targeting["patch_targeting_reason"] == "no_localized_evidence_backed_patch_target"


def test_localized_issue_selects_narrow_target_subset_with_caps() -> None:
    files = [
        {
            "filename": "repobrain/github_flow.py",
            "status": "modified",
            "changes": 90,
            "patch": "@@ -10,3 +10,4 @@\n-a\n+b\n@@ -50,2 +50,3 @@\n-x\n+y",
        },
        {
            "filename": "repobrain/output_md.py",
            "status": "modified",
            "changes": 60,
            "patch": "@@ -100,2 +100,3 @@\n-a\n+b",
        },
        {
            "filename": "docs/notes.md",
            "status": "modified",
            "changes": 40,
            "patch": "@@ -1 +1 @@\n-a\n+b",
        },
    ]
    review = {
        "risk_items": [
            {
                "message": "Merge conflict markers present",
                "severity": "high",
                "evidence": [
                    {
                        "kind": "file_path",
                        "path": "repobrain/github_flow.py",
                        "source": "path_rule",
                    }
                ],
            }
        ]
    }
    targeting = select_patch_targets(
        files=files,
        review=review,
        query="fix github_flow conflict markers",
        max_target_files=1,
        max_target_hunks=1,
        require_localized_evidence=True,
    )

    assert targeting["patch_target_files_total"] == 3
    assert targeting["patch_target_files_selected"] == 1
    assert targeting["patch_target_hunks_selected"] == 1
    assert targeting["patch_targeting_mode"] in {"localized", "localized_capped"}
    assert targeting["selected_files"] == ["repobrain/github_flow.py"]
    assert targeting["localized_patch_evidence_count"] >= 1
