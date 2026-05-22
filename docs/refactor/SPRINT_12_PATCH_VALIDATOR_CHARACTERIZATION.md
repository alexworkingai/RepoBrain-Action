# Sprint 12 Patch Validator Characterization

## 1. Purpose

Add narrow characterization coverage around `repobrain/patch_validator.py` before any future surgical refactor, while preserving current Fix-Lite, `NO_PATCH`, and bounded no-action behavior.

## 2. Repository states and local paths

- Primary repository: `<LOCAL_REPO_ROOT>`
  - Branch at sprint start: `main`
  - Starting commit: `10c2352 Merge pull request #105 from alexworkingai/codex/refactor-11-patch-targeting-microrefactor`
- Public external runtime repository: `<LOCAL_PROJECT_ROOT>\repobrain-community`
  - Expected branch/state reviewed from sprint instructions only: `codex/sprint-78-fix-lite-candidate`, clean
- Third-party validation repository: `<EXTERNAL_CONSUMER_REPO>`
  - Expected branch/state reviewed from sprint instructions only: `test/sprint-73-guidance-live-validation`, with possible pre-existing `artifacts/` noise

## 3. Current command truth and primary/external contract split

- External GitHub foundation truth remains: `/repobrain doctor`, `/repobrain help`, `/repobrain ask`, `/repobrain review`, `/repobrain fix`.
- External review remains a bounded read-only Review Candidate.
- External fix remains a Fix-Lite Candidate manual-only patch suggestion.
- Mandatory Fix-Lite visible boundary remains: `No patch was applied. No files were modified.`
- Primary RepoBrain-Action PR UI remains distinct:
  - `/repobrain review` may render as `### ? PR Review`
  - `/repobrain fix` may render as primary-mode patch operation output
  - bounded behavior and non-claims remain mandatory

## 4. Files inspected

- `repobrain/patch_validator.py`
- `repobrain/patch_targeting.py`
- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`
- `tests/test_patch_validator.py`
- `tests/test_patch_targeting.py`
- `tests/test_patch_extract.py`
- `tests/test_patch_guard.py`
- `tests/test_fix_governance_localized_evidence.py`
- `tests/test_fix_no_patch_rendering.py`
- `docs/refactor/SPRINT_10_PATCH_TARGETING_CHARACTERIZATION.md`
- `docs/refactor/SPRINT_11_PATCH_TARGETING_MICROREFACTOR.md`

## 5. Existing coverage summary

Existing tests already covered:

- placeholder patch rejection
- unrelated-file patch rejection against PR changed files
- grounded minimal diff acceptance for `fix`
- explicit empty-payload `NO_PATCH` classification
- patch extraction behavior for diff fences, raw diffs, JSON `no_patch`, and missing patch text
- patch guard behavior for empty output, placeholder content, generic prose, and real diffs
- patch targeting refusal and localized selection behavior
- fix-localization gating and safe `no_patch` rendering

The main remaining gaps were around generic prose classification inside the validator itself, malformed diff-like payloads with no touched file, and the deterministic non-`fix` grounded path when diff structure is valid but no PR changed-file filter is supplied.

## 6. Characterization tests added

Added to `tests/test_patch_validator.py`:

- `test_generic_prose_patch_payload_is_invalid`
  - confirms generic prose remains `INVALID_PATCH_FORMAT` and does not become a valid patch
- `test_diff_like_payload_without_touched_files_is_rejected`
  - confirms malformed diff-like text with no usable touched file remains rejected as `PATCH_WITHOUT_TOUCHED_FILES`
- `test_non_fix_command_can_validate_grounded_diff_without_pr_changed_files`
  - confirms current non-`fix` behavior for a valid minimal diff remains grounded and deterministic without implying application

## 7. Any implementation changes made, if any

- None.
- `repobrain/patch_validator.py` was not modified in this sprint.

## 8. Behavior-preservation statement

This sprint was test-first and behavior-preserving.

- No command behavior changed.
- No Fix-Lite semantics changed.
- No `NO_PATCH` governance changed.
- No patch application behavior was added.
- No file modification behavior was added.
- No patch targeting behavior changed.
- No public output wording changed.

## 9. Risks and rollback notes

- Risk is low because the sprint adds only characterization coverage plus this note.
- If a later refactor conflicts with these tests, the tests should be treated as the current validator contract until a dedicated behavior-change sprint explicitly redefines it.
- Rollback is straightforward because no runtime code changed in this sprint.

## 10. Validation results

Planned validation for this sprint:

- `ruff check .`
- `pytest -q`
- `pytest -q tests/test_patch_validator.py`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `pytest -q -k "patch or no_patch or fix"`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 11. Explicit statement

No runtime behavior was intentionally changed in Sprint 12.
