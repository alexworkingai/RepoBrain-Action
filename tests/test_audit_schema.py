from pathlib import Path

from repobrain.github_flow import get_last_audit, run_github_flow


def _contains_forbidden_key(obj: object) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in {"raw_text", "snippet", "content"}:
                return True
            if _contains_forbidden_key(value):
                return True
        return False
    if isinstance(obj, list):
        return any(_contains_forbidden_key(item) for item in obj)
    return False


def test_audit_schema_has_core_fields_and_no_raw_content_keys() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Где реализована логика TKYProvider?",
        issue_number=None,
        tky_mode="baseline",
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert "timings_ms" in audit
    assert "route_final" in audit
    assert "tky_mode_used" in audit
    assert "index_source" in audit
    assert audit["tky_mode_used"] in {"baseline", "remote", "local", "fallback_baseline", "n/a"}
    assert audit["tky_fallback_reason"] in {"n/a", "remote_error"}
    assert audit["tky_remote_status"] is None or isinstance(audit["tky_remote_status"], int)
    assert audit["index_source"] in {"cache_hit", "artifact_present", "rebuilt", "n/a"}
    timings = audit["timings_ms"]
    assert isinstance(timings, dict)
    assert timings
    assert "parse" in timings
    assert "security_check" in timings
    assert "format" in timings
    for value in timings.values():
        assert isinstance(value, float)
        assert value >= 0.0
    assert _contains_forbidden_key(audit) is False


def test_audit_tky_fields_are_na_for_verify_dry_run() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain verify",
        issue_number=None,
        tky_mode="baseline",
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["tky_mode_used"] == "n/a"
    assert audit["tky_fallback_reason"] == "n/a"
    assert audit["tky_remote_status"] is None
    assert audit["index_source"] == "n/a"
