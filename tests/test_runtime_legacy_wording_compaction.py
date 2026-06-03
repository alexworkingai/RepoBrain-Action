from repobrain.output_md import render_doctor_markdown, render_status_markdown


def test_status_default_uses_partner_wording_without_legacy_repetition() -> None:
    md = render_status_markdown(
        report={
            "version": "0.0.0",
            "repo_name": "owner/repo",
            "event_context": "issue",
            "supported_commands": [],
            "topocore_policy": [],
            "safety_policy": ["no patch/autofix"],
            "install_hints": [],
            "workflow": {"exists": True, "permissions_explicit": True, "read_mostly_baseline": True},
            "action_runtime_mode": "issue_comment",
            "topocore_dependency_mode": "private_checkout_beta_only",
            "topocore_runtime_mode_requested": "private_checkout",
            "topocore_runtime_mode_effective": "private_checkout",
            "installed_package_proof_status": "passed",
        },
        audit_summary={"command": "status", "route_final": "STATUS"},
    )

    assert "Private runtime boundary: configured." in md
    assert "Current run: controlled private runtime path." in md
    assert "Installed-package proof: passed." in md
    assert "No v5 or legacy community dependency." not in md
    assert "TopoCore runtime mode requested:" not in md


def test_doctor_default_uses_partner_wording_without_raw_runtime_block() -> None:
    md = render_doctor_markdown(
        report={
            "overall_status": "PASS_WITH_NOTES",
            "repo_name": "owner/repo",
            "event_context": "issue",
            "checks": [],
            "issues_found": [],
            "recommended_fixes": [],
            "limitations": [],
            "topocore_dependency_mode": "private_checkout_beta_only",
            "topocore_runtime_mode_requested": "private_checkout",
            "topocore_runtime_mode_effective": "private_checkout",
            "installed_package_proof_status": "passed",
        },
        audit_summary={"command": "doctor", "route_final": "DOCTOR"},
    )

    assert "Private runtime boundary: configured." in md
    assert "Current run: controlled private runtime path." in md
    assert "Installed-package proof: passed." in md
    assert "TopoCore runtime mode requested:" not in md

