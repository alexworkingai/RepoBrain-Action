# RepoBrain Environment Reference

This file is generated from `repobrain/config.py` by `scripts/gen_env_reference.py`.

| ENV | Type | Default | Allowed / Range | Description |
| --- | --- | --- | --- | --- |
| `RB_AI_DISABLE_EMBED_WHEN_REMAINING_LT` | int | `3` | 0..1000 | Disable embedding threshold. |
| `RB_AI_DISABLE_REDUCE_WHEN_REMAINING_LT` | int | `3` | 0..1000 | Disable reduce threshold. |
| `RB_AI_ESTIMATE_MODE_CONSERVATIVE` | bool | `1` | - | Conservative mode when headers absent. |
| `RB_AI_MAX_EMBED_CALLS_PER_RUN` | int | `10` | 1..1000 | Governor max embedding calls. |
| `RB_AI_MAX_LLM_CALLS_PER_RUN` | int | `6` | 1..100 | Governor max LLM calls. |
| `RB_AI_MAX_TOKENS_PER_RUN_EMBED` | int | `200000` | 1..10000000 | Governor embedding token cap. |
| `RB_AI_MAX_TOKENS_PER_RUN_LLM` | int | `12000` | 1..2000000 | Governor LLM token cap. |
| `RB_AI_MIN_REMAINING_BUFFER` | int | `2` | 0..100 | Governor request buffer. |
| `RB_AI_STOP_AT_REMAINING` | bool | `1` | - | Governor: stop when remaining exhausted. |
| `RB_AI_SWITCH_TO_MINI_WHEN_REMAINING_LT` | int | `5` | 0..1000 | Model downgrade threshold. |
| `RB_AI_TIME_BUDGET_S` | int | `240` | 1..86400 | Governor wall-clock budget. |
| `RB_ALLOW_DYNAMIC_VERIFY` | bool | `0` | - | Allow dynamic verification (pytest). |
| `RB_APPLY_PATCH` | bool | `0` | - | Allow patch auto-apply. |
| `RB_CREATE_PR` | bool | `0` | - | Allow PR creation after patch push. |
| `RB_DISABLE_INTERNAL_REACTIONS` | bool | `0` | - | Disable Python-side reactions. |
| `RB_EMBED_BATCH_SIZE` | int | `64` | 1..1024 | Embeddings batch size. |
| `RB_EMBED_ENABLED` | bool | `0` | - | Enable embeddings pipeline. |
| `RB_EMBED_MODEL` | str | `openai/text-embedding-3-small` | - | Embeddings model id. |
| `RB_FAIL_ON_NOT_RUN` | bool | `0` | - | Treat NOT_RUN verification as failure. |
| `RB_INDEX_CACHE_RESTORED` | bool | `0` | - | Mark index cache hit from workflow. |
| `RB_LLM_ALLOW_LOCATE` | bool | `0` | - | Allow LLM for locate command. |
| `RB_LLM_BATCH_ENABLE` | bool | `0` | - | Enable batch map-reduce LLM mode. |
| `RB_LLM_BATCH_FORCE` | bool | `0` | - | Force batch mode for review/fix in controlled runs. |
| `RB_LLM_BATCH_MAX_CALLS_PER_RUN` | int | `6` | 1..100 | Batch LLM call cap per run. |
| `RB_LLM_BATCH_REDUCE_ENABLE` | bool | `1` | - | Enable reduce step in batch mode. |
| `RB_LLM_BATCH_REDUCE_MODEL` | str | `` | - | Optional override model for reduce step. |
| `RB_LLM_ENABLED` | bool | `0` | - | Enable LLM layer. |
| `RB_LLM_MAX_INPUT_TOKENS` | int | `7600` | 256..64000 | Prompt input token budget. |
| `RB_LLM_MAX_INPUT_TOKENS_PATCH` | int | `3200` | 256..64000 | Patch prompt input token budget. |
| `RB_LLM_MAX_OUTPUT_TOKENS_ASK` | int | `1000` | 200..16000 | Ask max output tokens. |
| `RB_LLM_MAX_OUTPUT_TOKENS_FIX` | int | `2000` | 200..16000 | Fix max output tokens. |
| `RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL` | int | `2000` | 200..16000 | Global max output tokens. |
| `RB_LLM_MAX_OUTPUT_TOKENS_PATCH` | int | `900` | 64..16000 | Patch max output tokens. |
| `RB_LLM_MAX_OUTPUT_TOKENS_REVIEW` | int | `1400` | 200..16000 | Review max output tokens. |
| `RB_LLM_MODEL_HIGH` | str | `openai/gpt-4.1` | - | High-tier model id. |
| `RB_LLM_MODEL_LOW` | str | `openai/gpt-4.1-mini` | - | Low-tier model id. |
| `RB_LLM_PATCH_BATCH_ENABLE` | bool | `1` | - | Enable patch-specific LLM batching. |
| `RB_LLM_PATCH_BATCH_FORCE` | bool | `0` | - | Force patch batching in fix mode. |
| `RB_LLM_PATCH_BATCH_MAX_CALLS` | int | `4` | 1..32 | Patch batch call cap per run. |
| `RB_LLM_PATCH_MAX_HUNKS_PER_CALL` | int | `4` | 1..64 | Patch max diff hunks per LLM call. |
| `RB_LLM_PROVIDER` | str | `` | - | LLM provider name (github_models). |
| `RB_REQUIRE_VERIFY_FOR_PATCH` | bool | `0` | - | Require verification pass for patch success. |
| `RB_RETRIEVAL_VECTOR_TOPK` | int | `30` | 1..500 | Vector candidate top-k. |
| `RB_RETRIEVAL_W_LEX` | float | `0.55` | 0.0..1.0 | Hybrid lexical weight. |
| `RB_RETRIEVAL_W_VEC` | float | `0.45` | 0.0..1.0 | Hybrid vector weight. |
| `RB_TKYA_ALLOW_REMOTE` | bool | `0` | - | Allow remote/network operations in TKYA. |
| `RB_TKYA_BACKEND` | enum | `lite` | lite, v2, v5, original | TKYA backend selection. |
| `RB_TKYA_ORIGINAL_PATH` | str | `` | - | Optional override path for original vendor file. |
| `RB_TKYA_STRICT` | bool | `0` | - | Strict TKYA load mode. |
| `RB_TKYA_STRICT_ORIGINAL` | bool | `0` | - | Strict original vendor load mode. |
| `RB_TKYA_STRICT_V5` | bool | `0` | - | Strict v5 vendor load mode. |
| `RB_TKYA_V5_PATH` | str | `` | - | Optional override path for v5 vendor file. |
| `RB_TRUSTED_CONTEXT` | bool | `0` | - | Trusted execution context. |
| `RB_VERIFY_TIME_BUDGET_S` | int | `120` | 1..7200 | Verification time budget. |
