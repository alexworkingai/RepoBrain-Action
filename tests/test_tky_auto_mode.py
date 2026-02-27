from repobrain.config import RepoBrainConfig
from repobrain.github_flow import resolve_tky_mode


def test_auto_selects_remote_when_enabled_and_url_present() -> None:
    cfg = RepoBrainConfig(
        tky_remote_enabled=True,
        tky_remote_allow_commands=["ask", "explain"],
        tky_remote_allow_branches=[],
        tky_remote_allow_repos=[],
    )
    used_mode, reason, effective_url = resolve_tky_mode(
        requested_mode="auto",
        cfg=cfg,
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url_input="https://example.test/v1/tky/decide",
    )
    assert used_mode == "remote"
    assert reason is None
    assert effective_url == "https://example.test/v1/tky/decide"


def test_auto_skips_remote_when_disabled() -> None:
    cfg = RepoBrainConfig(tky_remote_enabled=False)
    used_mode, reason, effective_url = resolve_tky_mode(
        requested_mode="auto",
        cfg=cfg,
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url_input="https://example.test/v1/tky/decide",
    )
    assert used_mode == "baseline"
    assert reason == "remote_disabled_by_config"
    assert effective_url == ""


def test_auto_skips_when_url_missing() -> None:
    cfg = RepoBrainConfig(
        tky_remote_enabled=True,
        tky_remote_allow_branches=[],
        tky_remote_allow_repos=[],
    )
    used_mode, reason, effective_url = resolve_tky_mode(
        requested_mode="auto",
        cfg=cfg,
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url_input="",
    )
    assert used_mode == "baseline"
    assert reason == "remote_url_missing"
    assert effective_url == ""


def test_remote_requested_but_not_allowed_cmd() -> None:
    cfg = RepoBrainConfig(
        tky_remote_enabled=True,
        tky_remote_allow_commands=["ask"],
        tky_remote_allow_branches=[],
        tky_remote_allow_repos=[],
    )
    used_mode, reason, effective_url = resolve_tky_mode(
        requested_mode="remote",
        cfg=cfg,
        cmd="locate",
        repo_name="owner/repo",
        branch_name="main",
        remote_url_input="https://example.test/v1/tky/decide",
    )
    assert used_mode == "baseline"
    assert reason == "command_not_allowed"
    assert effective_url == ""
