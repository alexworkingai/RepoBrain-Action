# TopoCore v6 Test Coverage Index

## 1. Purpose

Sprint 38 maps TopoCore v6 migration-related tests.

Current truth:

- this index is documentation only
- it does not change test behavior
- it does not add runtime behavior
- it helps explain what is covered and what is not covered

## 2. Current Test Baseline

Current test baseline:

- latest accepted test result from Sprint 37:
  - `pytest` passed with `725` tests
- disabled/default harness check passed
- no `topocore_v6` dependency is required in default CI
- no runtime behavior was intentionally changed

## 3. Test Index by Artifact

| Test file | Covered artifact | Phase | Main coverage | Runtime behavior changed? |
|---|---|---|---|---|
| `tests/test_topocore_v6_adapter_skeleton.py` | `repobrain/topocore_v6_adapter.py` | Phase 1 | Adapter request preview shape, summary-to-policy mapping, safe candidate refs, unsafe metadata blocking, no runtime wiring | No |
| `tests/test_topocore_v6_adapter_stub_compatibility.py` | Adapter plus fake or stub v6-style payloads | Phase 1 | Offline stub compatibility, fake `ExternalDecisionView`-style outputs, product-safe previews, failure taxonomy, no real dependency | No |
| `tests/test_topocore_v6_adapter_real_contract.py` | `repobrain/topocore_v6_adapter.py` | Phase 7 | Dynamic public API loading, real `EngineRequest` mapping, real summary-family policy keys, safe `decide_external` extraction, no runtime wiring | No |
| `tests/test_topocore_backend_selection.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Backend precedence, legacy env rejection, v6-only selection, missing-dependency safe failure, safe v6 normalization, no runtime wiring | No |
| `tests/test_topocore_backend_review_verify.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Review and verify task-family mapping, safe v6 summary-family payloads, no legacy runtime fallback, strict local failure, fix exclusion, no runtime wiring | No |
| `tests/test_topocore_backend_fix_lite.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Fix-lite command-family preservation, conservative v6 fix decision shaping, patch-safety markers, no legacy runtime fallback, strict local failure, no runtime wiring | No |
| `tests/test_topocore_backend_lab_default_policy.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Auto lab-default backend policy, v6-only runtime selection, no silent legacy fallback, strict local failure, command-family coverage, GitHub pin safety | No |
| `tests/test_github_runtime_v6_lab_switch.py` | `action.yml` plus `.github/workflows/repobrain.yml` | Phase 7 | Manual workflow-dispatch backend selection, v6-only supported choices, no default strict mode, no private install, legacy-selector blocking | No |
| `tests/test_github_runtime_v6_dependency_gate.py` | `.github/workflows/repobrain.yml` | Phase 7 | Manual-only private checkout gate, secret-only token handling, strict-mode gating, no default private dependency install | No |
| `tests/test_github_workflow_dispatch_meaningful_v6_path.py` | `.github/workflows/repobrain.yml` plus `scripts/run_github.py` | Phase 7 | Meaningful workflow-dispatch lab command inputs, bounded v6 decision execution evidence, fallback markers, conservative fix-lite evidence, no patch or repo mutation steps | No |
| `tests/test_github_topocore_v6_import_blocker_fix.py` | `.github/workflows/repobrain.yml`, `scripts/check_topocore_v6_runtime_import.py`, `scripts/run_github.py` | Phase 7 | Private-checkout path propagation, runtime import diagnostics, sanitized import/API failure categories, failure evidence artifact coverage, issue-comment safety preservation | No |
| `tests/test_github_optional_tkya_evidence_artifact.py` | `.github/workflows/repobrain.yml` | Phase 7 | Optional TKYA evidence-pack upload handling, preserved lab backend evidence visibility, narrow workflow artifact strictness fix, issue-comment and private-checkout safety preservation | No |
| `tests/test_github_issue_comment_v6_lab_runtime.py` | `.github/workflows/repobrain.yml` | Phase 7 | Controlled issue-comment v6 lab gate, v6-only backend policy, gated private checkout and install, non-fatal issue-comment diagnostics, workflow-dispatch preservation, no patch or repo mutation steps | No |
| `tests/test_github_issue_comment_v6_gate_env_propagation.py` | `.github/workflows/repobrain.yml`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | Gated issue-comment local provider propagation, explicit action backend override, safe TopoCore backend diagnostics, preserved workflow-dispatch path, no legacy runtime re-enable seam | No |
| `tests/test_topocore_v5_runtime_removed.py` | `repobrain/topocore_deprecation.py`, `repobrain/topocore_backend.py`, `repobrain/tky_local.py`, workflow/action metadata | Phase 7 | Runtime-removal metadata, old-env unsupported diagnostics, no v5 fallback, no v5/lite workflow advertising, no patch or raw decision drift | No |
| `tests/test_topocore_v5_vendor_assets_removed.py` | filesystem/workflow/action/static cleanup surfaces | Phase 7 | Vendor directory absence, no vendor imports, no legacy workflow advertising, no canary-v5 residue, no patch or raw decision drift | No |
| `tests/test_topocore_v5_residue_cleanup.py` | docs/runtime/workflow static cleanup surfaces | Phase 7 | Deleted standalone v5 guides, no active lower-case runtime residue, no stale guide references, historical-doc supersession markers, no patch or raw decision drift | No |
| `tests/test_external_github_foundation_workflow.py` | external pilot docs/examples | Phase 7 | Direct RepoBrain-Action pilot install truth, direct caller workflow example, no community-hosted install claims in active pilot docs | No |
| `tests/test_repobrain_community_removed_from_product.py` | active runtime/onboarding/workflow product surfaces | Phase 7 | No repobrain-community dependency in runtime/workflow/action surfaces, no v5/lite reintroduction, no copied private TopoCore source in product repo | No |
| `tests/test_external_command_matrix_docs.py` | Sprint 70 external command matrix documentation and indexes | Phase 7 | External command matrix report exists, v6-only runtime truth is recorded, no v5/community reintroduction in the Sprint 70 evidence layer, indexes link the result | No |
| `tests/test_external_retrieval_quality_docs.py` | Sprint 71 external retrieval-quality documentation and indexes | Phase 7 | External retrieval/evidence quality report exists, v6 backend evidence is recorded, fixed workflow-evidence defect is documented, no v5/community/patch drift in the Sprint 71 evidence layer | No |
| `tests/test_verify_command_productionization.py` | `repobrain/verify.py`, `repobrain/formatting.py`, `repobrain/github_flow.py` | Phase 7 | Verify status-label mapping, source/limitation rendering, permission-safe fallback handling, issue-scope safety preservation, no unsafe merge/security wording, no v5/community/patch drift in verify output | No |
| `tests/test_fix_command_product_path.py` | `repobrain/output_md.py`, `repobrain/github_flow.py` | Phase 7 | Fix proposal/governance rendering, visible no-mutation safety markers, unsafe mutation blocking, issue-scope fix safety preservation, no v5/community/autofix drift in fix output | No |
| `tests/test_external_security_permissions_fork_safety.py` | external workflow example, onboarding docs, readiness guidance, verify/fix security wording | Phase 7 | Minimal external permission baseline, private-action troubleshooting, secret/token degradation docs, fork-safety policy, no `pull_request_target`, no broad write permissions, no v5/community/patch drift in security guidance | No |
| `tests/test_external_onboarding_ux_docs.py` | README plus canonical install, command, and troubleshooting docs | Phase 7 | Canonical external onboarding exists, supported vs unsupported commands are documented honestly, troubleshooting covers observed pilot failures, active docs do not drift back to v5/community/unsafe mutation claims | No |
| `tests/test_release_candidate_readiness_docs.py` | release-readiness docs plus active README/install/command/troubleshooting surfaces | Phase 7 | RC checklist/public-readiness/Marketplace-readiness docs exist, decisions are explicit, private TopoCore boundary remains stated, no v5/community/patch drift in active release-facing docs | No |
| `tests/test_public_scrub_license_topocore_security_positioning.py` | license, release, security, positioning, and active-doc scrub surfaces | Phase 7 | Source-available BYO-LLM license exists, TopoCore private boundary and security policy are documented, active docs are scrubbed of local machine paths and secret-value patterns, public and Marketplace decisions remain explicit, scoring roadmap is documented without runtime drift | No |
| `tests/test_audit_command_scoring.py` | `repobrain/audit_scoring.py` | Phase 7 | 100-point category weights, bounded deterministic repository scoring, strong-vs-sparse fixture calibration, dangerous workflow penalties, confidence and limitation surfaces | No |
| `tests/test_audit_command_github_flow.py` | `repobrain/commands.py`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | `/repobrain audit` parser and route support, issue/PR repository-audit behavior, no-mutation audit markers, honest unsupported command handling, PR metadata usage without live API dependency | No |
| `tests/test_audit_command_docs.py` | command, scoring, release-notes, and Sprint 78 docs | Phase 7 | Audit MVP is documented as implemented, command guide truth stays current, release notes mention the audit MVP, and coverage indexes link the new audit tests | No |
| `tests/test_audit_calibration.py` | `repobrain/audit_scoring.py`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | Expanded private/generated directory exclusions, embedded-config calibration, non-duplicative audit output, and static-scoring limitation visibility | No |
| `tests/test_doctor_command.py` | `repobrain/commands.py`, `repobrain/doctor_status.py`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | `/repobrain doctor` parser and route support, report-only backend markers, token-name-safe diagnostics, fork-boundary messaging, and no-mutation guarantees | No |
| `tests/test_status_command.py` | `repobrain/commands.py`, `repobrain/doctor_status.py`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | `/repobrain status` parser and route support, version/policy rendering, report-only backend markers, PR-context support, and no secret exposure | No |
| `tests/test_doctor_status_docs.py` | command, onboarding, troubleshooting, and Sprint 79 docs | Phase 7 | Doctor/status command truth is documented, install/troubleshooting point users to doctor, Sprint 79 doc exists, and coverage indexes link the new diagnostic tests | No |
| `tests/test_audit_benchmark.py` | `repobrain/audit_scoring.py`, release benchmark docs | Phase 7 | Synthetic sparse/docs-only/CI/risky/mature benchmark ranking, stable repeated runs, private-checkout exclusion, and bounded audit limitations for demo evidence | No |
| `tests/test_microsoft_github_demo_report_docs.py` | release demo and benchmark docs | Phase 7 | Microsoft/GitHub-facing positioning report exists, benchmark report exists, release docs reflect Sprint 80 narrative, and no unsafe approval or partnership claims are introduced | No |
| `tests/test_audit_v6_contract.py` | `repobrain/audit_contract.py` | Phase 7 | `AuditScoreRequestV1` construction, category and weight preservation, evidence bounding, path and token sanitization, and no-mutation constraint payloads | No |
| `tests/test_audit_v6_contract_guard.py` | `repobrain/audit_contract.py` | Phase 7 | `AuditScoreResponseV1` validation, category and score bounds, mutation-flag rejection, unsafe-claim blocking, secret and private-path blocking, and bounded output lists | No |
| `tests/test_audit_v6_backend_integration.py` | `repobrain/audit_v6.py`, `repobrain/github_flow.py`, `repobrain/output_md.py`, `repobrain/topocore_v6_adapter.py` | Phase 7 | Honest static/contract-ready/v6-enriched audit-mode rendering, fake private capability integration, rejected-response downgrade, and no-mutation backend evidence truth | No |
| `tests/test_audit_v6_contract_docs.py` | Sprint 81 contract and release docs | Phase 7 | Contract docs exist, private TopoCore boundary remains explicit, static-versus-v6 roadmap truth is documented, and indexes link Sprint 81 contract tests | No |
| `tests/test_github_issue_comment_v6_pr_path_evidence.py` | `.github/workflows/repobrain.yml`, `action.yml`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | PR-path backend evidence propagation, explicit verify scoped diagnostics, non-PR review/fix scoped behavior, workflow-to-action backend env export, no patch side effects | No |
| `tests/test_github_pr_output_backend_evidence.py` | `repobrain/output_md.py`, `repobrain/github_flow.py` | Phase 7 | Visible PR ask/review/verify backend evidence rendering, safe missing-field normalization, gate=`1` v6 evidence visibility, gate=`0` v5 evidence visibility, scoped unsupported patch-safety preservation | No |
| `tests/test_topocore_v6_local_validation_harness.py` | `scripts/validate_topocore_v6_local.py` | Phase 1/2 | Disabled default, missing dependency behavior, fake local `topocore_v6` path, sanitized JSON artifact mode, `decide_raw` not called | No |
| `tests/test_topocore_v6_decision_diff.py` | `repobrain/topocore_v6_decision_diff.py` | Phase 1/2 | Sanitized v5/v6 snapshot comparison, severity and category mapping, candidate overlap, fix-governance mismatch detection, forbidden field blocking | No |
| `tests/test_topocore_v6_advisory_artifact.py` | `repobrain/topocore_v6_advisory_artifact.py` | Phase 2 | Advisory artifact schema, go/no-go hint, fix conservatism, retention defaults, forbidden field blocking, no runtime wiring | No |
| `tests/test_topocore_v6_shadow_path.py` | `repobrain/topocore_v6_shadow_path.py` | Phase 3 | Disabled skeleton behavior, env flags, safe result shape, no `topocore_v6` dependency, no runtime wiring | No |
| `tests/test_topocore_v6_shadow_path_guardrails.py` | `repobrain/topocore_v6_shadow_path.py` | Phase 3 | No-op guardrails, forbidden input and output handling, artifact flag safety, fail-closed recording, fix conservatism, manual harness unchanged | No |
| `tests/test_topocore_v6_advisory_boundary.py` | `repobrain/topocore_v6_advisory_boundary.py` | Phase 5 | Still-disabled boundary skeleton, delegation safety, forbidden input handling, failure-category normalization, no runtime wiring | No |
| `tests/test_topocore_v6_advisory_boundary_guardrails.py` | `repobrain/topocore_v6_advisory_boundary.py` | Phase 5 | Boundary guardrails, nested forbidden fields, forbidden output checks, no dependency drift, manual harness unchanged, fix conservatism | No |

