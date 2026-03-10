# Post-Merge Validation (Default Branch)

Run this after merging release changes into the default branch.

## 1. Baseline workflow_dispatch validation

1. Trigger `.github/workflows/post_merge_validate.yml` via `workflow_dispatch`.
2. Confirm the run is green:
   - `ruff check .`
   - `pytest -q`
   - `python scripts/check_env_reference_up_to_date.py`
   - `python scripts/usersafe_scan.py`
   - `python scripts/check_tkya_contract_guard.py`
3. Confirm `repobrain-release-notes` artifact is uploaded with `artifacts/release_notes.md`.

## 2. Real issue_comment path validation

Use a real PR in the repository and post these commands in PR discussion:

1. `/repobrain review`
2. `/repobrain ask what changed in this PR?`
3. `/repobrain fix improve naming in modified files`

For each command, confirm:

- workflow run starts from `issue_comment`
- usersafe comment is posted
- expected artifacts are uploaded
- no secrets/tokens appear in comment or artifacts

## 3. Check-run validation on real PR

1. Confirm `RepoBrain Review` / `RepoBrain Fix` check-run appears on PR.
2. Confirm conclusion aligns with route + verification outcome.
3. Confirm annotations (if present) are usersafe and include only path/line metadata.

## 4. Rollback plan

If regression is detected:

1. Disable optional features in workflow env (LLM/embeddings/batch/patch apply flags) and re-run.
2. Revert the problematic release merge commit(s) on default branch.
3. Re-run post-merge validation workflow to confirm baseline stability.
4. Open incident note with:
   - failing scenario
   - affected command (`ask/review/fix/verify`)
   - failing artifact/check-run evidence
