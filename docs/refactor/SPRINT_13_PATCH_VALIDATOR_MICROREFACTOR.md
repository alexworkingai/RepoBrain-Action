# Sprint 13 Patch Validator Micro-Refactor

## 1. Purpose

Perform a narrow behavior-preserving micro-refactor of `repobrain/patch_validator.py` after Sprint 12 characterization coverage pinned the current patch validator contract.

## 2. Repository states and local paths

- Primary repository: `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
  - Branch at sprint start: `main`
  - Starting commit: `3c992ac Merge pull request #106 from alexworkingai/codex/refactor-12-patch-validator-characterization`
- Public external runtime repository: `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
  - Expected branch/state reviewed from sprint instructions only: `codex/sprint-78-fix-lite-candidate`, clean
- Third-party validation repository: `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`
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
- `tests/test_patch_validator.py`
- `docs/refactor/SPRINT_12_PATCH_VALIDATOR_CHARACTERIZATION.md`

## 5. Baseline test result before edit

Baseline checks passed before editing:

- `pytest -q tests/test_patch_validator.py` -> `7 passed`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py` -> `21 passed`
- `pytest -q -k "patch or no_patch or fix"` -> `98 passed, 412 deselected`

## 6. Implementation changes made

Changed only `repobrain/patch_validator.py`.

- Extracted private helper `_result(...)` to centralize validator result payload construction.
- Extracted private helper `_normalize_changed_files(...)` to centralize changed-file normalization.
- Simplified `validate_patch_grounding(...)` by delegating repeated payload construction and normalization while preserving the existing decision tree.

No public function names, return schema, reason codes, threshold behavior, or grounding semantics were changed.

## 7. Behavior-preservation analysis

The refactor is internal-only.

Preserved deliberately:

- `NO_PATCH` handling for empty payloads
- invalid unified-diff classification behavior
- touched-file extraction and missing-touched-file rejection
- placeholder patch rejection
- PR grounding rejection for unrelated files
- grounded valid-patch acceptance behavior
- all reason codes and `reason_short` strings
- all public output wording and command behavior
- Fix-Lite manual-only and `NO_PATCH` governance

## 8. Tests run

- `pytest -q tests/test_patch_validator.py`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `pytest -q -k "patch or no_patch or fix"`
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

## 9. Risks and rollback notes

- Risk is low because the change is isolated to a private helper extraction inside `patch_validator.py` and is covered by Sprint 12 characterization tests plus broader patch/no-patch validation.
- If rollback is needed, reverting this sprint should be straightforward because the runtime contract was not expanded and no external interfaces changed.

## 10. Explicit statement

No runtime behavior was intentionally changed in Sprint 13.
