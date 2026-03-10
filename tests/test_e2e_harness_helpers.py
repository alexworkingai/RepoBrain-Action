from importlib.util import module_from_spec, spec_from_file_location
import json
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


def test_commit_and_push_stages_deletions_with_add_all(monkeypatch) -> None:
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
                return module.CmdResult(code=0, out=" D e2e_marker_123.txt", err="")
            return module.CmdResult(
                code=0,
                out="A  scripts/e2e/marker_bad.py\nD  e2e_marker_123.txt",
                err="",
            )
        return module.CmdResult(code=0, out="", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    module._commit_and_push([Path("scripts/e2e/marker_bad.py")], "e2e: marker", "test-branch")  # noqa: SLF001

    add_all_idx = next(i for i, call in enumerate(calls) if call == ["git", "add", "-A"])
    commit_idx = next(i for i, call in enumerate(calls) if call[:2] == ["git", "commit"])
    assert add_all_idx < commit_idx


def test_clean_e2e_markers_issues_safe_commands(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.chdir(tmp_path)

    marker_a = tmp_path / "e2e_marker_1.txt"
    marker_b = tmp_path / "e2e_marker_2.txt"
    keep_file = tmp_path / "keep.txt"
    marker_a.write_text("marker-a", encoding="utf-8")
    marker_b.write_text("marker-b", encoding="utf-8")
    keep_file.write_text("keep", encoding="utf-8")

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

    module._clean_e2e_markers("e2e/test-branch")  # noqa: SLF001

    assert not marker_a.exists()
    assert not marker_b.exists()
    assert keep_file.exists()
    assert ["git", "rm", "-f", "--cached", "--", "e2e_marker_*.txt"] in calls
    assert ["git", "add", "-A"] in calls
    assert not any(call[:2] == ["git", "commit"] for call in calls)


def test_gh_retry_on_tls_timeout(monkeypatch) -> None:
    module = _load_module()
    calls: list[list[str]] = []
    responses = [
        module.CmdResult(code=1, out="", err="TLS handshake timeout"),
        module.CmdResult(code=0, out="[]", err=""),
    ]
    sleeps: list[int] = []

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del cwd, check
        calls.append(args)
        return responses.pop(0)

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(int(seconds)))

    result, attempts = module._run_gh_cmd_with_retries(  # noqa: SLF001
        ["gh", "run", "list"],
        retries=3,
        backoff_s=2,
        check=True,
    )

    assert result.code == 0
    assert attempts == 2
    assert sleeps == [2]
    assert len(calls) == 2


def test_fix_scenario_toggles_include_allow_dynamic_verify() -> None:
    module = _load_module()
    scenarios = module._build_scenarios(  # noqa: SLF001
        require_llm_used=True,
        require_embeddings_used=True,
        require_patch=True,
        require_batch_calls_min=2,
    )
    fix_spec = next(item for item in scenarios if item.name == "fix_patch_required_dispatch")
    assert fix_spec.allow_dynamic_verify is True


def test_build_marker_file_path_under_markers_dir() -> None:
    module = _load_module()
    marker = module._build_marker_file_path(12345)  # noqa: SLF001
    assert marker.as_posix() == "scripts/e2e/_markers/e2e_marker_12345.txt"


def test_create_temp_pr_stages_marker_from_markers_dir(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    monkeypatch.chdir(tmp_path)
    calls: list[list[str]] = []

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del cwd, check
        calls.append(args)
        if args[:3] == ["git", "check-ignore", "--quiet"]:
            return module.CmdResult(code=1, out="", err="")
        if args[:4] == ["gh", "pr", "create", "--base"]:
            return module.CmdResult(code=0, out="https://example.test/pr/42", err="")
        if args[:3] == ["gh", "pr", "view"]:
            payload = {"number": 42, "url": "https://example.test/pr/42"}
            return module.CmdResult(code=0, out=json.dumps(payload), err="")
        return module.CmdResult(code=0, out="", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    marker = module._build_marker_file_path(999)  # noqa: SLF001
    pr_number, pr_url = module._create_temp_pr(  # noqa: SLF001
        repo="owner/repo",
        default_branch="main",
        branch="e2e/test",
        marker_file=marker,
    )

    assert pr_number == "42"
    assert pr_url == "https://example.test/pr/42"
    assert marker.exists()
    assert marker.parent.as_posix() == "scripts/e2e/_markers"
    assert ["git", "add", "--", marker.as_posix()] in calls


def test_assert_marker_path_not_ignored(monkeypatch) -> None:
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
        if args[:3] == ["git", "check-ignore", "--quiet"]:
            return module.CmdResult(code=1, out="", err="")
        return module.CmdResult(code=0, out="", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    module._assert_marker_path_not_ignored(Path("scripts/e2e/_markers/e2e_marker_1.txt"))  # noqa: SLF001
    assert ["git", "check-ignore", "--quiet", "scripts/e2e/_markers/e2e_marker_1.txt"] in calls


def test_download_artifacts_transient_then_success(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    responses = [
        module.CmdResult(code=1, out="", err="TLS handshake timeout"),
        module.CmdResult(code=0, out="ok", err=""),
    ]
    sleeps: list[float] = []

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del args, cwd, check
        return responses.pop(0)

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)
    monkeypatch.setattr(module.random, "uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(float(seconds)))

    ok, msg = module._download_artifacts(  # noqa: SLF001
        "owner/repo",
        "123",
        tmp_path / "artifacts",
        retries=3,
        backoff_s=2,
    )

    assert ok is True
    assert "attempts=2" in msg
    assert sleeps == [2.0]


def test_scenario_classified_infra_when_download_totally_fails(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()

    monkeypatch.setattr(
        module,
        "_dispatch_run",
        lambda **_kwargs: (
            {"databaseId": "321", "url": "https://example.test/run/321", "conclusion": "success"},
            "",
        ),
    )
    monkeypatch.setattr(module, "_download_artifacts", lambda *args, **kwargs: (False, "network down"))  # noqa: ANN001
    monkeypatch.setattr(
        module,
        "_collect_run_fallback_diagnostics",
        lambda **_kwargs: {
            "run_view_path": "tmp/run_view.json",
            "run_log_path": "tmp/run_log.txt",
            "log_markers": [],
            "artifact_evidence_hits": [],
            "upload_likely": False,
            "notes": [],
        },
    )

    spec = module.ScenarioSpec(
        name="fix_patch_required_dispatch",
        command="/repobrain fix quick change",
        enable_llm=True,
        enable_embeddings=False,
        enable_batch_llm=False,
        batch_force=False,
        trusted_context=True,
        allow_dynamic_verify=True,
        apply_patch=False,
        create_pr=False,
        requirements=module.ScenarioRequirements(require_patch=True),
    )

    result = module._scenario_dispatch_command(  # noqa: SLF001
        repo="owner/repo",
        workflow="repobrain.yml",
        branch="e2e/test",
        pr_number="12",
        spec=spec,
        artifacts_dir=tmp_path,
        timeout_s=60,
        gh_retries=2,
        gh_backoff_s=1,
        artifact_download_retries=3,
        artifact_download_backoff_s=1,
    )

    assert result.status == "FAIL_INFRA"
    assert any("artifact_transport_failure=true" in note for note in result.notes)


def test_fix_scenario_warn_with_run_view_log_when_upload_likely(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()

    monkeypatch.setattr(
        module,
        "_dispatch_run",
        lambda **_kwargs: (
            {"databaseId": "654", "url": "https://example.test/run/654", "conclusion": "success"},
            "",
        ),
    )
    monkeypatch.setattr(module, "_download_artifacts", lambda *args, **kwargs: (False, "TLS timeout"))  # noqa: ANN001
    monkeypatch.setattr(
        module,
        "_collect_run_fallback_diagnostics",
        lambda **_kwargs: {
            "run_view_path": "tmp/run_view.json",
            "run_log_path": "tmp/run_log.txt",
            "log_markers": ["artifacts/patch.diff"],
            "artifact_evidence_hits": ["repobrain-patch"],
            "upload_likely": True,
            "notes": [],
        },
    )

    spec = module.ScenarioSpec(
        name="fix_patch_required_dispatch",
        command="/repobrain fix quick change",
        enable_llm=True,
        enable_embeddings=False,
        enable_batch_llm=False,
        batch_force=False,
        trusted_context=True,
        allow_dynamic_verify=True,
        apply_patch=False,
        create_pr=False,
        requirements=module.ScenarioRequirements(require_patch=True),
    )

    result = module._scenario_dispatch_command(  # noqa: SLF001
        repo="owner/repo",
        workflow="repobrain.yml",
        branch="e2e/test",
        pr_number="12",
        spec=spec,
        artifacts_dir=tmp_path,
        timeout_s=60,
        gh_retries=2,
        gh_backoff_s=1,
        artifact_download_retries=3,
        artifact_download_backoff_s=1,
    )

    assert result.status == "WARN"
    assert any("run_view_path=tmp/run_view.json" in note for note in result.notes)
    assert any("run_log_path=tmp/run_log.txt" in note for note in result.notes)
    assert any("artifact upload likely succeeded" in note for note in result.notes)


def test_fix_scenario_rate_limited_classified_as_infra(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    artifacts_root = tmp_path / "fix429"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    (artifacts_root / "config_snapshot.json").write_text('{"config":{"safe":true}}', encoding="utf-8")
    (artifacts_root / "ai_quota_snapshot.json").write_text('{"governor":{"ok":true}}', encoding="utf-8")
    (artifacts_root / "llm_usage.json").write_text(
        json.dumps(
            {
                "llm_used": False,
                "skip_reason": "LLM_NOT_AVAILABLE:rate_limited",
                "decision_route": "FAST",
                "provider_http_status": 429,
                "provider_error_type": "rate_limited",
                "effective_model_id": "openai/gpt-4.1-mini",
                "fallback_used": True,
            }
        ),
        encoding="utf-8",
    )
    (artifacts_root / "llm_http_debug.json").write_text(
        json.dumps(
            {
                "provider_http_status": 429,
                "provider_error_type": "rate_limited",
                "fallback_model": "openai/gpt-4.1-mini",
            }
        ),
        encoding="utf-8",
    )
    (artifacts_root / "patch_generation_debug.json").write_text(
        '{"reason":"diff_not_found_in_engine_or_llm_output"}',
        encoding="utf-8",
    )

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del args, cwd, check
        return module.CmdResult(code=0, out="ok", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    result = module._scenario_from_run(  # noqa: SLF001
        scenario_name="fix_patch_required_dispatch",
        trigger="/repobrain fix",
        run_data={"databaseId": "1", "url": "https://example.test/run/1", "conclusion": "success"},
        artifacts_root=artifacts_root,
        requirements=module.ScenarioRequirements(require_patch=True),
    )

    assert result.status == "FAIL_INFRA"
    assert any("classified as FAIL_INFRA due to provider rate limit (429)" in note for note in result.notes)
    assert any("effective_model_id=openai/gpt-4.1-mini" in note for note in result.notes)


def test_fix_scenario_llm_used_but_no_patch_is_product_fail(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    artifacts_root = tmp_path / "fix-product-fail"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    (artifacts_root / "config_snapshot.json").write_text('{"config":{"safe":true}}', encoding="utf-8")
    (artifacts_root / "ai_quota_snapshot.json").write_text('{"governor":{"ok":true}}', encoding="utf-8")
    (artifacts_root / "llm_usage.json").write_text(
        json.dumps(
            {
                "llm_used": True,
                "skip_reason": "n/a",
                "decision_route": "FAST",
                "provider_http_status": None,
                "provider_error_type": "n/a",
                "effective_model_id": "openai/gpt-4.1",
                "fallback_used": False,
            }
        ),
        encoding="utf-8",
    )
    (artifacts_root / "patch_generation_debug.json").write_text(
        '{"reason":"diff_not_found_in_engine_or_llm_output"}',
        encoding="utf-8",
    )

    def fake_run_cmd(
        args: list[str],
        *,
        cwd: Path | None = None,
        check: bool = True,
    ):
        del args, cwd, check
        return module.CmdResult(code=0, out="ok", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    result = module._scenario_from_run(  # noqa: SLF001
        scenario_name="fix_patch_required_dispatch",
        trigger="/repobrain fix",
        run_data={"databaseId": "2", "url": "https://example.test/run/2", "conclusion": "success"},
        artifacts_root=artifacts_root,
        requirements=module.ScenarioRequirements(require_patch=True),
    )

    assert result.status == "FAIL_PRODUCT"


def test_scenario_order_places_fix_before_batch() -> None:
    module = _load_module()
    scenarios = module._build_scenarios(  # noqa: SLF001
        require_llm_used=True,
        require_embeddings_used=True,
        require_patch=True,
        require_batch_calls_min=2,
    )
    names = [item.name for item in scenarios]
    assert names == [
        "review_dispatch",
        "fix_patch_required_dispatch",
        "llm_used_dispatch",
        "embeddings_warmup_dispatch",
        "embeddings_used_dispatch",
        "batch_llm_dispatch",
    ]