## 4. Coverage by Safety Area

| Safety area | Covered by | Status | Notes |
|---|---|---|---|
| no `topocore_v6` dependency in default CI | Adapter, decision-diff, artifact, shadow-path, and advisory-boundary tests | Covered | Multiple modules import cleanly without private dependency access. |
| disabled/no-op behavior | Shadow-path and advisory-boundary tests | Covered | Default path stays inert. |
| explicit disabled override | Shadow-path guardrails and advisory-boundary guardrails | Covered | Disabled mode wins over artifact and fail-closed flags. |
| enabled-still-disabled behavior | Shadow-path and advisory-boundary tests | Covered | Enabled flags still do not activate live v6 behavior. |
| forbidden input blocking | Adapter, decision-diff, artifact, shadow-path, and advisory-boundary tests | Covered | Flat and nested unsafe fields are blocked. |
| nested forbidden field blocking | Shadow-path guardrails and advisory-boundary tests | Covered | Nested dictionaries and lists are scanned for unsafe keys. |
| forbidden output prevention | Decision-diff, advisory artifact, shadow-path guardrails, and advisory-boundary guardrails | Covered | Output-like payloads are kept product-safe. |
| `decide_raw` not called | Local validation harness, adapter, decision-diff, shadow-path, and advisory-boundary tests | Covered | `decide_raw` remains absent from current track behavior. |
| no artifact persistence or publication | Advisory artifact, shadow-path guardrails, and advisory-boundary guardrails | Covered | Default behavior keeps artifacts sanitized and unpublished. |
| no runtime wiring | Adapter, local validation harness, decision-diff, artifact, shadow-path, and advisory-boundary tests | Covered | Protected runtime files remain free of migration-module wiring. |
| no user-visible output change | Shadow-path and advisory-boundary guardrails plus checkpoint docs | Covered indirectly | Tests verify non-user-visible, no-op boundaries rather than live product rendering. |
| fix conservatism | Local validation harness, decision-diff, advisory artifact, shadow-path, and advisory-boundary tests | Covered | Fix-like cases do not authorize patching or repo actions. |
| manual harness default skip | Local validation harness, shadow-path guardrails, and advisory-boundary guardrails | Covered | Default harness path still exits `0` with the same skip message. |
| JSON serialization safety | Adapter stub compatibility, decision-diff, advisory artifact, shadow-path, and advisory-boundary tests | Covered | Migration artifacts remain serializable and safe to render. |
| sanitized failure categories | Adapter stub compatibility, shadow-path guardrails, and advisory-boundary tests | Covered | Failure taxonomy stays bounded and product-safe. |

