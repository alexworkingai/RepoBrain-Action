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
| `RB_GH_APP_ID` | str | `` | - | GitHub App id for app-first onboarding/readiness checks. |
| `RB_GH_APP_INSTALLATION_ID` | str | `` | - | GitHub App installation id for selected/all repository rollout checks. |
| `RB_GH_APP_PRIVATE_KEY` | str | `` | - | GitHub App private key PEM (secret) for app-first onboarding/readiness checks. |
| `RB_GH_APP_PRIVATE_KEY_PATH` | str | `` | - | Optional path to GitHub App private key PEM used by readiness checker. |
| `RB_GH_APP_REPOSITORY_SELECTION` | enum | `selected` | selected, all | GitHub App repository rollout mode for onboarding (`selected` recommended, `all` allowed). |
| `RB_GH_APP_SELECTED_REPOS` | str | `` | - | Comma-separated repository allowlist when `RB_GH_APP_REPOSITORY_SELECTION=selected`. |
| `RB_GH_APP_WEBHOOK_SECRET` | str | `` | - | GitHub App webhook secret used by onboarding/readiness checks. |
| `RB_INDEX_CACHE_RESTORED` | bool | `0` | - | Mark index cache hit from workflow. |
| `RB_LLM_ALLOW_LOCATE` | bool | `0` | - | Allow LLM for locate command. |
| `RB_LLM_BATCH_ENABLE` | bool | `0` | - | Enable batch map-reduce LLM mode. |
| `RB_LLM_BATCH_FORCE` | bool | `0` | - | Force batch mode for review/fix in controlled runs. |
| `RB_LLM_BATCH_MAX_CALLS_PER_RUN` | int | `6` | 1..100 | Batch LLM call cap per run. |
| `RB_LLM_BATCH_REDUCE_ENABLE` | bool | `1` | - | Enable reduce step in batch mode. |
| `RB_LLM_BATCH_REDUCE_MODEL` | str | `` | - | Optional override model for reduce step. |
| `RB_LLM_BUDGET_SENSITIVITY` | enum | `not_available` | low, normal, high, not_available | Optional budget sensitivity hint for control-plane audit truth. |
| `RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_ASK` | int | `8` | 0..1000 | Minimum remaining requests before allowing ask downgrade from preferred model. |
| `RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_FIX` | int | `5` | 0..1000 | Minimum remaining requests before allowing fix downgrade from preferred model. |
| `RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW` | int | `4` | 0..1000 | Minimum remaining requests before allowing review downgrade from preferred model. |
| `RB_LLM_ENABLED` | bool | `0` | - | Enable LLM layer. |
| `RB_LLM_ENABLE_ISSUE_COMMENT` | bool | `1` | - | Allow LLM for issue_comment event path. |
| `RB_LLM_ENABLE_ISSUE_ONLY` | bool | `0` | - | Allow LLM for issue_comment on non-PR issues. |
| `RB_LLM_ENABLE_PR_COMMENTS` | bool | `1` | - | Allow LLM for issue_comment on PR discussions. |
| `RB_LLM_EXECUTION_PROFILE` | enum | `balanced` | cheap, balanced, premium | Execution profile control-plane mode (`cheap`, `balanced`, `premium`). |
| `RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK` | bool | `1` | - | Retain preferred strong model for complex ask/explain when quota remains comfortable. |
| `RB_LLM_LATENCY_SENSITIVITY` | enum | `not_available` | low, normal, high, not_available | Optional latency sensitivity hint for control-plane audit truth. |
| `RB_LLM_MAX_FILES_REVIEW_CONTEXT` | int | `40` | 1..500 | Maximum changed files included in final review synthesis context. |
| `RB_LLM_MAX_FINDINGS_CONTEXT` | int | `24` | 1..200 | Maximum condensed findings/notes included in final review synthesis context. |
| `RB_LLM_MAX_HUNKS_REVIEW_CONTEXT` | int | `24` | 1..500 | Maximum diff hunks included in final review synthesis context. |
| `RB_LLM_MAX_INPUT_TOKENS` | int | `7600` | 256..64000 | Prompt input token budget. |
| `RB_LLM_MAX_INPUT_TOKENS_PATCH` | int | `3200` | 256..64000 | Patch prompt input token budget. |
| `RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL` | int | `3600` | 256..64000 | Final review synthesis prompt input token budget. |
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
| `RB_LLM_PATCH_MAX_TARGET_FILES` | int | `5` | 1..100 | Maximum files selected for localized patch generation. |
| `RB_LLM_PATCH_MAX_TARGET_HUNKS` | int | `12` | 1..300 | Maximum hunks selected for localized patch generation. |
| `RB_LLM_PATCH_REQUIRE_LOCALIZED_EVIDENCE` | bool | `1` | - | Require localized evidence before running patch generation. |
| `RB_LLM_PROVIDER` | str | `` | - | LLM provider name (github_models). |
| `RB_REPOBRAIN_ENABLE_ISSUE_LLM` | bool | `1` | - | Enable controlled LLM for trusted issue ask/explain and issue audit narrative flows. |
| `RB_REQUIRE_VERIFY_FOR_PATCH` | bool | `0` | - | Require verification pass for patch success. |
| `RB_RETRIEVAL_VECTOR_TOPK` | int | `30` | 1..500 | Vector candidate top-k. |
| `RB_RETRIEVAL_W_LEX` | float | `0.55` | 0.0..1.0 | Hybrid lexical weight. |
| `RB_RETRIEVAL_W_VEC` | float | `0.45` | 0.0..1.0 | Hybrid vector weight. |
| `RB_TKYA_ALLOW_REMOTE` | bool | `0` | - | Allow remote/network operations in TKYA. |
| `RB_TKYA_BACKEND` | enum | `auto` | auto, v6 | Legacy compatibility selector. Supported runtime selectors: auto or v6. Legacy lite/v5 values are unsupported and fail safely. |
| `RB_TKYA_STRICT` | bool | `0` | - | Strict TKYA load mode. |
| `RB_TKYA_STRICT_V5` | bool | `0` | - | Strict protected-kernel v5 load mode. |
| `RB_TKYA_V5_PATH` | str | `` | - | Obsolete legacy override for a removed v5 runtime file. Retained only for safe unsupported diagnostics. |
| `RB_TOPOCORE_ALLOW_DEPRECATED_V5` | bool | `0` | - | Obsolete legacy env. It no longer re-enables any runtime path and is retained only for safe unsupported diagnostics. |
| `RB_TOPOCORE_BACKEND` | enum | `auto` | auto, v6 | Supported TopoCore runtime selector. Supported values: auto or v6. Legacy v5 is unsupported and fails safely. |
| `RB_TOPOCORE_V5_SIMULATE_DISABLED` | bool | `0` | - | Obsolete legacy simulation env. V5 runtime is already removed; this variable is retained only for compatibility metadata. |
| `RB_TRUSTED_CONTEXT` | bool | `0` | - | Trusted execution context. |
| `RB_VERIFY_TIME_BUDGET_S` | int | `120` | 1..7200 | Verification time budget. |
