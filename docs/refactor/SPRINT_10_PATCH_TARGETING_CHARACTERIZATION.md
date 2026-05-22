# Sprint 10 Patch Targeting Characterization

## 1. Purpose

Add narrow characterization coverage around `repobrain/patch_targeting.py` before any future surgical refactor, while preserving current Fix-Lite, `NO_PATCH`, and bounded no-action behavior.

## 2. Repository states and local paths

- Primary repository: `<LOCAL_REPO_ROOT>`
  - Branch at sprint start: `main`
  - Starting commit: `93487bc Merge pull request #104 from alexworkingai/codex/refactor-9-fix-helper-microrefactor`
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

- `repobrain/patch_targeting.py`
- `repobrain/patch_validator.py`
- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`
- `tests/test_patch_targeting.py`
- `tests/test_patch_validator.py`
- `tests/test_patch_extract.py`
- `tests/test_patch_guard.py`
- `tests/test_fix_governance_localized_evidence.py`
- `tests/test_fix_no_patch_rendering.py`
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`
- `docs/refactor/SPRINT_9_FIX_HELPER_MICROREFACTOR.md`

## 5. Existing coverage summary

Existing tests already covered:

- broad PRs without localized evidence returning no patch target
- localized issue selection with file and hunk caps
- patch grounding validation for placeholder, unrelated, grounded, and explicit `NO_PATCH` outcomes
- patch extraction behavior for diff fences, raw diffs, JSON `no_patch`, and missing patch text
- patch guard behavior for empty output, placeholder content, generic prose, and real diffs
- fix-localization gating and safe `no_patch` rendering

The main remaining gaps were around skipped malformed file entries, ambiguous competing code targets without localized signals, and deterministic ranking when equally scored localized targets compete.

## 6. Characterization tests added

Added to `tests/test_patch_targeting.py`:

- `test_missing_filename_entries_are_skipped`
  - confirms empty/missing filename entries do not become patch targets
- `test_competing_code_targets_without_localized_signals_remain_no_patch`
  - confirms multiple code-file candidates still collapse to `none` when localized evidence is required and absent
- `test_equal_rank_localized_targets_are_selected_deterministically_by_path`
  - confirms current tie-breaking remains deterministic by path ordering for equally scored localized targets

## 7. Any implementation changes made, if any

- None.
- `repobrain/patch_targeting.py` was not modified in this sprint.

## 8. Behavior-preservation statement

This sprint was test-first and behavior-preserving.

- No command behavior changed.
- No Fix-Lite semantics changed.
- No `NO_PATCH` governance changed.
- No patch application behavior was added.
- No file modification behavior was added.
- No public output wording changed.

## 9. Risks and rollback notes

- Risk is low because the sprint adds only characterization coverage plus this note.
- If any follow-up refactor later conflicts with these tests, the tests should be treated as the current contract until a dedicated behavior-change sprint explicitly redefines it.
- Rollback is straightforward because no runtime code changed in this sprint.

## 10. Validation results

Planned validation for this sprint:

- `ruff check .`
- `pytest -q`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `pytest -q -k "patch or no_patch or fix"`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 11. Explicit statement

No runtime behavior was intentionally changed in Sprint 10.