## 5. What Tests Prove

Current tests prove that:

- adapter shapes are dependency-free
- manual harness is disabled by default
- shadow skeleton is no-op by default
- advisory boundary is no-op by default
- forbidden fields are blocked
- no `topocore_v6` dependency is required in default CI
- no runtime wiring has been introduced by migration artifacts
- fix-like paths do not authorize patching
- artifacts are sanitized and not persisted or published by default
- Sprint 53 static workflow and runtime tests prove the gate and env propagation seams
- Sprint 53 operational checks proved:
  - gate `1` can resolve issue-comment TopoCore v6
  - gate `0` originally kept the issue-comment path on the v5-side runtime
- Sprint 55 adds no new runtime coverage:
  - it maps existing v6 and v5 fallback evidence
  - it identifies missing deprecation evidence rather than adding new execution coverage
- Sprint 56 adds no new runtime test coverage:
  - it maps existing tests and operational evidence into an observation window and deprecation runway
  - repeated live observation remains pending
- Sprint 57 adds live operational evidence:
  - issue `ask` and explain-style v6 observation succeeded under gate=`1`
  - workflow-dispatch v6 sanity rerun succeeded
  - gate=`0` kill switch succeeded
  - PR and review/fix observation did not yet provide stable, consistent v6 backend evidence
