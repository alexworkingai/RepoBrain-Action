from repobrain.config import RepoBrainConfig


def test_config_validation_clamps() -> None:
    cfg = RepoBrainConfig.from_env(
        source={
            "RB_LLM_MAX_INPUT_TOKENS": "-10",
            "RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL": "999999",
            "RB_EMBED_BATCH_SIZE": "0",
            "RB_RETRIEVAL_W_LEX": "2.5",
            "RB_RETRIEVAL_W_VEC": "abc",
            "RB_AI_MAX_LLM_CALLS_PER_RUN": "foo",
        }
    )
    assert cfg.llm.max_input_tokens == 256
    assert cfg.llm.max_output_tokens_global == 16000
    assert cfg.embeddings.batch_size == 1
    assert cfg.embeddings.weight_lexical == 1.0
    assert cfg.embeddings.weight_vector == 0.45
    assert cfg.governor.max_llm_calls_per_run == 6
    assert cfg.warnings
