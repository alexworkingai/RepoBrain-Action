# TopoCore v6 Private Dependency Strategy Proposal

## 1. Purpose

Sprint 39 defines a private or local TopoCore v6 dependency strategy proposal.

Current truth:

- Sprint 39 is docs-only
- Sprint 39 does not add a dependency
- Sprint 39 does not change CI
- Sprint 39 does not import or call TopoCore v6
- Sprint 39 does not activate advisory behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- Phase 6 NO-GO remains in effect

This sprint exists to define how RepoBrain-Action may later access private or local TopoCore v6 safely without changing current runtime behavior or making default CI depend on private access.

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 39:
  - `ec4d4ab Docs: add TopoCore v6 migration indexes`
- Phase 7 started with documentation and test index consolidation
- Sprint 38 validation:
  - `pytest` passed with `725` tests
- current state:
  - still-disabled advisory boundary exists
  - manual/local validation harness exists
  - advisory experiment implementation remains blocked
  - default CI does not require `topocore_v6`
  - runtime behavior remains unchanged

See:

- `docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_EVIDENCE_COLLECTION_AND_PHASE_7_CHECKPOINT.md`

## 3. Problem Statement

Current problem:

- RepoBrain-Action has safe adapter, decision-diff, advisory artifact, shadow skeleton, and boundary code
- real TopoCore v6 compatibility still depends on private or local access
- current CI must remain green without private TopoCore v6
- any dependency strategy must avoid leaking secrets, tokens, package URLs, private repo data, or internal implementation details
- the project needs a dependency strategy before any controlled advisory experiment discussion can be reopened

## 4. Dependency Strategy Goals

Goals:

- keep default CI independent from private TopoCore v6
- support local and manual developer validation
- support future private validation only after explicit approval
- avoid runtime import at module import time
- avoid accidental public dependency exposure
- avoid secrets in repository files
- avoid workflow changes in this sprint
- keep missing dependency as skip or no-op, not failure, unless strict manual mode is explicitly requested
- keep v5/TKYA primary

## 5. Non-Goals

Current non-goals:

- no dependency addition in Sprint 39
- no `pyproject` or `requirements` change
- no workflow or `action.yml` change
- no package registry setup
- no secret configuration
- no private repo URL committed
- no runtime import
- no runtime wiring
- no advisory activation
- no canary
- no route migration
- no v5 replacement
- no fix migration

## 6. Candidate Dependency Options

| Option | Description | Pros | Risks | Default CI impact | Recommended status |
|---|---|---|---|---|---|
| A. Local editable install | Developer installs private TopoCore v6 locally outside RepoBrain-Action | Fast iteration, clean separation, no repo config change | Local environment drift, workstation-specific setup | None | Recommended now for manual validation |
| B. Local wheel or package file outside repo | Developer installs a locally built private wheel | More reproducible than editable install, easier version pinning in manual contexts | Distribution discipline required, stale wheel risk | None | Acceptable future manual option |
| C. Private package registry | Private PyPI or GitHub Packages style distribution | Centralized versioning, better repeatability for approved private contexts | Secrets handling, access policy, CI complexity, registry leakage risk | None unless explicitly configured | Future option only |
| D. Private Git dependency | Install from private git URL | Familiar workflow for some teams | URL leakage, token leakage, poor safety if committed | None unless configured, but risky | Not recommended |
| E. Git submodule or subtree | Private source linked into repo structure | Direct source access, no package build step | Boundary confusion, access friction, repo complexity | Potentially high | Not recommended now |
| F. Vendoring TopoCore v6 into RepoBrain-Action | Embed private v6 code in this repo | Immediate local availability | Recreates monolith or vendor problem, harder boundary control | High long-term risk | Not recommended |
| G. Optional extras dependency | Future optional extra such as `[topocore_v6_local]` | Could make local setup clearer later | Still needs packaging policy and approval, easy to over-expand | None if truly optional | Possible later, not approved now |

## 7. Recommended Strategy

Recommended strategy:

Primary path now:

- use local or manual editable install, or a local wheel, outside RepoBrain-Action
- allow dynamic import only inside the manual or local validation path
- keep default CI dependency-free
- keep missing dependency behavior as skip or no-op
- allow strict failure only under an explicit manual env flag

Future path:

- private package registry or optional extra only after separate approval
- never make private v6 required in default CI
- never commit secrets or private URLs

Current truth:

- no dependency is added in Sprint 39
- this is a proposal only

## 8. Install and Access Model

Proposed future local or manual model:

Developer machine:

- install private TopoCore v6 outside RepoBrain-Action
- run manual or local validation only when explicitly opted in
- keep private credentials outside the repository
- use sanitized output only

Default CI:

- no `topocore_v6` install
- no private credentials
- no failure when `topocore_v6` is absent
- existing tests remain offline and deterministic

Private or approved validation context:

- possible later
- must require explicit approval
- must use secrets only through approved secure CI mechanism
- must not publish raw artifacts

## 9. Import Boundary Rules

Allowed:

- dynamic import only inside manual or local validation, or a future explicitly approved optional boundary
- import only after env opt-in
- missing import becomes skip or no-op unless strict manual flag is set

Forbidden:

- `topocore_v6` import at module import time
- import from `github_flow.py`
- import from `tky_local.py`
- import from `tky_engine.py`
- import from `tkya` engine modules
- import from `action.yml` or workflow-driven default runtime
- import in tests that run by default unless fake or monkeypatched

