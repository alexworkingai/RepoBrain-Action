# Sprint 3 External CLI / Self-Test Surface Audit

## 1. Purpose

Sprint 3 is an audit-only review of the remaining external CLI and self-test surface inside `RepoBrain-Action` after:

- Sprint 1 truth freeze,
- Sprint 2 retirement of stale legacy workflow/template copies, and
- migration of the canonical public external runtime host to `repobrain-community`.

This sprint does not delete, move, or refactor runtime behavior. It records what still appears required, what looks historical, and what should be handled later in a dedicated follow-up sprint.

## 2. Repository States and Local Paths

Primary repository under audit:

- `<LOCAL_REPO_ROOT>`

Reference repositories only:

- `<LOCAL_PROJECT_ROOT>\repobrain-community`
- `<EXTERNAL_CONSUMER_REPO>`

Observed branch state at audit start:

- `RepoBrain-Action`: `codex/refactor-2-legacy-external-retirement` @ `f5fd3c4`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate` @ `7969932`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation` @ `0835bd2`

Repository role boundaries used in this audit:

- `RepoBrain-Action`: historical/core repo, docs/tests/current-truth alignment, governance and regression coverage, not the public external runtime host
- `repobrain-community`: canonical public external runtime host and reusable workflow host
- `elen-mcp-prod_v2`: validation-only repo and live PR validation surface

## 3. Current Sprint 78 Truth

Current public external GitHub foundation commands:

- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask <question>`
- `/repobrain review`
- `/repobrain fix`

Current meanings:

- `doctor` = setup health card
- `help` = command truth and boundaries
- `ask` = repo/PR/guidance-aware bounded answer
- `review` = bounded read-only Review Candidate
- `fix` = bounded Fix-Lite Candidate manual-only patch suggestion

Mandatory Fix-Lite boundary:

- `No patch was applied. No files were modified.`

Mandatory non-claims remain in force:

- no autofix
- no patch application
- no file modification
- no commit creation
- no branch pushing
- no PR creation
- no full review parity
- no security verdict
- no safe-to-merge claim
- no approval/rejection verdict
- no autonomous repair behavior
- no whole-repo deep analysis

## 4. Audit Scope

Primary audit targets reviewed directly:

- `repobrain/external_flow.py`
- `tests/test_external_flow.py`
- `scripts/run_github.py`
- `tests/test_external_github_foundation_workflow.py`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/startup/READINESS_MATRIX.md`
- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

Second-order dependency and context files reviewed:

- `repobrain/mcp_surface.py`
- `README.md`
- `docs/packaging/CAPABILITY_SURFACES.md`
- `docs/governance/ACCEPTANCE_POLICY.md`
- `docs/refactor/SPRINT_0_REPO_BOUNDARY_INVENTORY.md`
- `docs/refactor/STALE_EXTERNAL_SURFACE_CANDIDATES.md`
- `docs/refactor/KEEP_MOVE_DELETE_MATRIX.md`

## 5. Search / Reference Evidence Summary

Repo-wide search terms included:

- `external_flow`
- `--mode external`
- `mode external`
- `external CLI`
- `external mode`
- `UNSUPPORTED_COMMAND`
- `test_external_flow`
- `test_external_github_foundation_workflow`
- `elen-mcp-prod_v2`
- `Elen-MCP-v.2.2.0`
- `repobrain-community`
- `public runtime host`
- `validation repo`
- `ask-only`
- `review unsupported`
- `fix unsupported`

Key evidence from the search pass:

1. `repobrain/external_flow.py` is still an active dependency.
   - It is called by `scripts/run_github.py --mode external`.
   - It is also reused by `repobrain/mcp_surface.py` for MCP `ask` execution.

2. `tests/test_external_flow.py` still protects two live behaviors.
   - supported local/external `ask` path returns `ANSWER`
   - unsupported `review` path blocks with `UNSUPPORTED_COMMAND`

3. `tests/test_external_github_foundation_workflow.py` is no longer about the deleted local legacy workflow copy.
   - It asserts that the template points to `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`
   - It also checks current doc truth in `docs/EXTERNAL_MODE.md` and `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md`

4. Current-facing docs still intentionally describe two distinct external surfaces.
   - public GitHub foundation hosted through `repobrain-community`
   - local external CLI ask-only path owned in `RepoBrain-Action`

5. Trial artifacts for `alexworkingai/Elen-MCP-v.2.2.0` remain present and are still referenced from README/docs, but they encode older trial history.
   - `docs/trials/external_repo_trial_01_elen_mcp.md`
   - `docs/benchmarks/external_trial_01_elen_mcp_report.md`

