# Sprint 8: Runtime Entrypoint Dependency Map

## 1. Purpose

This sprint creates a precise dependency map of `RepoBrain-Action` runtime
entrypoints before any code refactoring begins.

The goal is to identify which entrypoints, modules, tests, and docs are:

- active and must remain
- legacy but still regression-protecting
- plausible refactor candidates later
- unsafe to remove
- candidates for a future surgical cleanup sprint

This sprint is analysis/docs-only. No runtime behavior changes are made.

## 2. Repository States and Local Paths

- Primary repository:
  `D:\ARIADNA_Minsk\1MyProjects\RepoBrain-Action`
- Public external runtime repository:
  `D:\ARIADNA_Minsk\1MyProjects\repobrain-community`
- Third-party validation repository:
  `D:\ARIADNA_Minsk\1MyProjects\elen-mcp-prod_v2`

At Sprint 8 start:

- `RepoBrain-Action`: `codex/refactor-7-repo-boundary-contract-freeze`
- `repobrain-community`: `codex/sprint-78-fix-lite-candidate`
- `elen-mcp-prod_v2`: `test/sprint-73-guidance-live-validation`

## 3. Current Sprint 78 Truth

External GitHub foundation supports:

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

## 4. Boundary Contract Summary

Using `docs/REPO_BOUNDARY_CONTRACT.md` as canonical reference:

- `RepoBrain-Action` owns core/docs/tests/current-truth alignment, TKYA/TopoCore
  contracts, governance and regression tests, the external CLI ask-only
  secondary surface, and the MCP ask-only secondary surface.
- `RepoBrain-Action` does not own the public external GitHub runtime host, the
  canonical reusable workflow, the canonical public install template, or
  validation-repo content.
- `repobrain-community` owns the public external runtime host, reusable
  workflow host, community install kit, and canonical public template.
- `elen-mcp-prod_v2` remains validation-only and must not be treated as a
  source of current runtime truth.

## 5. Runtime Entrypoint Map

### 5.1 Primary GitHub Action Surface

1. `.github/workflows/repobrain.yml`
   - active workflow entrypoint
   - triggers on `issue_comment` and `workflow_dispatch`
   - checks out repo and invokes local composite action via `uses: ./.`

2. `action.yml`
   - composite action entrypoint
   - installs dependencies and runs `python scripts/run_github.py`
   - passes `GITHUB_TOKEN`, dry-run inputs, issue number, and TKY mode

3. `scripts/run_github.py`
   - CLI/runtime launcher
   - `--mode github` path delegates to `repobrain.github_flow.run_github_flow`
   - writes audit/evidence/benchmark outputs after the GitHub flow completes

4. `repobrain/github_flow.py`
   - main GitHub-mode orchestrator
   - parses `/repobrain` commands via `repobrain.commands.parse_command`
   - handles:
     - `help`
     - `ask`
     - `locate`
     - `explain`
     - `review`
     - `verify`
     - `fix`
   - owns event parsing, GitHub client calls, PR metadata fetch, audit
     assembly, formatting/rendering selection, verification orchestration,
     check-run publishing, and artifact writing

### 5.2 External CLI Surface

1. `scripts/run_github.py --mode external`
   - active external CLI entrypoint
   - builds `ExternalFlowInput`
   - delegates to `repobrain.external_flow.run_external_flow`

2. `repobrain/external_flow.py`
   - bounded ask-only runtime
   - blocks non-ask commands with `UNSUPPORTED_COMMAND`
   - loads repo config, builds/loads index, retrieves evidence, and answers via
     `LocalTKYProvider`

### 5.3 MCP Surface

1. `scripts/run_mcp_surface.py`
   - CLI adapter for MCP-style request/response execution
   - loads payload, normalizes request, and prints JSON response

2. `repobrain/mcp_surface.py`
   - active MCP request handler
   - supports only capability `ask`
   - blocks unsupported capabilities with `UNSUPPORTED_CAPABILITY`
   - reuses `repobrain.external_flow.run_external_flow` for actual ask
     execution

### 5.4 TKYA / TopoCore / Local Provider Stack

