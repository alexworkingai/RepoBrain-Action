from repobrain.config import RepoBrainConfig


def test_config_snapshot_usersafe_masks_secret_like_values() -> None:
    cfg = RepoBrainConfig.from_env(
        source={
            "RB_FAKE_TOKEN": "abc123",
            "RB_SAMPLE_KEY": "xyz",
            "RB_LLM_ENABLED": "1",
            "GITHUB_TOKEN": "topsecret",
        }
    )
    payload = cfg.usersafe_dict()
    masked_env = payload["raw_env_masked"]
    assert masked_env["RB_FAKE_TOKEN"] == "***"
    assert masked_env["RB_SAMPLE_KEY"] == "***"
    assert masked_env["RB_LLM_ENABLED"] == "1"
    assert payload["workflow"]["github_token"] == "***"
