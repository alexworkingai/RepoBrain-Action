# Public Readiness Assessment

## Current Repository Visibility

- `RepoBrain-Action`: `PUBLIC`
- TopoCore v6: `PRIVATE`
- `Elen-MCP-v.2.2.0`: `PRIVATE`

## Current Product Truth

- audit and score run live in real `v6`-enriched mode when the authorized private runtime is available
- doctor and status are report-only and truthful about runtime state
- operational `/repobrain ask` answers runtime/workflow/public-readiness questions as a status/ops response rather than a generic review-style synthesis
- Sprint 92A manual issue smoke hotfix removed private checkout evidence leakage, aligned issue-mode LLM diagnostics with actual execution, and corrected locate/explain issue UX
- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior
- no `v5`
- no `repobrain-community`
- enterprise P0 hardening from Sprint 86 remains in place after the public switch

## What Must Stay Private

- TopoCore v6 repository
- TopoCore v6 source and internal implementation details
- any real token or private key material
- consumer repository secrets such as `TOPOCORE_V6_REPO_TOKEN` and `TOPOCORE_V6_ARTIFACT_TOKEN`

## Public Scrub Status

Public scrub improvements remain intact after Sprint 91:

- top-level `LICENSE` exists
- local machine paths have been sanitized from tracked docs
- no private TopoCore source is present in RepoBrain-Action
- no real secret or private key values are present in tracked docs
- command/docs/support surface is aligned with current product behavior
- post-switch public file checks completed without exposure findings

## Runtime Distribution Status

Sprint 84 selected the near-term partner-testing runtime model:

- decision: `INSTALLED_PRIVATE_PACKAGE_SELECTED`
- `private_checkout` remains controlled beta only
- selected partner testing should prefer installed private package mode

Important caveat:
- a standard private Python wheel can still contain readable implementation files
- this is acceptable for selected partner testing only under scoped access and explicit approval
- it is not the same as strong source secrecy or broad public distribution hardening

Historical runtime-proof trace:
- Sprint 87 established the external installed-package proof path
- Sprint 88 selected the GitHub-supported minimum-scope artifact authorization model
- Sprint 89 correctly stopped because the required secret was absent
- Sprint 90 completed decisive external installed-package proof with real `v6` enrichment and no private source checkout

Sprint 91 public-action smoke update:
- RepoBrain-Action is now public while TopoCore and Elen-MCP remain private
- post-switch Elen-MCP smoke passed for doctor, status, audit, score, and ask
- audit and score remained `v6-enriched scoring`
- backend evidence remained `auto -> v6`
- no secret or TopoCore source exposure occurred in user-facing output

Sprint 92C diagnostics and permission update:
- live Elen-MCP issue and PR retest passed for ask, locate, explain, review, verify, fix, audit, and score
- default GitHub comments are now compact by default while verbose and artifact traces remain available behind sanitized gates
- justified `pull-requests: write` is now classified as a constrained PR comment response permission rather than a broad write-heavy workflow risk when all no-mutation constraints hold
- latest PR audit and score comments improved to `85 / 100 STRONG`
- no `.topocore-v6` leakage was observed in the latest checked issue and PR comment slices

Sprint 92D branch update:
- issue ask now has a deterministic product-analysis fallback when safe issue-mode LLM policy does not allow an LLM call
- visible route labels reflect the typed command rather than internal analysis mode
- PR ask scope is rendered as `PR ask`
- verify default output stays compact and no longer uses the legacy TopoCore diagnostics header
- review and fix default comments are compact by default, with deeper internals reserved for verbose/artifact diagnostics
- protected main baseline is now enabled on the public RepoBrain repository
- required checks and CODEOWNERS enforcement remain intentionally deferred for now

