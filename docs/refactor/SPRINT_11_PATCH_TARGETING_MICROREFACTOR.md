# Sprint 11 Patch Targeting Micro-Refactor

## 1. Purpose

Perform a narrow behavior-preserving micro-refactor of `repobrain/patch_targeting.py` after Sprint 10 characterization coverage pinned the current patch-targeting contract.

## 2. Repository states and local paths

- Primary repository: `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
  - Branch at sprint start: `codex/refactor-10-patch-targeting-characterization`
  - Starting commit: `e959962 Refactor tests: characterize patch targeting behavior`
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

- `repobrain/patch_targeting.py`
- `tests/test_patch_targeting.py`
- `docs/refactor/SPRINT_10_PATCH_TARGETING_CHARACTERIZATION.md`

## 5. Baseline test result before edit

Baseline checks passed before editing:

- `pytest -q tests/test_patch_targeting.py` -> `5 passed`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py` -> `18 passed`

## 6. Implementation changes made

Changed only `repobrain/patch_targeting.py`.

- Extracted private dataclass `_PatchTargetAssessment` to carry a scored target plus localized/query-match flags.
- Extracted private helper `_assess_patch_target(...)` to centralize per-file scoring and classification.
- Simplified `select_patch_targets(...)` so the outer loop now coordinates normalization, counter accumulation, and final selection while reusing the helper.

No public function names, return schema, reason codes, score values, thresholds, or ordering logic were changed.

## 7. Behavior-preservation analysis

The refactor is internal-only.

Preserved deliberately:

- target ranking weights
- likely-fixable vs context-only thresholds
- deterministic tie-break by `path`
- refusal behavior when localized evidence is required and absent
- selected file/hunk capping behavior
- Fix-Lite manual-only and `NO_PATCH` governance
- all public output wording and command behavior

## 8. Tests run

- `pytest -q tests/test_patch_targeting.py`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `ruff check .`
- `pytest -q`
- `pytest -q tests/test_patch_targeting.py`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `pytest -q -k "patch or no_patch or fix"`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 9. Risks and rollback notes

- Risk is low because the change is isolated to a private helper extraction inside `patch_targeting.py` and is covered by the Sprint 10 characterization tests plus broader patch/no-patch validation.
- If rollback is needed, reverting this sprint should be straightforward because the runtime contract was not expanded and no external interfaces changed.

## 10. Explicit statement

No runtime behavior was intentionally changed in Sprint 11.
