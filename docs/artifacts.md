# RepoBrain Artifacts & Usersafe Output

## Index Zip Contract

RepoBrain index packages are generated as:

- `artifacts/index-package.zip` (runtime default)
- `artifacts/repobrain-index-<commit>.zip` (explicit commit-tagged copy)

Required entries **inside** the zip:

- `manifest.json`
- `topo_map.json`
- `index/chunks.jsonl`

Backward-compatibility entry is also kept:

- `chunks.jsonl` (legacy loader path)

`manifest.json` fields:

- `format_version`
- `commit_sha`
- `created_at`
- `files_indexed`
- `chunks`
- `embeddings`
- `topo`
- `exclusions`
- `tool_versions`

`topo_map.json` is usersafe and metadata-only (graph counts, metrics, file-level chunk counts).  
No raw source code is embedded by default (`store_text=false`).

## Usersafe Ask Output Rules

QA markdown responses must remain usersafe:

- no env dumps
- no runner-local paths
- no tokens/secrets
- no raw code snippets in comments

Template behavior:

- route-aware headers:
  - `✅ Answer`
  - `⏳ Needs verification`
  - `🚫 Refused`
  - `🛑 Blocked`
- include `What I used` with file locators only (`path + line range`)
- include `Verification` summary (`PASS/WARN/NOT_RUN`)
- include `Route/Mode`, including deep-pass marker when pass-2 was used

Comment size protection:

- if rendered markdown exceeds ~60KB, comment is truncated safely
- full markdown is saved to `artifacts/ask_result.md`
- workflow should publish artifacts for deeper inspection

## Review/Fix Artifacts

When review/fix verification runs:

- `artifacts/verification_report.json` is written (usersafe summary only)
- `artifacts/patch.diff` is written when `/repobrain fix` has a generated patch
- `artifacts/patch_parts/*.diff` stores per-batch patch parts when batch LLM fix mode is enabled
- `artifacts/check_run_payload.json` is written when PR check payload is prepared
- `artifacts/llm_usage.json` is written when GitHub Models LLM is enabled
- `artifacts/batch_summaries.json` stores usersafe map-stage summaries for batch runs

`artifacts/llm_usage.json` (usersafe) includes:

- `date_utc`
- `llm_used`, `skip_reason`
- `model_id`, `tier`
- `calls_this_run`
- `tokens_prompt`, `tokens_completion`, `tokens_total`
- `max_output_tokens_used`
- `input_budget_limit`, `input_budget_used_est`
- `dropped_locators_count`, `dropped_hunks_count`, `dropped_snippets_count`
- `remaining_requests`, `remaining_is_estimate`
- `reset_time_utc_iso`
- `estimate_flags` (reported vs estimated usage/remaining)
- `ratelimit_headers_subset` (`x-ratelimit-*` only)
- `calls` (per-call entries with `batch_id`, model, tokens, remaining/reset)
- `totals` (`calls_count`, token totals)
- `model_counts` (model -> call count)
- `final_remaining_requests`, `final_reset_time_utc_iso`

Safe defaults:

- patch is **not** auto-applied unless both `RB_APPLY_PATCH=1` and `RB_TRUSTED_CONTEXT=1`
- dynamic verification (pytest) is gated by `RB_TRUSTED_CONTEXT=1` and `RB_ALLOW_DYNAMIC_VERIFY=1`

## Canary Workflow

Workflow: `.github/workflows/canary_v5.yml`

- trigger: `workflow_dispatch`
- env:
  - `RB_TKYA_BACKEND=v5`
  - `RB_TKYA_ALLOW_REMOTE=0`
  - `RB_TKYA_STRICT=0`
- behavior:
  - runs lint/tests for wiring safety
  - if v5 vendor file is present, executes full test suite
  - if v5 vendor file is absent, executes a fallback test subset and does not fail purely because vendor is missing
