# Sprint 86 - Enterprise P0 Hardening

## 1. Purpose

Sprint 86 hardens enterprise P0 gaps before any public visibility switch.
It does not make the repository public.

## 2. Baseline

- latest main before Sprint 86: `63c8f82 Record pre-public smoke evidence`
- Sprint 85 status: `PUBLIC_VISIBILITY_APPROVAL_PACK_READY`
- meta-audit readiness: `79 / 100`

## 3. Supply-Chain Hardening

- files added:
  - `SECURITY.md`
  - `CONTRIBUTING.md`
  - `.github/CODEOWNERS`
  - `.github/dependabot.yml`
  - `.github/workflows/dependency-review.yml`
  - `.github/workflows/codeql.yml`
  - `.github/workflows/sbom.yml`
  - `.github/workflows/provenance.yml`
  - `docs/security/SUPPLY_CHAIN_SECURITY_BASELINE.md`
- status:
  - baseline added and validated locally
- limitations:
  - provenance is prepared, but no public release artifact or RC tag was created in Sprint 86

## 4. Release Integrity

- SBOM/provenance/tag plan:
  - documented in `docs/release/RELEASE_INTEGRITY_AND_PROVENANCE.md`
- RC tag created:
  - `no`
- approval state:
  - owner approval still required
- status:
  - release integrity is operationally prepared, but not exercised through a public RC tag

## 5. Governance Evidence

- CODEOWNERS:
  - added
- branch protection/ruleset verification:
  - checked with `scripts/check_repo_governance.py`
- API limitations:
  - GitHub API returned `403` for branch protection/rulesets on the current token scopes
  - `403` is treated as `UNKNOWN`, not `PASS`
- status:
  - `GOVERNANCE_PARTIAL_API_LIMITED`

## 6. Installed Package Live Proof

- attempted:
  - `yes`
- repo used:
  - `alexworkingai/Elen-MCP-v.2.2.0`
- mode:
  - `installed_package`
- source checkout avoided:
  - `yes`
- result:
  - blocked
- blocker:
  - external workflow did not yet have an operational private package/artifact delivery path
  - doctor/status correctly degraded to `installed_package_unavailable`
  - audit/score correctly stayed static instead of falsely claiming `v6`

## 7. Dormant Mutation Surface

- removed/isolated:
  - dormant `_maybe_apply_patch(...)`
  - dormant `_maybe_create_patch_pr(...)`
- tests:
  - `tests/test_no_dormant_mutation_surface.py`
- no-mutation policy:
  - unchanged

## 8. Workflow Least Privilege

- changes:
  - main RepoBrain execution workflow no longer requests `checks: write` or `pull-requests: write`
  - auxiliary internal workflows were also narrowed where safe
- remaining write permissions:
  - the dedicated checks publisher workflow still keeps `checks: write` and `statuses: write`
- justification:
  - that workflow exists only to publish check-run/status evidence and is documented separately in `docs/security/GITHUB_ACTIONS_PERMISSION_MODEL.md`

## 9. Structural Maintainability

- hotspots:
  - documented in `docs/architecture/STRUCTURAL_MAINTAINABILITY_PLAN.md`
- containment plan:
  - added
- safe extraction:
  - dormant mutation cleanup removed dead code from `repobrain/github_flow.py`

## 10. Live Smoke

- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/34`
- run URLs:
  - doctor: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455194721`
  - status: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455243664`
  - audit: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455244765`
  - score: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455247646`
  - ask: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455249062`
  - installed-package doctor proof: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455084053`
  - installed-package status proof: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455128599`
  - installed-package audit proof: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455131085`
  - installed-package score proof: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26455134051`
- command results:
  - doctor: `PASS`
  - status: `success`
  - audit: `v6-enriched scoring`, `77 / 100 GOOD`
  - score: `v6-enriched scoring`, `77 / 100 GOOD`
  - ask: completed without leakage, but response quality was weaker than the command-specific smoke outputs
- backend evidence:
  - issue-comment main path resolved `v6` for audit/score
  - installed-package proof path correctly resolved `not_applicable` and stayed static
- safety:
  - no secret exposure
  - no TopoCore source exposure
  - no mutation

## 11. Product Status

- `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`

## 12. Next Step

- Sprint 87 should target:
  - external installed-package delivery path operationalization
  - partner-like proof of real `v6` enrichment without `private_checkout`
- only after that should owner approval for a public switch be reconsidered

## 13. Non-Goals

- no public switch
- no Marketplace
- no v5
- no repobrain-community
- no patch/autofix
- no TopoCore source exposure
- no Microsoft partnership claim