## 6. File-by-File Classification Table

| Path | Current role in repo | Classification | Why |
|---|---|---|---|
| `repobrain/external_flow.py` | Implements bounded external CLI `ask` execution and explicit unsupported blocking | `KEEP_CORE_REGRESSION` | Still used by `scripts/run_github.py --mode external` and by `repobrain/mcp_surface.py`; removing it would change current CLI and MCP behavior |
| `tests/test_external_flow.py` | Regression coverage for supported external CLI `ask` and unsupported `review` blocking | `KEEP_CORE_REGRESSION` | Protects a still-live local/no-GitHub-runtime path and explicit unsupported behavior |
| `scripts/run_github.py` external branch | CLI entrypoint for bounded external ask-only execution | `KEEP_CORE_REGRESSION` | Still documented, still covered by tests, still used for local/external evaluation and acceptance policy |
| `tests/test_external_github_foundation_workflow.py` | Contract test for current public template and current doc truth | `KEEP_CORE_REGRESSION` | It tests current references to `repobrain-community`, not the retired local workflow copy |
| `docs/EXTERNAL_MODE.md` | Current-facing explanation of public foundation vs CLI external vs MCP surfaces | `KEEP_CURRENT_DOC_TRUTH` | Correctly distinguishes the canonical public host from the ask-only CLI path |
| `docs/USER_GUIDE.md` | Current-facing capability summary | `KEEP_CURRENT_DOC_TRUTH` | Still needed to explain bounded external GitHub foundation vs ask-only CLI/MCP surfaces |
| `docs/OPERATOR_QUICKSTART.md` | Operator-facing validation/runbook summary | `KEEP_CURRENT_DOC_TRUTH` | Current-facing and still used for validating both public foundation and CLI/MCP bounded paths |
| `docs/benchmarks/current_capabilities_matrix.md` | Current accepted capability matrix | `KEEP_CURRENT_DOC_TRUTH` | Still needed to show the distinction between external GitHub foundation and CLI/MCP ask-only surfaces |
| `docs/startup/READINESS_MATRIX.md` | Current readiness summary | `KEEP_CURRENT_DOC_TRUTH` | Still accurately distinguishes external GitHub foundation from external CLI ask-only behavior |
| `docs/trials/external_repo_trial_01_elen_mcp.md` | Repo-specific validation runbook tied to `alexworkingai/Elen-MCP-v.2.2.0` | `MOVE_TO_VALIDATION_REPO_CANDIDATE` | Specific to one validation repo and one older trial protocol; no longer the best source of current operational truth |
| `docs/benchmarks/external_trial_01_elen_mcp_report.md` | Historical benchmark/trial narrative | `ARCHIVE_HISTORICAL_CANDIDATE` | Encodes older Sprint 59 trial truth and mojibake in title; useful as history, not as current guide |
| `repobrain/mcp_surface.py` | MCP ask surface adapter reusing `external_flow` | `KEEP_CORE_REGRESSION` | Not a primary target, but shows `external_flow` is still an active dependency |
| `README.md` external sections | Top-level capability and doc index summary | `KEEP_CURRENT_DOC_TRUTH` | Still reflects current split between public foundation and local ask-only CLI |
| `docs/packaging/CAPABILITY_SURFACES.md` | Compact surface matrix | `KEEP_CURRENT_DOC_TRUTH` | Current-facing and still accurate |
| `docs/governance/ACCEPTANCE_POLICY.md` | Acceptance requirements for external CLI and MCP validation | `KEEP_CORE_REGRESSION` | Proves external CLI ask path still matters for acceptance discipline |

## 7. Answers to the Special Questions

### 1. Is `repobrain/external_flow.py` still required as a supported external CLI ask-only surface?

Yes.

Current evidence shows it is still the implementation behind:

- `scripts/run_github.py --mode external`
- `repobrain/mcp_surface.py` ask capability

Removing or retiring it now would alter current CLI and MCP behavior, not just remove an unused helper.

### 2. Is external CLI ask-only still a product surface, or is it now only a historical/bootstrap/test surface after `repobrain-community` became the public runtime host?

It is still a bounded supported surface inside `RepoBrain-Action`, but not the public external GitHub runtime surface.

Best current reading:

- public third-party GitHub-native runtime surface = `repobrain-community`
- local/external CLI ask-only path = retained bounded support and regression surface in `RepoBrain-Action`