1. `repobrain/tky_local.py`
   - bridges retrieval candidates into TKYA engine requests
   - builds `EngineRequest` objects and returns normalized `TKYResult`

2. `repobrain/tky_engine.py`
   - canonical engine protocol and dataclasses
   - defines:
     - `EngineCandidate`
     - `EngineQuery`
     - `EngineRequest`
     - `EngineSecurity`
     - `EngineDecision`
     - `TKYEngine` protocol

3. `repobrain/tkya/engine.py`
   - engine selector and backend loader
   - chooses Lite vs v5 vendor backend
   - installs remote guards by default
   - exposes `get_engine()` and `describe_engine_instance()`

4. `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
   - vendor-backed advanced backend
   - not an entrypoint by itself, but a runtime-selected dependency

### 5.5 Review / Fix / Verification / Rendering Support

These are not direct top-level entrypoints, but they are core dependencies of
`repobrain/github_flow.py`:

- `repobrain/ask.py`
- `repobrain/review.py`
- `repobrain/output_md.py`
- `repobrain/verify.py`
- `repobrain/verification_runner.py`
- `repobrain/patch_governance.py`
- `repobrain/patch_targeting.py`
- `repobrain/patch_validator.py`
- `repobrain/review_validator.py`
- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`

## 6. Test Coverage Map

### 6.1 GitHub Action / `run_github_flow` Coverage

Representative tests:

- `tests/test_github_dryrun.py`
- `tests/test_github_post_mode.py`
- `tests/test_audit_schema.py`
- `tests/test_bot_guard.py`
- `tests/test_ai_quota_snapshot_written.py`
- `tests/test_command_profile_surface.py`
- `tests/test_review_command_routing.py`
- `tests/test_reaction_logic.py`
- `tests/test_remote_fallback.py`
- `tests/test_rollout_policy.py`
- `tests/test_security_block.py`
- `tests/test_incremental_audit_visibility.py`
- `tests/test_rd_audit_integration.py`

What they protect:

- event/comment handling
- help output and command parsing behavior
- review PR-context gating
- profile policy behavior
- audit payload writing
- GitHub posting/reaction behavior
- remote fallback and rollout rules
- security refusal paths

### 6.2 External CLI Coverage

- `tests/test_external_flow.py`

What it protects:

- active `ask` success path
- honest unsupported block for `review`
- retention of `UNSUPPORTED_COMMAND` behavior

### 6.3 MCP Surface Coverage

- `tests/test_mcp_surface.py`

What it protects:

- payload normalization
- unsupported capability blocking
- missing query blocking
- successful MCP ask execution through shared external flow

### 6.4 Review / Fix / No-Patch / Governance Coverage

Representative tests:

- `tests/test_patch_validator.py`
- `tests/test_patch_extract.py`
- `tests/test_patch_extractor.py`
- `tests/test_fix_no_patch_rendering.py`
- `tests/test_fix_governance_localized_evidence.py`
- `tests/test_fix_llm_fallback.py`
- `tests/test_patch_governance.py`
- `tests/test_patch_targeting.py`
- `tests/test_review_batch_planner.py`
- `tests/test_review_command_routing.py`
- `tests/test_review_*`
- `tests/test_e2e_report_requirements.py`

What they protect:

- `NO_PATCH` classification
- patch grounding and localization gates
- review rendering and routing
- fix/governance safety behavior
- evidence-backed patch/refusal semantics

### 6.5 TKYA / Engine / Contract Coverage

Representative tests:

- `tests/test_tkya_engine.py`
- `tests/test_local_policy_context.py`
- `tests/test_tkya_evidence_pack.py`
- `tests/test_contract_guard.py`
- `tests/test_tkya_legacy_references_removed.py`
- `python scripts/check_tkya_contract_guard.py`

What they protect:

- engine selection and fallback behavior
- v5 vendor loading
- remote guard defaults
- engine decision dataclass compatibility
- TKYA contract guard discipline

### 6.6 Docs / Current-Truth / Boundary Coverage

- `tests/test_external_github_foundation_workflow.py`
- `tests/test_github_app_onboarding_docs.py`
- `tests/test_env_reference_is_current.py`

