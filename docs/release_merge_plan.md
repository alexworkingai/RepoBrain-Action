> Historical/internal release note. This file is retained for repository history and is not current public release, public install, or Marketplace publication guidance.
>
> Current release-readiness guidance lives in:
> - `docs/release/RELEASE_CANDIDATE_CHECKLIST.md`
> - `docs/release/PUBLIC_READINESS_ASSESSMENT.md`
> - `docs/release/MARKETPLACE_READINESS_ASSESSMENT.md`
> - `docs/release/RELEASE_NOTES_RC1.md`
# Release Merge Plan: `0.5.0-rc.1`

## Recommended merge order

Merge sprint branches into a release branch in this order:

1. `origin/codex/sprint-2-v5-wiring`
2. `origin/codex/sprint-3-e2e-ux-artifacts`
3. `origin/codex/sprint-4-pr-review-patch-verify`
4. `origin/codex/sprint-5-checks-gates-auto-pr`
5. `origin/codex/sprint-6-github-models-llm-selection`
6. `origin/codex/sprint-7-llm-hardening-quota-budget`
7. `origin/codex/sprint-8-batch-llm-large-pr`
8. `origin/codex/sprint-9-embeddings-hybrid-retrieval`
9. `origin/codex/sprint-10-ai-budget-governor`
10. `origin/codex/sprint-11-config-unification`
11. `origin/codex/sprint-12-release-candidate`

## Suggested git commands

```bash
git checkout main
git pull
git checkout -b release/0.5.0-rc.1
git merge --no-ff origin/codex/sprint-2-v5-wiring
git merge --no-ff origin/codex/sprint-3-e2e-ux-artifacts
git merge --no-ff origin/codex/sprint-4-pr-review-patch-verify
git merge --no-ff origin/codex/sprint-5-checks-gates-auto-pr
git merge --no-ff origin/codex/sprint-6-github-models-llm-selection
git merge --no-ff origin/codex/sprint-7-llm-hardening-quota-budget
git merge --no-ff origin/codex/sprint-8-batch-llm-large-pr
git merge --no-ff origin/codex/sprint-9-embeddings-hybrid-retrieval
git merge --no-ff origin/codex/sprint-10-ai-budget-governor
git merge --no-ff origin/codex/sprint-11-config-unification
git merge --no-ff origin/codex/sprint-12-release-candidate
```

## Expected conflict hotspots

- `repobrain/github_flow.py`
- `repobrain/output_md.py`
- `repobrain/index_store.py`
- `.github/workflows/repobrain.yml`
- `README.md`

Resolve with explicit manual review. Do not use `-X ours`.

## RC checklist

- Run workflows on a sample repo (`issue_comment`, `workflow_dispatch`, canary).
- Verify index artifact contains `manifest.json` and `topo_map.json` (and embeddings file when enabled).
- Confirm PR check-run publication appears for review/fix paths.
- Confirm usersafe outputs: no secrets/tokens in comments/artifacts.
- Confirm budget governor interventions appear in audit/usage artifacts.
- Confirm `artifacts/config_snapshot.json` exists and is usersafe.
- Run `ruff check .` and `pytest -q` on release branch before tagging.