- Sprint 58 adds targeted blocker coverage:
  - workflow-to-action `RB_TOPOCORE_BACKEND` propagation is now tested explicitly
  - PR ask/review markdown evidence surfaces are covered statically
  - PR verify report-only scoped diagnostics are covered explicitly
  - non-PR `review` and `fix` no longer rely on ambiguous PR-only guidance in tests
- Sprint 59 adds output-visibility coverage:
  - PR `ask` / `review` / `verify` now have explicit visible runtime backend evidence coverage
  - missing or partial backend metadata is rendered safely as `n/a` or scoped status rather than being silently omitted
  - gate=`1` v6 and gate=`0` v5 evidence visibility are both locked at the markdown layer
- Sprint 60 adds live operational evidence rather than new default-CI tests:
  - fresh PR fixture `#112` replaced stale PR `#87`
  - PR `ask` and PR `review` showed visible TopoCore backend evidence with `resolved_backend=v6`
  - PR `verify` showed explicit `verify_report_only` scoped backend evidence
  - `workflow_dispatch` sanity resolved to v6
  - gate=`0` kill switch still resolved to v5
- Sprint 61 adds policy and static coverage only:
  - Sprint 60 remains the runtime evidence basis
  - v5 fallback and kill-switch coverage remain critical
  - v5 is documented as fallback-only and deprecation candidate, not removed
