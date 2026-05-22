# RepoBrain External Repo Product Architecture

## Purpose

This document records the working product architecture after Sprint 69.
It replaces the old community-hosted bridge model with a direct pilot-consumer model.

## Final Repository Structure

- `topocore`
  - private permanently
  - TopoCore v6 engine and private decision logic
- `RepoBrain-Action`
  - main product repository
  - GitHub Action, docs, tests, and onboarding
- `Elen-MCP-v.2.2.0`
  - first external pilot consumer repository
- `repobrain-community`
  - retired from the working product architecture
  - optional archival later

## Private/Public Recommendation

- `topocore`: private permanently
- `RepoBrain-Action`: private during pilot, prepare for public only after explicit scrub/release readiness work
- `Elen-MCP-v.2.2.0`: private pilot consumer repository
- `repobrain-community`: not part of the product; archive later if desired

## Why `repobrain-community` Is Removed From Architecture

`repobrain-community` added an extra bridge layer without adding current product value.
After Sprint 68, the v6-only transition was already complete, so keeping a separate install bridge would only add:

- duplicate onboarding truth
- duplicate workflow ownership
- more places for stale runtime claims to survive
- more difficulty proving which repository is the actual product host

Current policy is direct:

- product action lives in `RepoBrain-Action`
- private engine lives in `topocore`
- pilot consumer repositories install directly from `RepoBrain-Action`

## TopoCore v6 Private Dependency Model

TopoCore v6 remains private and is never copied into consumer repositories.
The consumer workflow checks out the private repository at runtime using a repository secret.

## External Repo Pilot Model

The external consumer repository owns:

- caller workflow file
- repository secrets/variables
- issue and PR smoke evidence
- its own app code and validation lifecycle

`RepoBrain-Action` owns:

- action implementation
- onboarding docs/examples
- product regression tests
- current runtime and safety truth

## Security Boundaries

- TopoCore v6 source stays private
- `TOPOCORE_V6_REPO_TOKEN` is required for private TopoCore checkout and must never be printed
- private `RepoBrain-Action` access must be enabled from consumer repositories during the pilot
- consumer repositories should use read-mostly workflow permissions:
  - `contents: read`
  - `models: read`
  - `issues: write`
  - `pull-requests: read`
  - `checks: read`
  - `statuses: read`
  - `actions: read`
- `contents: write` is not required for the current external product path
- `pull_request_target` is not part of the current external pilot
- untrusted fork PRs must not receive the private TopoCore token by default
- no patch/autofix by default
- no file modification by RepoBrain behavior
- no RepoBrain-created commit/branch/PR behavior
- no `repobrain-community` dependency in active product runtime/onboarding

## Sprint 74 Security Hardening Follow-up

Sprint 74 hardens the same external product path around:

- minimal caller-workflow permissions
- private action access troubleshooting
- missing/invalid private TopoCore token degradation
- no-`pull_request_target` fork safety guidance
- explicit no-mutation security boundaries

## Next Product Roadmap

Next external-product work should focus on:

- command-matrix validation on the pilot consumer repo
- visible backend evidence across issue and PR scopes
- hardening caller-repo install/readiness guidance
- release-readiness review for wider distribution

## Sprint 70 Validated External Surface

Sprint 70 validated the direct external consumer path on `alexworkingai/Elen-MCP-v.2.2.0`.

Validated command surface:

- issue scope:
  - `help`
  - `ask`
  - `locate`
  - `explain`
  - honest scoped unsupported for `review`, `verify`, and `fix`
- PR scope:
  - `ask`
  - `review`
  - report-only `verify` with explicit verification status semantics and source limitations
  - conservative `fix` with `no_patch`

Validated runtime truth:

- requested backend: `auto`
- resolved backend: `v6` for backend-invoking ask/review/fix and retrieval commands
- no `v5`
- no `repobrain-community`

## Sprint 71 Retrieval Quality Follow-up

Sprint 71 validated evidence quality on the same external pilot path and fixed an issue-side retrieval defect:

- `.github/workflows/repobrain.yml` is now indexed in the default retrieval scan
- workflow-focused issue queries now surface the caller workflow as primary evidence
- changed-file prioritization on PR commands remained intact

## Sprint 72 Verify Productionization Follow-up

Sprint 72 made the external PR `verify` path production-useful without changing runtime policy:

- issue-scope `verify` remains scoped unsupported and safe
- PR-scope `verify` now reports explicit `PASS/WARN/FAIL/PENDING/NOT_RUN/UNKNOWN` status labels
- source availability is explicit:
  - `checks`
  - `statuses`
  - `workflow_runs`
- limitations are explicit when evidence is missing, permission-limited, or coarse
- verify remains informational only:
  - no safe-to-merge claim
  - no security approval claim

## Sprint 73 Fix Productization Follow-up

Sprint 73 made the external PR `fix` path product-useful without enabling mutation:

- issue-scope `fix` remains scoped unsupported and safe
- PR-scope `fix` now renders a visible proposal/governance header before lower-level patch diagnostics
- explicit safety gates are user-visible:
  - `patch_authorized=false`
  - `patch_applied=false`
  - `files_modified=false`
  - `branch_created=false`
  - `commit_created=false`
  - `pr_created=false`
- unsafe mutation prompts are blocked explicitly with `BLOCKED_BY_SAFETY`
- `fix` remains informational only:
  - no patch application
  - no branch/commit/PR creation
  - no merge/security approval claim
