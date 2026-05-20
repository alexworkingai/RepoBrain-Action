from pathlib import Path

from repobrain.github_flow import get_last_audit, run_github_flow


def test_rd_block_is_present_for_local_v5_with_rd_enabled(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("RB_TKYA_BACKEND", "v5")
    monkeypatch.setenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", "1")
    monkeypatch.setenv("RB_TKYA_ENABLE_RD_PIPELINE", "1")
    monkeypatch.delenv("RB_TKYA_V5_CANARY_PERCENT", raising=False)
    monkeypatch.delenv("RB_TKYA_CANARY_KEY", raising=False)

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Где реализована логика TKYProvider?",
        issue_number=None,
        tky_mode="local",
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit.get("tky_engine") == "topocore_v5"
    rd = audit.get("rd", {})
    assert isinstance(rd, dict)
    assert rd.get("rd_used") is True
    assert rd.get("rd_status") in {"ok", "blocked_validation", "error", "unavailable"}
