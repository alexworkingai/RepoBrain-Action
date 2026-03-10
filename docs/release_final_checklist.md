# Release Final Checklist (`0.5.0-rc.1`)

Use this checklist before merging the release branch and preparing the final tag.

## 1. Pre-merge checks

- [ ] `ruff check .`
- [ ] `pytest -q`
- [ ] `python scripts/check_env_reference_up_to_date.py`
- [ ] `python scripts/usersafe_scan.py`
- [ ] `python scripts/check_tkya_contract_guard.py`
- [ ] Full E2E suite is green (`scripts/e2e/run_e2e_suite.py` strict scenarios)

## 2. Artifact checks

- [ ] `manifest.json` exists and `format_version == "1.0"`
- [ ] `topo_map.json` exists in index package
- [ ] `artifacts/llm_usage.json` is usersafe (no tokens/secrets/raw code)
- [ ] `artifacts/embeddings_usage.json` is usersafe
- [ ] `artifacts/ai_quota_snapshot.json` is usersafe
- [ ] `artifacts/config_snapshot.json` is usersafe

## 3. GitHub checks and comments

- [ ] RepoBrain check-run appears on PR review/fix flows
- [ ] Check annotations use usersafe path/line metadata only
- [ ] Comment output remains usersafe (no env dumps, no token values, no runner-local paths)

## 4. LLM / Embeddings / Patch readiness

- [ ] Model selection is visible in output (`gpt-4.1` vs `gpt-4.1-mini`)
- [ ] Quota fields are visible (remaining/reset/estimated marker)
- [ ] Embeddings status and evidence are visible when enabled
- [ ] Fix scenario produces patch artifact or explicit usersafe diagnostic outcome

## 5. Release mechanics

- [ ] `VERSION` matches release target
- [ ] `CHANGELOG.md` and `MIGRATION.md` are up to date
- [ ] `python scripts/release/gen_release_notes.py` produces deterministic `artifacts/release_notes.md`
- [ ] Merge plan reviewed (`docs/release_merge_plan.md`)