- Sprint 62 adds deprecation-prep metadata and classification coverage:
  - static seam and test classification is documented
  - metadata policy is import-safe and side-effect free
  - remaining gaps stay explicit:
    - v5-off simulation is not implemented yet
    - v5 removal is not tested or approved
- Sprint 63 adds opt-in simulation coverage:
  - simulation helper truthiness is covered
  - explicit `v5` and legacy `lite` are blocked safely when simulation is enabled
  - `auto` plus v6 available still resolves to v6
  - `auto` plus v6 unavailable no longer silently falls back to v5 during simulation
- Sprint 64 adds authoritative-default coverage:
  - v6 authoritative metadata is covered
  - v5 disabled-by-default behavior is covered
  - emergency deprecated-v5 allow is covered explicitly
  - simulation still wins over emergency allow
  - GitHub action and workflow defaults move to `auto`
  - remaining gap:
    - v5 physical removal is still not done until Sprint 65
- Sprint 65 adds runtime-removal coverage:
  - deprecated v5 runtime execution is removed
  - legacy `lite` execution is removed
  - old env values are covered as safe unsupported diagnostics
  - workflow and action no longer advertise v5 or `lite` as supported runtime choices
- Sprint 66 adds physical cleanup coverage:
  - orphaned vendor assets are absent
  - legacy canary workflow residue is removed
  - compatibility stubs remain non-executable
