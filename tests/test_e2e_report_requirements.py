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
    (tmp_path / "ask_result.md").write_text(
        "### LLM\n- Calls this run: 1\n- Models used: openai/gpt-4.1-mini (1 call)",
        encoding="utf-8",
    )
    requirements = module.ScenarioRequirements(require_batch_calls_min=2)

    status, notes = module.validate_artifacts("batch_llm_dispatch", tmp_path, requirements)

    assert status == "FAIL"
    assert any("calls_count=1 is below required 2" in note for note in notes)