What they protect:

- public external foundation current truth
- canonical community host/template references
- onboarding/current-doc consistency

## 7. Documentation Reference Map

| File | Reference role | Notes |
|---|---|---|
| `docs/REPO_BOUNDARY_CONTRACT.md` | boundary guidance | canonical ownership and refactor guardrail doc |
| `README.md` | current operational guidance | top-level mode summary and doc index |
| `docs/EXTERNAL_MODE.md` | current operational guidance | distinguishes public GitHub foundation from CLI/MCP ask-only surfaces |
| `docs/USER_GUIDE.md` | current operational guidance | user-facing capability summary |
| `docs/OPERATOR_QUICKSTART.md` | current operational guidance | operator validation flow across GitHub, external CLI, and MCP |
| `docs/benchmarks/current_capabilities_matrix.md` | current operational guidance | accepted capability matrix after Sprint 78 |
| `docs/packaging/CAPABILITY_SURFACES.md` | boundary guidance | compact surface matrix |
| `docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md` | boundary guidance | local pointer to community-owned public runtime/template host |
| `docs/packaging/PACKAGING_OVERVIEW.md` | boundary guidance | packaging-layer overview, not detailed runtime guide |
| `docs/startup/READINESS_MATRIX.md` | current operational guidance | bounded readiness summary, including external CLI/MCP limits |
| `docs/governance/ACCEPTANCE_POLICY.md` | boundary guidance | local-vs-live acceptance rules |
| `docs/trials/external_repo_trial_01_elen_mcp.md` | historical-only | historical trial artifact |
| `docs/benchmarks/external_trial_01_elen_mcp_report.md` | historical-only | historical benchmark artifact |
| `docs/refactor/*` | refactor/audit-only | inventory and reasoning record, not operator truth |

## 8. File / Module Classification Table