So it is not merely historical. It is narrower, secondary, and internal-to-core ownership, but still current.

### 3. Does `scripts/run_github.py --mode external` still need to exist for current development or regression testing?

Yes.

Evidence:

- it is directly documented in `README.md`, `docs/EXTERNAL_MODE.md`, `docs/USER_GUIDE.md`, `docs/OPERATOR_QUICKSTART.md`, and `docs/startup/EXTERNAL_EVALUATION_PATH.md`
- acceptance policy still requires external CLI execution checks on a real target repo path
- tests rely on the underlying `external_flow` behavior

### 4. Does `tests/test_external_flow.py` protect valuable no-GitHub-runtime isolation behavior that should remain even if public runtime moved to `repobrain-community`?

Yes.

It protects:

- a local checkout ask path that does not depend on GitHub issue-comment runtime
- honest unsupported blocking for non-ask commands
- behavior reused by the MCP ask surface through `external_flow`

That makes it more than a historical leftover.

### 5. Does `tests/test_external_github_foundation_workflow.py` still test current public truth, or does it test stale workflow/template behavior?

It still tests current public truth.

Current assertions verify:

- the template points at `repobrain-community` reusable workflow host
- `docs/EXTERNAL_MODE.md` reflects current command truth
- `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md` reflects Review Candidate / Fix-Lite Candidate wording

So it is not guarding the deleted local legacy workflow copy.

### 6. Which files would be dangerous to remove before a live PR validation cycle?

Most dangerous:

- `repobrain/external_flow.py`
- `scripts/run_github.py` external branch
- `repobrain/mcp_surface.py` dependency path through `external_flow`
- `tests/test_external_flow.py`
- `tests/test_external_github_foundation_workflow.py`
- current-facing external docs such as `docs/EXTERNAL_MODE.md`, `docs/USER_GUIDE.md`, `docs/OPERATOR_QUICKSTART.md`, `docs/benchmarks/current_capabilities_matrix.md`, `docs/startup/READINESS_MATRIX.md`

These either protect live bounded behavior or current operator truth.

### 7. Which docs are current-facing and must remain updated?

Current-facing and should remain updated:

- `README.md`
- `docs/EXTERNAL_MODE.md`
- `docs/USER_GUIDE.md`
- `docs/OPERATOR_QUICKSTART.md`
- `docs/benchmarks/current_capabilities_matrix.md`
- `docs/startup/READINESS_MATRIX.md`
- `docs/packaging/CAPABILITY_SURFACES.md`
- `docs/governance/ACCEPTANCE_POLICY.md`

### 8. Which docs should become explicitly historical/archive docs later?

Strongest later archive/historical candidates:

- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

Both are specific to the Elen-MCP validation path and encode older trial-era framing.

### 9. What is the smallest safe Sprint 4 candidate based on this audit?

Smallest safe Sprint 4 candidate:

- docs-only archival/labeling pass for the Elen-MCP trial runbook and benchmark narrative
- optionally trim README/doc indexes so those files are clearly historical rather than current operational guidance

Not recommended for Sprint 4 without a separate implementation scope:

- removing `external_flow`
- removing `scripts/run_github.py --mode external`
- removing `tests/test_external_flow.py`
- changing MCP’s dependency on `external_flow`

## 8. Recommended Next Sprint

Recommended next sprint:

- Sprint 4 should be a docs-only archival and labeling cleanup for validation-specific Elen-MCP materials.

Why this is the smallest safe step:

- it reduces historical/current-truth confusion
- it does not alter CLI or MCP runtime behavior
- it does not weaken regression coverage
- it preserves `repobrain-community` as the canonical public runtime host

## 9. Risks if External CLI Is Removed Too Early

1. It would break a still-documented local bounded surface in `RepoBrain-Action`.
2. It would remove acceptance-policy coverage for external CLI validation on a real repo path.
3. It would break MCP ask execution as currently implemented through `external_flow`.
4. It would reduce no-GitHub-runtime regression coverage for bounded ask behavior and explicit unsupported blocking.
5. It would blur the distinction between:
   - public external GitHub foundation runtime hosted in `repobrain-community`
   - local ask-only CLI/MCP surfaces retained in `RepoBrain-Action`

## 10. Validation Results

Validation run from `RepoBrain-Action` after adding this audit doc:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`
- `git diff --name-only`
- `git diff --stat`

## 11. Final Statement

No runtime behavior was intentionally changed in Sprint 3.
