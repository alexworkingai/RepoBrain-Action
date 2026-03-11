# Release Execution Report (`0.5.0-rc.1`)

## Release context

- `VERSION`: `0.5.0-rc.1`
- Default branch: `main`
- Release branch: `release/0.5.0-rc.1`
- Merge source: `origin/codex/sprint-26-release-finalization`
- Cumulative ancestry check: `PASSED`
  - `sprint-25-final-patch-output-fix -> sprint-26-release-finalization`: yes
  - `sprint-24-fix-patch-payload-compaction -> sprint-26-release-finalization`: yes
  - `sprint-21-embeddings-evidence-and-fix-llm -> sprint-26-release-finalization`: yes

## Release execution actions

1. Created branch `release/0.5.0-rc.1` from `main`.
2. Merged `origin/codex/sprint-26-release-finalization` using:
   - `git merge --no-ff ... -m "Merge RC implementation for 0.5.0-rc.1"`
3. Pushed `release/0.5.0-rc.1` to origin.

## Local validation on release branch

- `ruff check .`: PASS
- `pytest -q`: PASS (`251 passed`)
- `python scripts/gen_env_reference.py`: PASS
- `python scripts/check_env_reference_up_to_date.py`: PASS
- `python scripts/usersafe_scan.py`: PASS
- `python scripts/check_tkya_contract_guard.py`: PASS
- `python scripts/release/gen_release_notes.py`: PASS

## post_merge_validate workflow dispatch

- Attempted command:
  - `gh workflow run post_merge_validate.yml --ref release/0.5.0-rc.1`
- Result: `BLOCKED_BY_GITHUB_API`
- API response:
  - `HTTP 404: workflow post_merge_validate.yml not found on the default branch`
- Run URL: `n/a`
- Conclusion: `not executed`
- Notes:
  - Workflow file exists in release branch, but GitHub dispatch API requires workflow to be discoverable from default branch.

## E2E suite on release branch

- Command: `python -u scripts/e2e/run_e2e_suite.py`
- Report: `artifacts/e2e/e2e_report.md`
- Summary: `PASS=6, WARN=0, FAIL_PRODUCT=0, FAIL_INFRA=0`
- Scenario run URLs:
  - review_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896373421`
  - fix_patch_required_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896405953`
  - llm_used_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896525876`
  - embeddings_warmup_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896556154`
  - embeddings_used_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896588216`
  - batch_llm_dispatch: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/22896621380`

## Recommendation

RC release branch is validated via local/static checks and strict E2E.  
Status: `READY_FOR_PR` to `main`.

Post-merge action required on default branch:

1. Run `.github/workflows/post_merge_validate.yml` via `workflow_dispatch`.
2. Verify `repobrain-release-notes` artifact upload.
