from __future__ import annotations

import json
from pathlib import Path

from repobrain.github_flow import get_last_audit, run_github_flow


def _pr_event(tmp_path: Path, body: str) -> Path:
    payload = {
        "issue": {
            "number": 21,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/21"},
        },
        "comment": {"body": body, "id": 10, "user": {"login": "alice"}},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def test_help_output_documents_profile_option(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )
    output = capsys.readouterr().out
    assert status == "DRY_RUN_OK"
    assert "--profile cheap|balanced|premium" in output
    assert "Default is `balanced`" in output
    assert "requested `cheap` may be normalized to `balanced`" in output


def test_invalid_profile_value_fails_safely_with_guidance(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask --profile ultra provider selection",
        issue_number=None,
    )
    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "Invalid profile `ultra`." in output
    assert "Use `/repobrain help` for command examples." in output
    assert audit["route_final"] == "HELP"
    assert audit["command_parse_error_code"] == "invalid_profile_value"


def test_command_profile_overrides_env_and_review_guardrail(tmp_path: Path, monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")
    event_path = _pr_event(tmp_path, "/repobrain review --profile cheap")
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert audit["llm_execution_profile_command_override"] == "cheap"
    assert audit["llm_execution_profile_requested"] == "cheap"
    assert audit["llm_execution_profile_used"] == "balanced"
    assert audit["llm_execution_profile_reason_code"] == "cheap_guardrail_review_fix"
    assert audit["llm_profile_policy_outcome"] == "guardrail_override_to_balanced"
    assert audit["llm_profile_override_applied"] is True


def test_env_profile_used_when_command_profile_absent(tmp_path: Path, monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")
    event_path = _pr_event(tmp_path, "/repobrain review")
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert audit["llm_execution_profile_command_override"] == "none"
    assert audit["llm_execution_profile_requested"] == "premium"
    assert audit["llm_execution_profile_used"] == "premium"
    assert audit["llm_profile_policy_outcome"] == "profile_applied"


def test_balanced_default_when_no_command_profile_and_no_env(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("RB_LLM_EXECUTION_PROFILE", raising=False)
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Where is provider selection implemented?",
        issue_number=None,
    )
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert audit["llm_execution_profile_command_override"] == "none"
    assert audit["llm_execution_profile_requested"] == "balanced"
    assert audit["llm_execution_profile_used"] == "balanced"


def test_fix_profile_cheap_preserves_requested_and_guardrail_in_no_patch_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("RB_LLM_EXECUTION_PROFILE", raising=False)
    event_path = _pr_event(tmp_path, "/repobrain fix --profile cheap tighten null checks")
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert audit["llm_skip_reason"] == "no_localized_patch_target"
    assert audit["patch_generation_result"] == "no_patch"
    assert audit["llm_execution_profile_command_override"] == "cheap"
    assert audit["llm_execution_profile_requested"] == "cheap"
    assert audit["llm_execution_profile_used"] == "balanced"
    assert audit["llm_execution_profile_reason_code"] == "cheap_guardrail_review_fix"
    assert audit["llm_profile_policy_outcome"] == "guardrail_override_to_balanced"
    assert audit["llm_profile_override_applied"] is True
    assert audit["llm_adapter_execution_profile_requested"] == "cheap"
    assert audit["llm_adapter_execution_profile_used"] == "balanced"
    assert audit["llm_adapter_execution_profile_reason_code"] == "cheap_guardrail_review_fix"
    assert audit["llm_adapter_profile_policy_outcome"] == "guardrail_override_to_balanced"
    assert audit["llm_adapter_profile_override_applied"] is True


def test_ask_profile_cheap_remains_cheap_when_guardrail_not_applicable() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask --profile cheap Where is provider selection implemented?",
        issue_number=None,
    )
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert audit["llm_execution_profile_command_override"] == "cheap"
    assert audit["llm_execution_profile_requested"] == "cheap"
    assert audit["llm_execution_profile_used"] == "cheap"
