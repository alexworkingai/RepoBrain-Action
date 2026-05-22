# Sprint 14 Patch Guard Characterization

## 1. Purpose

Strengthen characterization coverage around `repobrain/fix/patch_guard.py` before deciding whether a future surgical patch-guard micro-refactor is worth doing.

## 2. Repository states and local paths

- Primary repository: `<LOCAL_REPO_ROOT>`
  - Branch at sprint start: `main`
  - Starting commit: `83bcfe0 Merge pull request #107 from alexworkingai/codex/refactor-13-patch-validator-microrefactor`
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
  - `/repobrain review` may render as `### ✅ PR Review`
  - `/repobrain fix` may render as primary-mode patch operation output
  - bounded behavior and non-claims remain mandatory

## 4. Files inspected

- `repobrain/fix/patch_guard.py`
- `tests/test_patch_guard.py`
- `tests/test_patch_extract.py`
- `tests/test_patch_validator.py`
- `tests/test_patch_targeting.py`
- `tests/test_fix_no_patch_rendering.py`
- `tests/test_fix_governance_localized_evidence.py`
- `docs/refactor/SPRINT_9_FIX_HELPER_MICROREFACTOR.md`
- `docs/refactor/SPRINT_10_PATCH_TARGETING_CHARACTERIZATION.md`
- `docs/refactor/SPRINT_11_PATCH_TARGETING_MICROREFACTOR.md`
- `docs/refactor/SPRINT_12_PATCH_VALIDATOR_CHARACTERIZATION.md`
- `docs/refactor/SPRINT_13_PATCH_VALIDATOR_MICROREFACTOR.md`

## 5. Existing coverage summary

Before Sprint 14, current tests already covered:

- empty payload classification as `EMPTY_OUTPUT`
- placeholder/template-style patch text rejection
- generic patch prose without diff markers as `PATCH_GENERIC_TEXT`
- concrete unified diff payload remaining non-triggering
- neighboring characterization in extraction, targeting, validator, localization gate, and safe `no_patch` rendering paths

The main remaining gaps were around whitespace-only payloads, precedence of placeholder detection when diff markers are present, generic-intro text paired with a real diff, malformed diff-like text that the guard currently leaves for later stages, and deterministic output for representative guard decisions.

## 6. Characterization tests added

Added tests in `tests/test_patch_guard.py`:

- `test_patch_guard_treats_whitespace_only_as_empty_output`
  - confirms whitespace-only output remains equivalent to empty output
- `test_patch_guard_keeps_placeholder_detection_even_with_diff_markers`
  - confirms placeholder detection still wins when diff markers are present
- `test_patch_guard_allows_generic_intro_when_concrete_diff_is_present`
  - confirms current behavior leaves generic intro text alone when a concrete diff is present
- `test_patch_guard_leaves_malformed_diff_like_text_non_triggering`
  - confirms diff-like malformed text currently passes the guard and is left for later layers
- `test_patch_guard_decision_is_deterministic_for_generic_prose`
  - confirms deterministic decision output for representative generic-prose input

## 7. Any implementation changes made, if any

None.

`repobrain/fix/patch_guard.py` was not modified.

## 8. Behavior-preservation statement

Sprint 14 was tests-only.

Preserved deliberately:

- Fix-Lite manual-only behavior
- `NO_PATCH` governance and safe no-action outcomes
- patch extraction behavior
- patch targeting behavior
- patch validation behavior
- patch guard classification behavior
- all public output wording and command behavior

## 9. Risks and rollback notes

- Risk is low because the sprint adds only narrow regression coverage.
- The main residual risk remains that patch-guard behavior is intentionally narrow and some malformed diff-like content is deferred to later stages rather than blocked immediately; Sprint 14 documents that current behavior explicitly instead of changing it.
- If rollback is needed, reverting this sprint should be straightforward because no runtime implementation changed.

## 10. Validation results

- `ruff check .`
- `pytest -q`
- `pytest -q tests/test_patch_guard.py`
- `pytest -q tests/test_patch_targeting.py tests/test_patch_validator.py tests/test_patch_extract.py tests/test_patch_guard.py`
- `pytest -q -k "patch or no_patch or fix"`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 11. Explicit statement

No runtime behavior was intentionally changed in Sprint 14.
