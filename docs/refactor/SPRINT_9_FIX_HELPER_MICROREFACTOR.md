## Purpose

Perform the first safe post-audit code cleanup in the Fix-Lite helper surface without changing command behavior, public wording, or NO_PATCH governance.

## Repository states and local paths

- Primary repository: `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
- Public runtime reference: `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- Validation repository reference: `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`
- RepoBrain-Action working branch: `codex/refactor-9-fix-helper-microrefactor`

## Current Sprint 78 truth

- External GitHub foundation supports `/repobrain doctor`, `/repobrain help`, `/repobrain ask <question>`, `/repobrain review`, and `/repobrain fix`.
- `/repobrain review` remains bounded read-only Review Candidate behavior.
- `/repobrain fix` remains Fix-Lite Candidate manual-only patch suggestion behavior.
- Mandatory Fix-Lite boundary remains: `No patch was applied. No files were modified.`

## Files inspected

- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`
- `repobrain/patch_targeting.py`
- `repobrain/patch_validator.py`
- `tests/test_patch_extract.py`
- `tests/test_patch_extractor.py`
- `tests/test_patch_guard.py`
- `tests/test_patch_targeting.py`
- `tests/test_patch_validator.py`

## Existing coverage summary

Existing coverage already characterized:

- diff-fence patch extraction
- raw unified diff extraction
- JSON envelope patch extraction through `github_flow` compatibility tests
- explicit `NO_PATCH` token handling
- placeholder patch rejection
- grounded vs ungrounded patch validation
- no-patch validation classification

Coverage was still thin around:

- JSON envelope `no_patch` extraction in the normalized helper
- empty patch-guard input
- generic patch prose without a unified diff

## Characterization tests added, if any

Added narrow characterization coverage in:

- `tests/test_patch_extract.py`
  - JSON envelope `{"result":"no_patch"}` remains a `NO_PATCH` outcome
- `tests/test_patch_guard.py`
  - empty payload remains non-triggering with `EMPTY_OUTPUT`
  - generic patch prose without diff markers remains blocked as `PATCH_GENERIC_TEXT`

These tests lock current helper behavior without introducing new product behavior or implying patch application.

## Implementation changes made, if any

Made a narrow internal cleanup in `repobrain/fix/patch_extract.py`:

- extracted repeated `PatchExtractResult` construction into one private helper
- left extraction order, return codes, flags, and output values unchanged

No runtime entrypoint or command-routing code was modified.

## Behavior-preservation statement

The Sprint 9 cleanup preserves:

- Fix-Lite Candidate manual-only patch suggestion semantics
- NO_PATCH governance
- no patch application behavior
- no file modification behavior
- existing extraction paths and reason codes used by callers/tests

## Risks and rollback notes

- Risk is low because the change is internal to `patch_extract.py` and is covered by targeted helper tests plus broader patch/no-patch tests.
- If rollback is needed, revert the private helper extraction and the added characterization tests together.

## Validation results

Targeted tests:

- `pytest -q tests/test_patch_extract.py tests/test_patch_guard.py tests/test_patch_validator.py`
- `pytest -q -k "patch or no_patch or fix"`

Full validation results are recorded with the sprint closeout report after the repo-wide gate passes.

## Explicit statement

No runtime behavior was intentionally changed in Sprint 9.
