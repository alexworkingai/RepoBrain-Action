from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "e2e" / "run_e2e_suite.py"
    spec = spec_from_file_location("repobrain_e2e_suite", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_repo_slug_variants() -> None:
    module = _load_module()
    assert module.parse_repo_slug("https://github.com/owner/repo.git") == "owner/repo"
    assert module.parse_repo_slug("git@github.com:owner/repo.git") == "owner/repo"
    assert module.parse_repo_slug("ssh://git@github.com/owner/repo.git") == "owner/repo"


def test_report_writer_contains_table() -> None:
    module = _load_module()
    result = module.ScenarioResult(
        name="review",
        trigger="/repobrain review",
        status="PASS",
        run_id="123",
        run_url="https://example.test/run/123",
        conclusion="success",
        notes=["ok"],
        artifact_dir="artifacts/e2e/review/123",
    )
    md = module.render_report_markdown(
        repo="owner/repo",
        pr_url="https://example.test/pr/1",
        results=[result],
    )
    assert "| Scenario | Trigger | Result | Conclusion | Run |" in md
    assert "RepoBrain E2E Report" in md
    assert "**PASS**" in md


def test_build_workflow_dispatch_args_includes_e2e_payload() -> None:
    module = _load_module()
    args = module._build_workflow_dispatch_args(  # noqa: SLF001
        workflow="repobrain.yml",
        ref="feature/test",
        enable_llm=False,
        enable_embeddings=False,
        enable_batch_llm=False,
        batch_force=False,
        trusted_context=False,
        allow_dynamic_verify=False,
        apply_patch=False,
        create_pr=False,
        e2e_command="/repobrain review",
        e2e_pr_number="123",
        e2e_ref="feature/test",
    )
    joined = " ".join(args)
    assert "e2e_command=/repobrain review" in joined
    assert "e2e_pr_number=123" in joined
    assert "e2e_ref=feature/test" in joined


def test_commit_and_push_skips_when_no_changes(monkeypatch) -> None:
    module = _load_module()
    calls: list[list[str]] = []

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del cwd, check
        calls.append(args)
        if args == ["git", "status", "--porcelain"]:
            return module.CmdResult(code=0, out="", err="")
        return module.CmdResult(code=0, out="", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    module._commit_and_push([Path("scripts/e2e/marker_bad.py")], "e2e: marker", "test-branch")  # noqa: SLF001

    assert any(call[:2] == ["git", "add"] for call in calls)
    assert not any(call[:2] == ["git", "commit"] for call in calls)
    assert not any(call[:2] == ["git", "push"] for call in calls)


def test_commit_and_push_stages_before_commit(monkeypatch) -> None:
    module = _load_module()
    calls: list[list[str]] = []
    status_counter = {"value": 0}

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del cwd, check
        calls.append(args)
        if args == ["git", "status", "--porcelain"]:
            status_counter["value"] += 1
            if status_counter["value"] == 1:
                return module.CmdResult(code=0, out="?? scripts/e2e/marker_bad.py", err="")
            return module.CmdResult(code=0, out="A  scripts/e2e/marker_bad.py", err="")
        return module.CmdResult(code=0, out="", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    module._commit_and_push([Path("scripts/e2e/marker_bad.py")], "e2e: marker", "test-branch")  # noqa: SLF001

    add_idx = next(i for i, call in enumerate(calls) if call[:2] == ["git", "add"])
    commit_idx = next(i for i, call in enumerate(calls) if call[:2] == ["git", "commit"])
    push_idx = next(i for i, call in enumerate(calls) if call[:2] == ["git", "push"])

    assert add_idx < commit_idx < push_idx
