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
| `tests/test_topocore_backend_selection.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Backend precedence, v5 default, v6 opt-in, missing-dependency fallback, strict local failure, safe v6 normalization, no runtime wiring | No |
| `tests/test_topocore_backend_review_verify.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Review and verify task-family mapping, safe v6 summary-family payloads, v5 fallback, strict local failure, fix exclusion, no runtime wiring | No |
| `tests/test_topocore_backend_fix_lite.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Fix-lite command-family preservation, conservative v6 fix decision shaping, patch-safety markers, v5 fallback, strict local failure, no runtime wiring | No |
| `tests/test_topocore_backend_lab_default_policy.py` | `repobrain/topocore_backend.py` plus `repobrain/tky_local.py` | Phase 7 | Auto lab-default backend policy, v6-preferred runtime selection, v5 fallback markers, strict local failure, command-family coverage, GitHub pin preservation | No |
| `tests/test_github_runtime_v6_lab_switch.py` | `action.yml` plus `.github/workflows/repobrain.yml` | Phase 7 | Manual workflow-dispatch backend selection, v5-pinned issue-comment safety, no default strict mode, no private install, selector compatibility | No |
| `tests/test_github_runtime_v6_dependency_gate.py` | `.github/workflows/repobrain.yml` | Phase 7 | Manual-only private checkout gate, secret-only token handling, strict-mode gating, no default private dependency install | No |
| `tests/test_github_workflow_dispatch_meaningful_v6_path.py` | `.github/workflows/repobrain.yml` plus `scripts/run_github.py` | Phase 7 | Meaningful workflow-dispatch lab command inputs, bounded v6 decision execution evidence, fallback markers, conservative fix-lite evidence, no patch or repo mutation steps | No |
| `tests/test_github_topocore_v6_import_blocker_fix.py` | `.github/workflows/repobrain.yml`, `scripts/check_topocore_v6_runtime_import.py`, `scripts/run_github.py` | Phase 7 | Private-checkout path propagation, runtime import diagnostics, sanitized import/API failure categories, failure evidence artifact coverage, issue-comment safety preservation | No |
| `tests/test_github_optional_tkya_evidence_artifact.py` | `.github/workflows/repobrain.yml` | Phase 7 | Optional TKYA evidence-pack upload handling, preserved lab backend evidence visibility, narrow workflow artifact strictness fix, issue-comment and private-checkout safety preservation | No |
| `tests/test_github_issue_comment_v6_lab_runtime.py` | `.github/workflows/repobrain.yml` | Phase 7 | Controlled issue-comment v6 lab gate, v5 fallback policy, gated private checkout and install, non-fatal issue-comment diagnostics, workflow-dispatch preservation, no patch or repo mutation steps | No |
| `tests/test_github_issue_comment_v6_gate_env_propagation.py` | `.github/workflows/repobrain.yml`, `repobrain/github_flow.py`, `repobrain/output_md.py` | Phase 7 | Gated issue-comment local provider propagation, explicit action backend override, safe TopoCore backend diagnostics, preserved kill switch and workflow-dispatch path | No |
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
  - gate `0` keeps the issue-comment path on the v5-side runtime
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