- Sprint 67 adds final residue-sweep coverage:
  - standalone v5 guides are absent
  - stale guide references are removed
  - active code, tests, workflows, and action surfaces stay free of lower-case legacy runtime residue
- Sprint 68 adds no new runtime coverage:
  - live issue-comment sanity passed on `main`
  - optional `workflow_dispatch` v6 sanity passed on `main`
  - final static proof passed for removed v5 docs, vendor assets, and workflow residue
- Sprint 69 adds direct external-pilot product-surface coverage:
  - active install docs now point directly to `RepoBrain-Action`
  - community-hosted workflow dependency is statically blocked on active runtime/onboarding surfaces
  - no new runtime behavior is claimed by tests alone
- Sprint 70 adds external command-matrix evidence documentation coverage:
  - issue and PR command outcomes on `Elen-MCP-v.2.2.0` are recorded
  - v6 backend evidence and scoped unsupported behavior are linked in current indexes
  - no new runtime behavior is claimed by local tests alone
- Sprint 71 adds retrieval-quality documentation and regression coverage:
  - workflow files are now part of the default retrieval scan
  - external issue and PR evidence quality is recorded against live Elen-MCP runs
  - no new runtime policy is claimed beyond the live evidence and targeted retrieval fix
- Sprint 72 adds verify-productionization coverage:
  - explicit `PASS/WARN/FAIL/PENDING/NOT_RUN/UNKNOWN` verify semantics are tested locally
  - missing verification signals no longer collapse into an implied pass
  - permission-limited or coarse-source verify output remains informational and safe
- Sprint 73 adds fix-product-path coverage:
  - PR fix now has explicit proposal/governance rendering coverage
  - visible no-mutation markers are tested directly
  - unsafe mutation prompts are tested as blocked product-path requests
- Sprint 74 adds external security hardening coverage:
  - consumer workflow permissions are statically constrained to a read-mostly baseline
  - private action access and missing-token failure modes are documented and guarded
  - fork-safety policy is recorded without widening runtime trust

## 6. What Tests Do Not Prove

Current tests do not prove:

- live TopoCore v6 runtime behavior
- GitHub workflow advisory behavior
- real PR v5/v6 parity
- canary readiness
- route migration readiness
- fix migration readiness
- v5 replacement readiness
- production packaging or private dependency CI strategy
- Sprint 54 adds no new runtime coverage because it is a docs and policy-freeze closeout sprint
- Sprint 55 does not prove v5 deprecation readiness by itself because it is an assessment-only sprint
- Sprint 56 does not prove repeated live stability because it defines observation requirements rather than executing them
- Sprint 57 does not prove full promotion readiness because the observation result was `PARTIAL_PASS`
- Sprint 58 adds no default-CI live GitHub observation by itself:
  - promotion still depends on rerunning the focused observation subset on `main`
- Sprint 59 still does not prove promotion by local tests alone:
  - live PR-path `issue_comment` evidence must still be rerun on `main`
- Sprint 60 does not add new default-CI runtime coverage:
  - it records live GitHub operational evidence and a fresh-PR promotion result rather than widening local test scope
- Sprint 61 does not add new runtime coverage by itself:
  - it locks policy wording and documentation state rather than changing execution paths
- Sprint 62 does not implement v5-off simulation yet:
  - runtime behavior remains unchanged
  - removal behavior is still untested and unapproved
