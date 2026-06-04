from repobrain.config import RepoBrainConfig


def test_config_defaults_safe() -> None:
    cfg = RepoBrainConfig.from_env(source={})
    assert cfg.llm.enabled is False
    assert cfg.llm.enable_issue_llm is True
    assert cfg.llm.enable_issue_comment is True
    assert cfg.llm.enable_pr_comments is True
    assert cfg.llm.enable_issue_only is False
    assert cfg.embeddings.enabled is False
    assert cfg.workflow.apply_patch is False
    assert cfg.workflow.create_pr is False
    assert cfg.workflow.trusted_context is False
    assert cfg.tkya.allow_remote is False
