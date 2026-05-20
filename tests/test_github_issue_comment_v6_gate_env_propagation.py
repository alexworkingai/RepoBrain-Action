from __future__ import annotations

from pathlib import Path

import yaml

from repobrain.output_md import render_answer_markdown


_ROOT = Path(__file__).resolve().parents[1]


def _load_workflow_yaml() -> dict[str, object]:
    return yaml.safe_load((_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8"))


def _action_step(workflow: dict[str, object]) -> dict[str, object]:
    steps = workflow["jobs"]["repobrain"]["steps"]
    return next(step for step in steps if step.get("uses") == "./.")


def test_gated_issue_comment_passes_topocore_backend_auto_and_local_mode() -> None:
    workflow = _load_workflow_yaml()
    action_step = _action_step(workflow)

    topocore_backend_expr = action_step["with"]["topocore_backend"]
    tky_mode_expr = action_step["with"]["tky_mode"]

    assert "github.event_name == 'issue_comment'" in topocore_backend_expr
    assert "startsWith(github.event.comment.body, '/repobrain')" in topocore_backend_expr
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in topocore_backend_expr
    assert "'auto'" in topocore_backend_expr
    assert "github.event_name == 'issue_comment'" in tky_mode_expr
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in tky_mode_expr
    assert "'local'" in tky_mode_expr


def test_disabled_issue_comment_stays_on_explicitly_blocked_legacy_side_path() -> None:
    workflow = _load_workflow_yaml()
    action_step = _action_step(workflow)
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    topocore_backend_expr = action_step["with"]["topocore_backend"]

    assert "'v5'" in topocore_backend_expr
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1' && 'auto' || 'v5'" in topocore_backend_expr
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1' && 'local' || 'auto'" in action_step["with"]["tky_mode"]
    assert "RB_TOPOCORE_V6_REQUIRE_LOCAL" in workflow_text
    assert "github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '/repobrain') && vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1' && '1'" not in workflow_text


def test_action_default_moves_to_auto_while_workflow_explicitly_overrides_issue_comment() -> None:
    action = yaml.safe_load((_ROOT / "action.yml").read_text(encoding="utf-8"))

    assert action["inputs"]["topocore_backend"]["default"] == "auto"


def test_issue_comment_private_checkout_and_diagnostic_are_gate_only() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]

    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for issue_comment lab run")
    path_step = next(step for step in steps if step.get("name") == "Expose private TopoCore v6 path for issue_comment lab run")
    diag_step = next(step for step in steps if step.get("name") == "Check TopoCore v6 runtime import for issue_comment lab run")

    for condition in (checkout_step["if"], path_step["if"], diag_step["if"]):
        assert "github.event_name == 'issue_comment'" in condition
        assert "startsWith(github.event.comment.body, '/repobrain')" in condition
        assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in condition

    assert diag_step["continue-on-error"] is True


def test_backend_evidence_is_rendered_in_issue_comment_safe_output() -> None:
    markdown = render_answer_markdown(
        answer_text="Backend summary.",
        evidence=[],
        audit_summary={
            "route_final": "FAST",
            "repobrain_version": "test",
            "tkya_backend": "v5",
            "tky_engine": "local",
            "tky_mode_requested": "local",
            "tky_mode_used": "local",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "backend_mode": "auto",
            "fallback_used": False,
            "fallback_reason": "none",
            "retrieved": 0,
            "selected": 0,
            "pass_count": 1,
            "verification_pass_count": 0,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Next",
        command="ask",
    )

    assert "TopoCore backend requested" in markdown
    assert "TopoCore backend resolved" in markdown
    assert "TopoCore fallback used" in markdown
    assert "TopoCore fallback reason" in markdown
    assert "safe-to-merge" not in markdown.lower()
    assert "security-approved" not in markdown.lower()