- Sprint 63 does not run a live simulation checkpoint yet:
  - simulation exists locally and is opt-in
  - workflow and action defaults remain unchanged
  - v5 is still not removed
- Sprint 64 still does not remove v5 physically:
  - deprecated v5 remains present only for emergency opt-in
  - post-merge live issue-comment validation is still separate from local test coverage
- Sprint 65 does not yet prove post-removal live GitHub sanity:
  - local validation covers the removal policy and safe unsupported diagnostics
  - post-removal hardening and optional live sanity remain Sprint 66 work
- Sprint 66 does not run live post-removal sanity by itself:
  - vendor-absence and residue cleanup are covered statically
  - bounded live v6 sanity remains a follow-up hardening step
- Sprint 67 still does not prove live issue-comment sanity by itself:
  - static cleanup and policy proof are covered
  - bounded live v6 sanity remains optional follow-up work unless explicitly run on `main`
- Sprint 68 adds no new local runtime test surface:
  - it records successful live sanity and final static proof
  - no additional runtime behavior was introduced
- Sprint 69 does not prove external pilot runtime execution yet:
  - `Elen-MCP-v.2.2.0` live issue/PR smoke remained blocked on missing private TopoCore access
  - local pilot-repo Node validation was blocked because `npm` / `npx` were unavailable in the operator environment
- Sprint 70 documentation tests do not replace live GitHub evidence:
  - they guard the recorded matrix and indexes
  - the live command matrix evidence still comes from GitHub runs on `Elen-MCP-v.2.2.0`
- Sprint 71 documentation and retrieval tests do not replace live GitHub evidence:
  - they guard the documented quality results and the workflow-indexing fix
  - the retrieval/evidence quality result still comes from GitHub runs on `Elen-MCP-v.2.2.0`
- Sprint 74 documentation and static-guard tests do not replace full live fork/security chaos testing:
  - they guard the published permissions, token, and fork-safety policy
  - live missing-secret and untrusted-fork secret-withholding scenarios remain intentionally conservative unless run in isolated fixtures

## 7. Recommended Future Test Maintenance

Recommended maintenance:

- keep guardrail tests deterministic and offline
- keep `topocore_v6` absent from default CI requirements
- add future tests only behind disabled or manual boundaries
- preserve no-runtime-wiring assertions
- preserve forbidden-output assertions
- preserve manual harness default skip behavior

See also:

- `docs/architecture/TOPOCORE_V6_MANUAL_EVIDENCE_COLLECTION_AND_PHASE_7_CHECKPOINT.md`
- `docs/architecture/TOPOCORE_V6_REAL_INTEGRATION_CONTRACT_LOCK.md`
- `docs/architecture/TOPOCORE_V6_REAL_ADAPTER_IMPLEMENTATION.md`
- `docs/architecture/TOPOCORE_V6_RUNTIME_BACKEND_SELECTION.md`
- `docs/architecture/TOPOCORE_V6_REVIEW_VERIFY_BACKEND_EXPANSION.md`
- `docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_DEFAULT_LAB_RUNTIME_POLICY.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_RUNTIME_LAB_SWITCH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_DEPENDENCY_GATE.md`
- `docs/architecture/TOPOCORE_V6_WORKFLOW_DISPATCH_MEANINGFUL_DECISION_PATH.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_IMPORT_BLOCKER_FIX.md`
- `docs/architecture/TOPOCORE_V6_GITHUB_LAB_TKYA_ARTIFACT_OPTIONALITY.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_RUNTIME.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_GATE_PROPAGATION_FIX.md`
- `docs/architecture/TOPOCORE_V6_ISSUE_COMMENT_LAB_TRANSITION_CLOSEOUT.md`
- `docs/architecture/TOPOCORE_V6_V5_DEPRECATION_READINESS_ASSESSMENT.md`
- `docs/architecture/TOPOCORE_V6_OBSERVATION_AND_V5_DEPRECATION_RUNWAY.md`
- `docs/architecture/TOPOCORE_V6_SPRINT_57_OBSERVATION_RESULTS.md`
- `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`
