from __future__ import annotations

from pathlib import Path

import repobrain.github_flow as gf


class _FakeClient:
    def __init__(self) -> None:
        self.repo = "owner/repo"
        self.token = "token"


def test_publish_pr_check_run_uses_command_specific_names(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def _fake_publish_check_run(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(dict(kwargs))
        return {"ok": True, "status_code": 201}

    monkeypatch.setattr(gf, "publish_check_run", _fake_publish_check_run)

    for cmd in ("ask", "review", "fix"):
        audit = {
            "route_final": "FAST",
            "check_intent": "analysis" if cmd == "ask" else ("review" if cmd == "review" else "patch"),
            "verification_report": {"overall": "NOT_RUN", "checks": []},
            "pr_head_sha": "abc123",
        }
        gf._publish_pr_check_run(
            repo_root=tmp_path,
            client=_FakeClient(),
            cmd=cmd,
            issue_number=7,
            body_markdown="body",
            audit=audit,
            github_context_seed={"head_sha": "abc123"},
        )
        assert audit["check_run_published"] is True
        assert audit["check_run_name"].startswith("RepoBrain")

    assert len(calls) == 3
    assert {str(item["name"]) for item in calls} == {"RepoBrain Ask", "RepoBrain Review", "RepoBrain Fix"}


def test_publish_pr_check_run_sets_skip_reason_when_head_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gf, "_resolve_pr_head_sha", lambda **_: "")
    audit = {"route_final": "FAST", "check_intent": "analysis", "verification_report": {"overall": "NOT_RUN"}}

    gf._publish_pr_check_run(
        repo_root=tmp_path,
        client=_FakeClient(),
        cmd="ask",
        issue_number=3,
        body_markdown="body",
        audit=audit,
        github_context_seed={},
    )

    assert audit["check_run_published"] is False
    assert audit["check_run_skip_reason"] == "head_sha_missing"


def test_repobrain_workflow_allows_check_run_publication() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")
    assert "checks: write" in workflow
