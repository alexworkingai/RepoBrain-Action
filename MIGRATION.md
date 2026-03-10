# Migration Guide

This guide summarizes what changed to move to the `0.5.0-rc.1` release candidate.

## 1. Workflow permissions

Ensure your RepoBrain workflow includes:

- `contents: read`
- `issues: write`
- `pull-requests: write`
- `checks: read`
- `statuses: read`
- `actions: read`
- `models: read` (required only when enabling LLM/embeddings GitHub Models features)

## 2. New artifacts

RepoBrain now emits additional usersafe artifacts:

- `artifacts/llm_usage.json`
- `artifacts/embeddings_usage.json`
- `artifacts/ai_quota_snapshot.json`
- `artifacts/config_snapshot.json`
- `artifacts/check_run_payload.json` (when check-run path is used)

See `docs/artifacts.md` for schemas.

## 3. Commands

Supported commands include:

- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review` (PR context)
- `/repobrain fix <instruction>` (PR context)
- `/repobrain verify` (PR checks/status verification)

## 4. Env configuration

RB_* variables are now centralized via `repobrain/config.py`.

- Reference: `docs/env_reference.md`
- Generator: `python scripts/gen_env_reference.py`

## 5. Safe defaults

Defaults remain conservative:

- LLM disabled (`RB_LLM_ENABLED=0`)
- Embeddings disabled (`RB_EMBED_ENABLED=0`)
- Apply patch disabled (`RB_APPLY_PATCH=0`)
- Auto PR disabled (`RB_CREATE_PR=0`)
- Trusted context disabled (`RB_TRUSTED_CONTEXT=0`)
- TKYA remote/network disabled (`RB_TKYA_ALLOW_REMOTE=0`)

Enable features explicitly per workflow and repository policy.

