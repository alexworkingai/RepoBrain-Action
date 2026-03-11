from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "e2e" / "run_e2e_suite.py"
    spec = spec_from_file_location("repobrain_e2e_suite_requirements", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_base_artifacts(root: Path) -> None:
    _write_json(root / "config_snapshot.json", {"config": {"safe": True}})
    _write_json(root / "ai_quota_snapshot.json", {"governor": {"ok": True}})


def test_validate_artifacts_fails_when_patch_missing(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    requirements = module.ScenarioRequirements(require_patch=True)

    status, notes = module.validate_artifacts("fix_patch_required_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("patch artifact missing" in note for note in notes)


def test_validate_artifacts_fails_when_llm_required_but_not_used(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": False,
            "model_id": "not used",
            "skip_reason": "route=WAIT",
            "decision_route": "WAIT",
            "tokens_total": 0,
            "remaining_requests": 10,
            "reset_time_utc_iso": None,
            "totals": {"calls_count": 0},
        },
    )
    requirements = module.ScenarioRequirements(require_llm_used=True)

    status, notes = module.validate_artifacts("llm_used_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("llm_used must be true" in note for note in notes)
    assert any("skip_reason=route=WAIT" in note for note in notes)


def test_validate_artifacts_fails_when_batch_calls_below_threshold(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": True,
            "model_id": "openai/gpt-4.1-mini",
            "tokens_total": 120,
            "remaining_requests": 5,
            "reset_time_utc_iso": "2026-01-01T00:00:00Z",
            "calls": [{"batch_id": "b1", "tokens_total": 120}],
            "totals": {"calls_count": 1},
        },
    )
    requirements = module.ScenarioRequirements(require_batch_calls_min=2)

    status, notes = module.validate_artifacts("batch_llm_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("calls_count=1 is below required 2" in note for note in notes)


def test_embeddings_evidence_accepts_ok_partial(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "embeddings_usage.json",
        {
            "embed_used": True,
            "query_embedded": True,
            "remaining_requests": 7,
            "reset_time_utc_iso": "2026-01-01T00:00:00Z",
        },
    )
    _write_json(
        tmp_path / "index_embeddings_evidence.json",
        {
            "status": "PARTIAL",
            "reason": "query_embedded_but_index_vectors_not_used",
            "index_vectors_used": False,
            "embeddings_file_present_in_zip": False,
            "model": "openai/text-embedding-3-small",
            "chunks_with_vectors": 12,
        },
    )
    requirements = module.ScenarioRequirements(
        require_embeddings_used=True,
        require_index_embeddings=True,
    )

    status, notes = module.validate_artifacts("embeddings_used_dispatch", tmp_path, requirements)

    assert status == "PASS"
    assert any("index_embeddings_evidence.status=PARTIAL" in note for note in notes)


def test_validate_artifacts_patch_missing_shows_debug_reason(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": False,
            "model_id": "not used",
            "skip_reason": "route=WAIT",
            "decision_route": "WAIT",
            "tokens_total": 0,
            "remaining_requests": 10,
            "reset_time_utc_iso": None,
            "totals": {"calls_count": 0},
        },
    )
    _write_json(
        tmp_path / "patch_generation_debug.json",
        {
            "reason": "diff_not_found_in_engine_or_llm_output",
            "llm_skip_reason": "route=WAIT",
            "decision_route": "WAIT",
            "compacted": True,
            "patch_batch_mode": True,
            "patch_batch_count": 3,
            "estimated_input_tokens": 3000,
            "max_output_tokens_used": 900,
        },
    )
    _write_json(
        tmp_path / "llm_http_debug.json",
        {
            "provider_http_status": 503,
            "provider_error_type": "server_error",
            "decision_route": "WAIT",
            "llm_skip_reason": "route=WAIT",
        },
    )
    requirements = module.ScenarioRequirements(require_patch=True)

    status, notes = module.validate_artifacts("fix_patch_required_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("patch_debug_reason=diff_not_found_in_engine_or_llm_output" in note for note in notes)
    assert any("provider_error_type=server_error" in note for note in notes)
    assert any("compacted=True" in note and "patch_batch_mode=True" in note for note in notes)


def test_fix_no_patch_returned_is_warn(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": True,
            "model_id": "openai/gpt-4.1-mini",
            "skip_reason": "n/a",
            "decision_route": "FAST",
            "tokens_total": 120,
            "remaining_requests": 9,
            "reset_time_utc_iso": "2026-01-01T00:00:00Z",
            "provider_http_status": None,
            "provider_error_type": "n/a",
        },
    )
    _write_json(
        tmp_path / "patch_generation_debug.json",
        {
            "reason": "no_patch_returned",
            "extraction_path_used": "no_patch",
            "compacted": True,
            "patch_batch_mode": True,
            "patch_batch_count": 2,
            "estimated_input_tokens": 1100,
            "max_output_tokens_used": 900,
        },
    )

    def fake_run_cmd(args: list[str], *, cwd: Path | None = None, check: bool = True):  # noqa: ANN001
        del args, cwd, check
        return module.CmdResult(code=0, out="ok", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    result = module._scenario_from_run(  # noqa: SLF001
        scenario_name="fix_patch_required_dispatch",
        trigger="/repobrain fix",
        run_data={"databaseId": "10", "url": "https://example/run/10", "conclusion": "success"},
        artifacts_root=tmp_path,
        requirements=module.ScenarioRequirements(require_patch=True),
    )
    assert result.status == "WARN"
    assert any("model chose NO_PATCH" in note for note in result.notes)


def test_fix_extractor_failed_is_fail_product(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": True,
            "model_id": "openai/gpt-4.1-mini",
            "skip_reason": "n/a",
            "decision_route": "FAST",
            "tokens_total": 140,
            "remaining_requests": 8,
            "reset_time_utc_iso": "2026-01-01T00:00:00Z",
            "provider_http_status": None,
            "provider_error_type": "n/a",
        },
    )
    _write_json(
        tmp_path / "patch_generation_debug.json",
        {
            "reason": "extractor_failed",
            "extraction_path_used": "none",
            "compacted": True,
            "patch_batch_mode": True,
            "patch_batch_count": 3,
            "estimated_input_tokens": 2500,
            "max_output_tokens_used": 900,
        },
    )

    def fake_run_cmd(args: list[str], *, cwd: Path | None = None, check: bool = True):  # noqa: ANN001
        del args, cwd, check
        return module.CmdResult(code=0, out="ok", err="")

    monkeypatch.setattr(module, "run_cmd", fake_run_cmd)

    result = module._scenario_from_run(  # noqa: SLF001
        scenario_name="fix_patch_required_dispatch",
        trigger="/repobrain fix",
        run_data={"databaseId": "11", "url": "https://example/run/11", "conclusion": "success"},
        artifacts_root=tmp_path,
        requirements=module.ScenarioRequirements(require_patch=True),
    )
    assert result.status == "FAIL_PRODUCT"


def test_validate_artifacts_requires_tkya_reason_lines(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": False,
            "execution_mode": "retrieval_only",
            "llm_decision_reason_short": "LLM not used: direct answer available from retrieved evidence.",
            "tokens_total": 0,
            "remaining_requests": 10,
            "reset_time_utc_iso": None,
        },
    )
    (tmp_path / "ask_result.md").write_text(
        "### ✅ Answer\n"
        "### 🤖 LLM\n"
        "- TKYA LLM decision: not used\n"
        "- Reason: LLM not used: direct answer available from retrieved evidence.\n",
        encoding="utf-8",
    )
    requirements = module.ScenarioRequirements(require_tkya_reason_lines=True)

    status, notes = module.validate_artifacts("llm_used_dispatch", tmp_path, requirements)

    assert status == "PASS"
    assert any("TKYA LLM decision line present" in note for note in notes)
    assert any("TKYA short reason line present" in note for note in notes)


def test_validate_artifacts_requires_runtime_override_when_llm_was_desired(tmp_path: Path) -> None:
    module = _load_module()
    _write_base_artifacts(tmp_path)
    _write_json(
        tmp_path / "llm_usage.json",
        {
            "llm_used": False,
            "execution_mode": "retrieval_plus_llm",
            "llm_decision_reason_short": "LLM used: multi-source synthesis required after retrieval.",
            "tokens_total": 0,
            "remaining_requests": 10,
            "reset_time_utc_iso": None,
        },
    )
    (tmp_path / "ask_result.md").write_text(
        "### ✅ Answer\n"
        "### 🤖 LLM\n"
        "- TKYA LLM decision: used\n"
        "- Reason: LLM used: multi-source synthesis required after retrieval.\n",
        encoding="utf-8",
    )
    requirements = module.ScenarioRequirements(require_tkya_reason_lines=True)

    status, notes = module.validate_artifacts("llm_used_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("missing `Runtime override:` line" in note for note in notes)
