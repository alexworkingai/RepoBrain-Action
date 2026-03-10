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
2. `fix_patch_required_dispatch`  
   Required: `patch.diff` or `patch_parts/*.diff`.
   This scenario runs early because patch generation is quota-sensitive.
3. `llm_used_dispatch`  
   Required: `llm_usage.json`, `llm_used=true`, model/tokens/remaining/reset fields.
4. `embeddings_warmup_dispatch`
5. `embeddings_used_dispatch`  
   Required: `embeddings_usage.json`, `embed_used=true`, `query_embedded=true`, remaining/reset fields, and runtime-truth embeddings evidence (`index_embeddings_evidence.json` with status `OK|PARTIAL`).
   Semantics:
   - `OK`: query embedding + loaded index vectors + vectors used in hybrid scoring.
   - `PARTIAL`: query embedding works, but index vectors were unavailable or not used.
   - `DISABLED`: embeddings disabled in this run.
   - `UNKNOWN`: internal embedding error (usersafe reason is included).
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
- `--reserve-fix-quota true|false` (default `true`; harness may skip batch with `WARN` when remaining quota after fix is very low)
- `--cleanup` (close PR and delete branch at the end)
- workflow_dispatch toggle `batch_force=true` enables forced batch path for E2E-only validation.

Patch generation notes:

- Fix prompts enforce diff-only output (` ```diff ... ``` ` or raw unified diff).
- If no diff is extracted, RepoBrain writes `artifacts/patch_generation_debug.json` for usersafe diagnostics.
- If fix LLM fails in `workflow_dispatch`, RepoBrain writes `artifacts/llm_http_debug.json` with usersafe provider diagnostics (`status/error type`, no prompt/code/secrets).

## PASS/FAIL interpretation

- **PASS**: workflow succeeded and all required assertions passed.
- **WARN**: strict checks passed, but non-critical transport/diagnostic warnings exist.
- **FAIL_PRODUCT**: product behavior failed (artifacts downloaded and strict assertions failed).
- **FAIL_INFRA**: infrastructure/transport failure (for example artifact download/network issues) prevented reliable product verdict.

Fix scenario special classification:

- Provider rate-limited errors (`provider_http_status=429` or `provider_error_type=rate_limited`) are classified as **FAIL_INFRA**.
- **FAIL_PRODUCT** for fix is only used when model path is available but patch output/extraction still fails.

Artifact transport fallback diagnostics:

- On download failure, the harness stores:
  - `run_view.json`
  - `run_log.txt`
- It scans logs and run artifact metadata for evidence of upload steps.
- If uploads likely succeeded but local download failed, the scenario is downgraded to `WARN` instead of product failure.
