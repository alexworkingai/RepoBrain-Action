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
    assert _contains_forbidden_key(audit) is False
