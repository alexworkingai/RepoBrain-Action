from repobrain.config import RepoBrainConfig
from repobrain.github_flow import decide_remote_usage


def test_skip_reason_remote_disabled_by_config() -> None:
    use_remote, reason = decide_remote_usage(
        cfg=RepoBrainConfig(tky_remote_enabled=False),
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url="https://example.test/v1/tky/decide",
    )
    assert use_remote is False
    assert reason == "remote_disabled_by_config"


def test_skip_reason_remote_url_missing() -> None:
    use_remote, reason = decide_remote_usage(
        cfg=RepoBrainConfig(tky_remote_enabled=True, tky_remote_allow_branches=[], tky_remote_allow_repos=[]),
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url="",
    )
    assert use_remote is False
    assert reason == "remote_url_missing"


def test_skip_reason_command_branch_repo_not_allowed() -> None:
    cfg = RepoBrainConfig(
        tky_remote_enabled=True,
        tky_remote_allow_commands=["ask"],
        tky_remote_allow_branches=["main"],
        tky_remote_allow_repos=["allowed/repo"],
    )

    use_remote, reason = decide_remote_usage(
        cfg=cfg,
        cmd="locate",
        repo_name="allowed/repo",
        branch_name="main",
        remote_url="https://example.test/v1/tky/decide",
    )
    assert use_remote is False
    assert reason == "command_not_allowed"

    use_remote, reason = decide_remote_usage(
        cfg=cfg,
        cmd="ask",
        repo_name="allowed/repo",
        branch_name="dev",
        remote_url="https://example.test/v1/tky/decide",
    )
    assert use_remote is False
    assert reason == "branch_not_allowed"

    use_remote, reason = decide_remote_usage(
        cfg=cfg,
        cmd="ask",
        repo_name="owner/repo",
        branch_name="main",
        remote_url="https://example.test/v1/tky/decide",
    )
    assert use_remote is False
    assert reason == "repo_not_allowed"
