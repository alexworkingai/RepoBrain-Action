from repobrain.output_md import render_status_markdown


def test_status_uses_partner_friendly_runtime_wording_by_default() -> None:
    md = render_status_markdown(
        report={
            "version": "0.0.0",
            "repo_name": "owner/repo",
            "event_context": "issue",
            "supported_commands": [],
            "topocore_policy": ["v6-only runtime policy", "no v5 fallback"],
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
    assert "Partner-preferred path: installed private package." in md
    assert "Installed-package proof: passed." in md
    assert "TopoCore source: private and not exposed" in md
    assert "TopoCore runtime mode requested:" not in md
