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


def test_missing_filename_entries_are_skipped() -> None:
    files = [
        {
            "filename": "",
            "status": "modified",
            "changes": 20,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
        {
            "status": "modified",
            "changes": 20,
            "patch": "@@ -3 +3 @@\n-old\n+new",
        },
        {
            "filename": "repobrain/patch_targeting.py",
            "status": "modified",
            "changes": 20,
            "patch": "@@ -10 +10 @@\n-old\n+new",
        },
    ]

    targeting = select_patch_targets(
        files=files,
        review={"risk_items": []},
        query="patch_targeting.py",
        max_target_files=3,
        max_target_hunks=4,
        require_localized_evidence=False,
    )

    assert targeting["patch_target_files_total"] == 1
    assert targeting["patch_target_files_selected"] == 1
    assert targeting["selected_files"] == ["repobrain/patch_targeting.py"]
    assert [item["path"] for item in targeting["ranked_targets"]] == ["repobrain/patch_targeting.py"]


def test_competing_code_targets_without_localized_signals_remain_no_patch() -> None:
    files = [
        {
            "filename": "repobrain/patch_targeting.py",
            "status": "modified",
            "changes": 120,
            "patch": "@@ -10,2 +10,3 @@\n-a\n+b",
        },
        {
            "filename": "repobrain/patch_validator.py",
            "status": "modified",
            "changes": 110,
            "patch": "@@ -20,2 +20,3 @@\n-a\n+b",
        },
    ]

    targeting = select_patch_targets(
        files=files,
        review={"risk_items": [], "confirmed_risk_items": []},
        query="apply broad cleanup",
        max_target_files=2,
        max_target_hunks=6,
        require_localized_evidence=True,
    )

    assert targeting["patch_target_files_total"] == 2
    assert targeting["patch_target_files_selected"] == 0
    assert targeting["patch_targeting_mode"] == "none"
    assert targeting["patch_targeting_reason"] == "no_localized_evidence_backed_patch_target"
    assert targeting["localized_patch_evidence_count"] == 0
    assert targeting["selected_files"] == []


def test_equal_rank_localized_targets_are_selected_deterministically_by_path() -> None:
    files = [
        {
            "filename": "repobrain/z_last.py",
            "status": "modified",
            "changes": 40,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
        {
            "filename": "repobrain/a_first.py",
            "status": "modified",
            "changes": 40,
            "patch": "@@ -1 +1 @@\n-old\n+new",
        },
    ]
    review = {
        "confirmed_risk_items": [
            {
                "message": "Two files have equally localized evidence",
                "severity": "medium",
                "evidence_paths": ["repobrain/z_last.py", "repobrain/a_first.py"],
            }
        ]
    }

    targeting = select_patch_targets(
        files=files,
        review=review,
        query="",
        max_target_files=1,
        max_target_hunks=4,
        require_localized_evidence=True,
    )

    assert targeting["patch_target_files_selected"] == 1
    assert targeting["selected_files"] == ["repobrain/a_first.py"]
    assert [item["path"] for item in targeting["ranked_targets"][:2]] == [
        "repobrain/a_first.py",
        "repobrain/z_last.py",
    ]