| Path | Classification | Why |
|---|---|---|
| `action.yml` | `KEEP_ACTIVE_RUNTIME` | active composite action entrypoint for GitHub Actions |
| `.github/workflows/repobrain.yml` | `KEEP_ACTIVE_RUNTIME` | active workflow trigger surface for GitHub mode |
| `scripts/run_github.py` | `KEEP_ACTIVE_RUNTIME` | runtime launcher for GitHub mode and external CLI mode |
| `repobrain/github_flow.py` | `KEEP_ACTIVE_RUNTIME` | central GitHub orchestration path for help/ask/review/fix/verify |
| `repobrain/commands.py` | `KEEP_CORE_CONTRACT` | command-surface parser and syntax contract |
| `repobrain/external_flow.py` | `KEEP_ACTIVE_RUNTIME` | active external CLI ask-only runtime and MCP shared dependency |
| `scripts/run_mcp_surface.py` | `KEEP_ACTIVE_RUNTIME` | active MCP adapter entrypoint |
| `repobrain/mcp_surface.py` | `KEEP_ACTIVE_RUNTIME` | active MCP handler, blocks unsupported capabilities, reuses external flow |
| `repobrain/tky_local.py` | `KEEP_CORE_CONTRACT` | bridge from retrieval/runtime into TKYA engine contract |
| `repobrain/tky_engine.py` | `KEEP_CORE_CONTRACT` | canonical engine request/decision datamodel |
| `repobrain/tkya/engine.py` | `KEEP_CORE_CONTRACT` | backend selection, vendor loading, remote-guard enforcement |
| `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py` | `KEEP_CORE_CONTRACT` | vendor backend dependency selected at runtime |
| `repobrain/ask.py` | `KEEP_CORE_CONTRACT` | answer-generation contract shared by external CLI and GitHub-mode QA paths |
| `repobrain/review.py` | `KEEP_CORE_CONTRACT` | review payload/risk heuristics used by GitHub review path |
| `repobrain/output_md.py` | `KEEP_CORE_CONTRACT` | user-visible markdown rendering for ask/review/fix/refuse/wait |
| `repobrain/verify.py` | `KEEP_CORE_CONTRACT` | verify-report shaping for GitHub verification summaries |
| `repobrain/verification_runner.py` | `KEEP_CORE_CONTRACT` | trusted/dynamic verification execution and report contract |
| `repobrain/patch_governance.py` | `KEEP_CORE_CONTRACT` | patch/no-patch governance contract builder |
| `repobrain/patch_targeting.py` | `KEEP_CORE_CONTRACT` | localized patch target selection logic |
| `repobrain/patch_validator.py` | `KEEP_CORE_CONTRACT` | patch grounding and `NO_PATCH` classification contract |
| `repobrain/review_validator.py` | `KEEP_CORE_CONTRACT` | evidence-backed review finding validation |
| `repobrain/fix/patch_extract.py` | `REFACTOR_CANDIDATE` | focused fix-support utility; likely simplifiable later but safety-sensitive now |
| `repobrain/fix/patch_guard.py` | `REFACTOR_CANDIDATE` | focused fix-support utility; likely simplifiable later but safety-sensitive now |
| `tests/test_external_flow.py` | `KEEP_REGRESSION_GUARD` | guards external CLI ask-only and unsupported-command honesty |
| `tests/test_mcp_surface.py` | `KEEP_REGRESSION_GUARD` | guards MCP ask-only and unsupported-capability honesty |
| `tests/test_external_github_foundation_workflow.py` | `KEEP_REGRESSION_GUARD` | guards current doc truth and community ownership references |
| `tests/test_review_command_routing.py` | `KEEP_REGRESSION_GUARD` | guards PR-context routing for review |
| `tests/test_patch_validator.py` | `KEEP_REGRESSION_GUARD` | guards patch grounding and `NO_PATCH` semantics |
| `docs/REPO_BOUNDARY_CONTRACT.md` | `KEEP_CORE_CONTRACT` | canonical ownership boundary and anti-regression refactor guide |
| `docs/trials/external_repo_trial_01_elen_mcp.md` | `RETIRE_CANDIDATE` | historical, labeled artifact; not current truth |
| `docs/benchmarks/external_trial_01_elen_mcp_report.md` | `RETIRE_CANDIDATE` | historical benchmark artifact; not current truth |
| `scripts/run_ask.py` | `HUMAN_DECISION` | adjacent runtime helper not audited as a primary command surface here; likely active but needs its own cleanup scope if changed |
| `scripts/run_index.py` | `HUMAN_DECISION` | operational helper with potential indexing impact; not safe to classify as cleanup target without a dedicated sprint |
| `scripts/check_install_readiness.py` | `KEEP_CORE_CONTRACT` | readiness contract generator used by the workflow/operator path |

## 9. Answers to Special Questions

### 1. What are the current runtime entrypoints in RepoBrain-Action?

Current runtime entrypoints are:

- `.github/workflows/repobrain.yml`
- `action.yml`
- `scripts/run_github.py`
- `scripts/run_mcp_surface.py`

Operationally, these feed into:

- `repobrain.github_flow.run_github_flow`
- `repobrain.external_flow.run_external_flow`
- `repobrain.mcp_surface.handle_mcp_request`

### 2. Which entrypoints are public or user-facing?

Public or user-facing entrypoints:

- `.github/workflows/repobrain.yml` + `action.yml` for GitHub-mode users
- `scripts/run_github.py --mode external` for external CLI users
- `scripts/run_mcp_surface.py` for MCP/integration users

### 3. Which entrypoints are internal/regression-only?

Internal/regression-oriented surfaces include:

- `tests/test_external_flow.py`
- `tests/test_mcp_surface.py`
- `tests/test_external_github_foundation_workflow.py`
- `tests/test_patch_validator.py`
- `tests/test_tkya_engine.py`
- `scripts/check_tkya_contract_guard.py`

These are not runtime entrypoints for users, but they protect accepted behavior.

### 4. Which modules are shared between external CLI and MCP?

Shared between external CLI and MCP:

- `repobrain.external_flow`
- `repobrain.ask`
- `repobrain.tky_local`
- `repobrain.tky_engine`
- `repobrain.tkya.engine`
- retrieval/index/config dependencies used by `external_flow`

### 5. Which modules are shared between GitHub Action mode and external CLI / MCP mode?