Sprint 92E implementation target:
- issue `/repobrain ask` must analyze the current consumer repository rather than defaulting to RepoBrain-Action self-description
- PR `/repobrain ask` must stay PR-scoped and produce an impact assessment instead of a product overview
- locate and explain must stay relevant to the target repository and avoid unrelated workflow padding
- doctor and status default wording must stay partner-facing and compact
- PR `#119` merged the protected-main UX polish without admin bypass
- dependency graph enabled on the public RepoBrain repository
- dependency review passed on PR `#119`
- governance currently follows a solo-owner protected-main model rather than review-enforced branch protection

Sprint 92F implementation target:
- controlled trusted issue ask/explain LLM is enabled by default through `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1`
- issue ask/explain must fall back deterministically when policy, provider availability, or quota blocks LLM use
- `/repobrain audit --narrative` and `/repobrain audit --executive` add optional LLM explanation layers while keeping TopoCore as score authority
- `/repobrain audit --profile premium` implies a premium narrative layer after TopoCore scoring
- `/repobrain score` stays TopoCore-first and does not require an LLM
- remaining review/fix default-output noise is removed from compact comments

Sprint 92G implementation target:
- `/repobrain help` is restructured into a four-block command-reference manual
- every supported command and supported extension is documented in Help block 2
- `/repobrain audit --profile premium` implies premium narrative semantics in both issue and PR audit contexts
- PR audit narrative and PR impact sections stay distinct and non-duplicative
- explain applies RepoBrain connection reranking consistently and suppresses unrelated workflow padding
- review/fix/PR-ask compact outputs remove the last default evidence/verification noise without weakening verbose diagnostics

## Current Operating Conditions

Public visibility is now switched, but the operating model remains constrained:

1. TopoCore must remain private
2. selected-partner runtime/token process remains scoped and revocable
3. no accidental source-repo access grants beyond the chosen distribution model
4. no Marketplace publication in this phase
5. selected partner pilot only
6. enterprise P0 hardening remains green, including supply-chain baseline, governance evidence, least-privilege workflow posture, and mutation-surface cleanup
7. public switch remains a manual owner-approved event and is not automated by RepoBrain

## User Support Implication

Now that RepoBrain-Action is public:

- the public repo still fronts a private TopoCore boundary
- selected partners can reference the public action surface while receiving private runtime access separately
- broader turnkey public install and Marketplace support are still future work

## Decision

- current public readiness decision on the Sprint 92G branch: `SPRINT_92G_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`
- historical Sprint 91 post-switch decision: `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`
- private beta decision: `PRIVATE_BETA_RC_CONFIRMED`
- TopoCore security decision: `TOPOCORE_SECURITY_POLICY_ADOPTED`
- Marketplace decision: `MARKETPLACE_NOT_READY`

Historical state retained for traceability:

- Sprint 84 / Sprint 85 decision: `PUBLIC_READY_PENDING_OWNER_APPROVAL`
- Sprint 86 decision: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`
- Sprint 87 decision: `PUBLIC_BLOCKED_BY_TOKEN_SCOPE`
- Sprint 88 / Sprint 89 blocked state: `OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE`
- Sprint 90 decision: `PUBLIC_SWITCH_READY_AFTER_RUNTIME_PROOF`

## Governance Snapshot After PR #119

- protected-main baseline remains enabled on `main`
- current active ruleset follows a solo-owner model:
  - prevent force pushes
  - prevent deletions
  - require linear history
- PR `#119` is the merge evidence for the protected-main UX polish path
- dependency graph enabled
- dependency review passed
- required status checks: deferred
- CODEOWNERS review enforcement: deferred
- governance remains partial rather than enterprise-complete

## Sprint 91 Result

- owner approval was recorded and executed as a controlled visibility switch
- `RepoBrain-Action` is now public
- TopoCore remains private
- Elen-MCP remains private
- post-switch external smoke passed
- selected partner pilot readiness package is now aligned with the public action surface
- RC tag creation remains deferred pending separate approval
- public visibility must not be confused with Marketplace start or TopoCore source distribution
