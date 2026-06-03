# Sprint 92E Consumer Repo Ask And UX Final Fix

## 1. Purpose

Sprint 92E closes the remaining partner-facing issue and PR UX gaps after PR `#119` merged the Sprint 92D protected-main polish.

The core goal is repository-role isolation:

- issue `/repobrain ask` must analyze the consumer repository under test
- PR `/repobrain ask` must stay scoped to the PR and assess change impact
- partner-facing defaults must stay compact, relevant, and non-leaky

## 2. Baseline

- RepoBrain-Action is public
- TopoCore remains private
- Elen-MCP remains private
- latest merged main before Sprint 92E work: `bffe131 Polish issue and PR UX under protected main (#119)`
- current readiness state entering Sprint 92E: `SPRINT_92D_IMPLEMENTATION_MERGED_LIVE_RETEST_FINDINGS_PENDING_FIX`

## 3. Why Sprint 92E Exists

Post-merge manual findings showed that the public control plane still had partner-facing UX drift:

- complex issue ask could describe RepoBrain-Action internals instead of the consumer repository
- PR ask could collapse into a product overview instead of a PR impact assessment
- review/fix default comments still exposed too much internal detail
- doctor/status wording was still too raw for partner-facing comments
- locate could pad results with unrelated workflow files
- active docs still reflected pre-merge governance/readiness state

## 4. Governance Truth After PR #119

- PR `#119` merged without admin bypass
- dependency graph enabled
- dependency review passed on PR `#119`
- protected-main baseline remains enabled on the public RepoBrain repository
- current active ruleset is a solo-owner model
- force pushes blocked
- deletions blocked
- linear history required
- required checks deferred
- CODEOWNERS review enforcement deferred
- governance remains partial rather than enterprise-complete

## 5. Code-Level Fix Targets

- issue ask deterministic product-analysis fallback now reads the current consumer repository surface
- PR ask intent detection now prefers a PR impact assessment
- doctor/status default runtime wording is partner-facing and compact
- review/fix default comments keep deeper internals in verbose or artifact paths only
- locate workflow queries avoid unrelated deploy-workflow padding
- help notes cover the full supported command surface

## 6. Test Coverage Added

Sprint 92E coverage focuses on:

- consumer repository ask isolation
- PR ask impact assessment
- default output noise cleanup
- status/doctor partner wording compaction
- RepoBrain workflow relevance filtering
- merged-state public-readiness status after PR `#119`
- dependency graph and dependency review governance evidence

## 7. Current Product Status

- current branch status: `SPRINT_92D_IMPLEMENTATION_MERGED_LIVE_RETEST_FINDINGS_PENDING_FIX`
- target post-retest status: `SELECTED_PARTNER_PILOT_READY_AFTER_FINAL_CONSUMER_REPO_ASK_AND_UX_FIX`

## 8. Non-Goals

- no Marketplace work
- no TopoCore source exposure
- no runtime-policy relaxation
- no patch/autofix
- no mutation behavior
- no weakening of the protected-main baseline
