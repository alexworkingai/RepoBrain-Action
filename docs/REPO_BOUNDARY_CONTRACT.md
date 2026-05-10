# Repo Boundary Contract

## 1. Purpose

This document is the canonical repository ownership boundary after accepted
Sprint 78 behavior and Refactor Sprints 0–6.

Use it as the default contract for future refactoring so we preserve:

- current command truth,
- cross-repo ownership clarity,
- bounded external surfaces,
- regression and governance guarantees.

Refactor phase closeout reference:

- `docs/refactor/REFACTOR_PHASE_CLOSEOUT.md`

## 2. Current Command Truth

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
- `fix` = Fix-Lite Candidate manual-only patch suggestion

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

## 3. Repository Responsibilities

### 3.1 RepoBrain-Action Owns

`RepoBrain-Action` remains the core/docs/tests repository. It owns:

- historical/core repository role
- docs/tests/current-truth alignment
- capability matrix
- user/operator guide
- TKYA/TopoCore contracts
- governance and regression tests
- action packaging where still relevant to core product behavior
- external CLI ask-only bounded secondary surface
- MCP ask-only bounded secondary surface
- supported/unsupported matrix truth
- regression coverage for unsupported-command honesty
- no-autofix/no-patch/no-file-modification guarantees

### 3.2 RepoBrain-Action Does Not Own

`RepoBrain-Action` does not own:

- public external GitHub runtime host
- canonical reusable external workflow
- canonical public install template
- community install runtime
- third-party validation repository content
- live validation PR branch content

### 3.3 repobrain-community Owns

`repobrain-community` owns:

- public external runtime host
- canonical reusable GitHub workflow
- community install kit
- canonical public external GitHub foundation runtime
- canonical public install template
- public onboarding/install docs

### 3.4 elen-mcp-prod_v2 Role

`elen-mcp-prod_v2` is:

- a validation-only repository
- the live PR validation surface
- not a source of current RepoBrain-Action runtime truth

Operational note:

- do not touch pre-existing untracked `artifacts/` content there unless
  explicitly tasked

## 4. Retired From RepoBrain-Action

These artifacts were retired from `RepoBrain-Action`:

- `.github/workflows/repobrain_external_foundation.yml`
- `docs/repobrain_template.yml`
- `docs/packaging/repobrain_external_github_foundation_template.yml`

Why they were retired:

- they were stale local copies
- canonical public workflow/template ownership moved to
  `repobrain-community`
- removing them did not change active runtime behavior

## 5. Historical Docs Policy

Older trial and benchmark documents may preserve Sprint 59-era evidence, but
they must be labeled historical and must not override current Sprint 78 truth.

Key historical examples:

- `docs/trials/external_repo_trial_01_elen_mcp.md`
- `docs/benchmarks/external_trial_01_elen_mcp_report.md`

Historical material may retain older wording when needed for evidence, but it
must not be used as current operator guidance.

## 6. External CLI / MCP Policy

External CLI ask-only remains a bounded secondary surface in
`RepoBrain-Action`.

MCP ask-only remains a bounded secondary surface in `RepoBrain-Action`.

`repobrain/external_flow.py` is still core regression-supporting code because
it underpins:

- `scripts/run_github.py --mode external`
- `tests/test_external_flow.py`
- MCP ask execution paths that still depend on `external_flow`

Do not remove these without a dedicated implementation sprint and a full
regression/live validation plan:

- `repobrain/external_flow.py`
- `scripts/run_github.py --mode external`
- `tests/test_external_flow.py`

## 7. Future Refactor Guardrails

Future refactors must preserve:

- supported/unsupported command honesty
- no-autofix/no-patch/no-file-modification guarantees
- TKYA/TopoCore contract guards
- audit/evidence metadata
- current docs truth
- local validation gates
- live PR validation discipline for runtime-impacting changes

## 8. Forbidden Reintroductions

Do not reintroduce into `RepoBrain-Action`:

- stale local external workflow copies
- stale local install-template copies
- ask-only public GitHub foundation docs as current truth
- review/fix unsupported wording for the current public external GitHub
  foundation
- unsafe autofix claims
- unsafe full-review claims
- unsafe security or safe-to-merge claims

## 9. Acceptance Policy

Acceptance policy after this contract freeze:

- local green is required but not sufficient for runtime-impacting changes
- runtime-impacting changes require live GitHub PR UI validation
- docs-only changes can be locally accepted if they do not alter runtime
  behavior and they preserve current truth
