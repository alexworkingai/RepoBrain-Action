# E2E Testing (Current Repo)

RepoBrain E2E validation is executed locally via GitHub CLI:

- `python scripts/e2e/run_e2e_suite.py`

The harness uses only `workflow_dispatch --ref <branch>` simulation (no `issue_comment` dependency), so scenarios run before merge.

## Prerequisites

- `gh` CLI installed and authenticated (`gh auth status`)
- permissions to create branches/PRs and run workflows
- `models: read` permission in workflow for LLM/Embeddings scenarios

## Strict scenarios

1. `review_dispatch`
2. `llm_used_dispatch`  
   Required: `llm_usage.json`, `llm_used=true`, model/tokens/remaining/reset fields.
3. `embeddings_warmup_dispatch`
4. `embeddings_used_dispatch`  
   Required: `embeddings_usage.json`, `embed_used=true`, `query_embedded=true`, remaining/reset fields, and index embeddings evidence (`index/embeddings.jsonl` in zip OR `index_embeddings_evidence.json` with status `OK|PARTIAL`).
5. `fix_patch_required_dispatch`  
   Required: `patch.diff` or `patch_parts/*.diff`.
6. `batch_llm_dispatch`  
   Required: batch LLM multi-call (`calls_count >= 2` by default), plus markdown totals block.

## Required artifacts validated

- `config_snapshot.json` (usersafe scan)
- `ai_quota_snapshot.json`
- `llm_usage.json` (when required by scenario)
- `embeddings_usage.json` (when required by scenario)
- `index_embeddings_evidence.json` (for embeddings strict evidence)
- `patch.diff` / `patch_parts/*.diff` (for patch-required scenario)
- `batch_summaries.json` (optional but expected for batch diagnostics)

Artifacts are downloaded into:

- `artifacts/e2e/<scenario>/<run_id>/`
- final report: `artifacts/e2e/e2e_report.md`

## CLI controls

- `--require-llm-used true|false`
- `--require-embeddings-used true|false`
- `--require-patch true|false`
- `--require-batch-calls-min <int>`
- `--scenario-timeout-s <seconds>`
- `--cleanup` (close PR and delete branch at the end)
- workflow_dispatch toggle `batch_force=true` enables forced batch path for E2E-only validation.

Patch generation notes:

- Fix prompts enforce diff-only output (` ```diff ... ``` ` or raw unified diff).
- If no diff is extracted, RepoBrain writes `artifacts/patch_generation_debug.json` for usersafe diagnostics.

## PASS/FAIL interpretation

- **PASS**: workflow succeeded and all required assertions passed.
- **WARN**: workflow succeeded, strict assertions passed, but non-critical warnings exist (for example usersafe scan tool warning).
- **FAIL**: workflow failed, timeout happened, or any required artifact/JSON assertion failed.