Most important shared modules:

- `repobrain.ask`
- `repobrain.tky_local`
- `repobrain.tky_engine`
- `repobrain.tkya.engine`
- retrieval/index/config modules
- evidence/audit-formatting layers in different degrees

GitHub mode is broader because it adds:

- `repobrain.github_flow`
- review/fix/verify orchestration
- GitHub publishing and artifact logic

### 6. Which modules must not be touched before live PR UI validation is planned?

Highest-risk files before live validation planning:

- `action.yml`
- `.github/workflows/repobrain.yml`
- `scripts/run_github.py`
- `repobrain/github_flow.py`
- `repobrain/output_md.py`
- `repobrain/patch_governance.py`
- `repobrain/patch_targeting.py`
- `repobrain/patch_validator.py`
- `repobrain/review_validator.py`
- `repobrain/tky_local.py`
- `repobrain/tkya/engine.py`

These either affect live PR UX, patch/no-patch safety, or core engine routing.

### 7. Which files are plausible first code-refactor candidates?

Most plausible first code-refactor candidates:

- `repobrain/github_flow.py`
  - extremely large orchestrator
  - likely splittable into command-specific service modules later
- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`
- `repobrain/patch_targeting.py`

These look refactorable later without changing the repository boundary model, as
long as behavior and tests stay stable.

### 8. Which files are unsafe to refactor before stronger tests or live validation?

Unsafe early targets:

- `repobrain/github_flow.py`
- `action.yml`
- `.github/workflows/repobrain.yml`
- `scripts/run_github.py`
- `repobrain/external_flow.py`
- `repobrain/mcp_surface.py`
- `repobrain/tky_local.py`
- `repobrain/tkya/engine.py`

Reason:

- they sit on live entrypoints or on shared runtime behavior across multiple
  surfaces
- regressions here would not be isolated to one command path

### 9. What is the smallest safe Sprint 9 implementation candidate?

Smallest safe Sprint 9 candidate:

- a code-structure-only extraction of narrow fix support utilities around patch
  extraction/guarding or patch-targeting helpers, without changing user-visible
  behavior

Not recommended as the first cleanup:

- splitting `github_flow.py` immediately
- touching live workflow/action entrypoints
- changing `external_flow.py` / `mcp_surface.py` coupling

## 10. Recommended Smallest Safe Sprint 9

Recommended Sprint 9:

- a narrowly scoped internal cleanup around fix-support helper modules, such as:
  - `repobrain/fix/patch_extract.py`
  - `repobrain/fix/patch_guard.py`
  - or a thin extraction around patch-target ranking helpers

Why this is the smallest safe candidate:

- it avoids workflow entrypoints
- it avoids direct GitHub posting behavior
- it avoids shared external CLI/MCP execution paths
- it preserves current boundary ownership while still reducing local complexity

## 11. Risks and Live-Validation Needs

Key risks:

1. `repobrain/github_flow.py` is the central orchestrator for live GitHub-mode
   behavior and artifact publication; a casual refactor here could break multiple
   surfaces at once.
2. `repobrain.external_flow.py` is shared by external CLI and MCP ask execution;
   refactoring it affects both secondary surfaces.
3. `repobrain/tky_local.py` and `repobrain/tkya/engine.py` sit on the contract
   seam between retrieval/runtime and TKYA decisions.
4. patch/no-patch safety guarantees depend on several cooperating modules rather
   than one single fix entrypoint.

Live-validation need:

- any runtime-impacting change to GitHub-mode orchestration, patch governance,
  or output rendering should require a planned live PR UI validation cycle in
  addition to local green tests

## 12. Validation Results

Validation was run from `RepoBrain-Action` after adding this runtime dependency
map:

- `ruff check .`
- `pytest -q`
- `python scripts/gen_env_reference.py`
- `python scripts/check_env_reference_up_to_date.py`
- `python scripts/usersafe_scan.py`
- `python scripts/check_tkya_contract_guard.py`
- `git diff --check`
- `git status --short`

## 13. Explicit Statement

No runtime behavior was intentionally changed in Sprint 8.