## 10. Environment Controls

Current and existing controls:

- `RB_TOPOCORE_V6_LOCAL_VALIDATE=1`
- `RB_TOPOCORE_V6_REQUIRE_LOCAL=0|1`
- `RB_TOPOCORE_V6_LOCAL_ARTIFACT_JSON=1`
- `RB_TOPOCORE_V6_SHADOW_ENABLED=0|1`
- `RB_TOPOCORE_V6_SHADOW_ARTIFACTS=0|1`
- `RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED=0|1`

Future dependency-related proposal:

- `RB_TOPOCORE_V6_DEPENDENCY_MODE=none|local|private`
- `RB_TOPOCORE_V6_REQUIRE_PRIVATE=0|1`

Current truth:

- these future env names are proposal-only
- do not implement them in Sprint 39
- defaults must be safe
- missing dependency must not fail default CI

## 11. Security and Secrets Policy

Security and secrets policy:

- do not commit private repo URLs
- do not commit package tokens
- do not commit registry credentials
- do not print secrets in logs
- do not include secrets in advisory artifacts
- do not include raw exception dumps with credential-bearing paths
- do not expose private dependency metadata to users
- GitHub Actions secrets, if used later, require a separate approved sprint and threat review

## 12. CI Policy

Default CI policy:

- default CI must not install `topocore_v6`
- default CI must not require private credentials
- default CI must run all existing tests with fake, stub, or manual-disabled paths
- absence of `topocore_v6` must be expected
- private validation CI, if later approved, must be separate from default CI
- private validation failure must not block unrelated default CI unless explicitly scoped

## 13. Packaging / Distribution Risk Matrix

| Risk | Example | Impact | Mitigation | Current status |
|---|---|---|---|---|
| private credential leak | Token appears in shell history, config, or logs | High | Keep credentials outside repo, use approved secret stores only, redact logs | Open risk, no approved implementation |
| private URL leak | Private git or registry URL committed to docs or config | High | Never commit private URLs, keep strategy abstract in repo docs | Open risk, controlled by policy only |
| default CI dependency drift | Default pipeline starts requiring `topocore_v6` | High | Keep all private dependency paths separate from default CI | Must remain blocked |
| accidental runtime import | `topocore_v6` imported at module import time | High | Enforce dynamic import only behind explicit manual or approved boundaries | Must remain blocked |
| vendoring or monolith regression | Private v6 code copied into RepoBrain-Action | High | Do not vendor, preserve repo boundaries | Not recommended |
| artifact or log leakage | Private path info or raw output appears in artifacts | High | Sanitize outputs, forbid raw traces and secrets, avoid raw exception dumps | Must remain blocked |
| version mismatch | Local v6 install incompatible with adapter expectations | Medium | Record safe version evidence in manual reports only, review compatibility explicitly | Unresolved |
| install reproducibility issue | One developer setup works, another does not | Medium | Prefer documented editable install or local wheel workflow | Unresolved |
| platform compatibility issue | Local install works on one OS but not another | Medium | Keep validation local and opt-in until compatibility evidence exists | Unresolved |

## 14. Versioning and Compatibility Proposal

Future versioning rules:

- pin TopoCore v6 version only in private or manual context
- record version in manual evidence reports only if safe
- do not expose private version metadata in public user output
- compatibility evidence must include adapter preview shape, v6 external decision shape, decision-diff result, and advisory artifact safety
- semantic mismatch remains a blocker until reviewed

## 15. Relationship to Existing Manual Harness

See:

- `scripts/validate_topocore_v6_local.py`
- `docs/architecture/TOPOCORE_V6_MANUAL_LOCAL_VALIDATION_HARNESS.md`
- `docs/architecture/TOPOCORE_V6_MANUAL_DECISION_DIFF_ARTIFACT_HARNESS.md`

Current truth:

- current harness already supports local or manual dependency absence safely
- dependency strategy should preserve this behavior
- strict local failure should remain opt-in only
- no default CI private dependency should be introduced

## 16. Relationship to NO-GO State

See:

- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

Current truth:

- dependency strategy does not reopen implementation approval by itself
- advisory experiment implementation remains NO-GO
- runtime activation remains blocked
- strategy is prerequisite evidence only

## 17. Acceptance Gates for Future Dependency Work

Before any dependency implementation sprint, require:

- this strategy accepted
- explicit human approval
- exact dependency path selected
- default CI impact stated
- secrets handling stated
- rollback plan stated
- no runtime behavior changes
- no user-visible output changes
- no artifact publication
- no private URL or token committed
- validation plan defined

## 18. Recommended Next Step

Recommended next step:

- after Sprint 39, the next safe step may be a manual evidence collection checklist or a dependency decision checkpoint
- do not implement dependency handling without explicit approval

## 19. Acceptance Criteria

Sprint 39 is complete only if:

- the new dependency strategy proposal document exists
- it clearly states docs-only
- it compares dependency options
- it recommends local or manual strategy first
- it keeps default CI independent from private TopoCore v6
- it defines import boundary rules
- it defines security and secrets rules
- it defines CI policy
- it defines a risk matrix
- it references the current NO-GO state
- it does not add dependencies
- it does not change runtime behavior
