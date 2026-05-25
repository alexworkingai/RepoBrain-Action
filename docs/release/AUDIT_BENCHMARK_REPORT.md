# Audit Benchmark Report

## 1. Purpose

This benchmark validates the current MVP 100-point audit scorer across a small deterministic set of repository shapes.
It is not formal certification.
It is intended to support Microsoft/GitHub-facing demo evidence with bounded, reproducible observations.

## 2. Scoring Model Summary

RepoBrain audit currently scores 10 categories with bounded weights totaling 100:

- Architecture and modularity: 15
- Code quality and maintainability: 12
- Testing and validation: 12
- Security posture: 12
- CI/CD and automation: 10
- Dependency hygiene: 8
- Documentation and onboarding: 8
- Release and operations readiness: 8
- GitHub governance: 8
- AI-readiness / repository intelligence: 7

Readiness bands:

- `85-100`: `STRONG`
- `70-84`: `GOOD`
- `50-69`: `NEEDS_ATTENTION`
- `0-49`: `WEAK`

## 3. Benchmark Set

| Fixture | Purpose | Expected behavior | Observed score | Observed band | Notes |
|---|---|---|---:|---|---|
| `mature_repo_fixture` | strong repo surface with docs, tests, release files, governance, and read-mostly workflow | should rank highest | 88 | `STRONG` | high governance and release signals |
| `read_mostly_workflow_repo` | healthy workflow/test baseline without full release/governance surfaces | should rank above sparse and risky fixtures | 72 | `GOOD` | read-mostly permissions avoid dangerous penalty |
| `ci_but_no_tests_repo` | CI present but no tests | should get CI credit without fake testing maturity | 66 | `NEEDS_ATTENTION` | testing score remains intentionally low |
| `docs_only_repo` | strong docs without CI/tests | documentation improves, but overall maturity stays limited | 48 | `WEAK` | docs help, but missing automation/tests cap the score |
| `risky_permissions_repo` | explicit dangerous workflow posture | security and governance should drop materially | 44 | `WEAK` | `pull_request_target`, `contents: write`, `checks: write`, and `pull-requests: write` all penalize the score |
| `sparse_repo` | almost no maturity signals | should rank lowest | 8 | `WEAK` | low confidence, minimal assessable evidence |
| `private_checkout_boundary_repo` | same as mature plus `.topocore-v6`, artifacts, reports, and caches | ignored private/generated dirs should not improve score | 88 | `STRONG` | same score as mature fixture confirms boundary exclusion |

## 4. Rank Order

Expected order:

1. `mature_repo_fixture`
2. `read_mostly_workflow_repo`
3. `ci_but_no_tests_repo`
4. `docs_only_repo`
5. `risky_permissions_repo`
6. `sparse_repo`

Observed order matched the expected order in repeated local runs.

## 5. Calibration Findings

What worked:

- sparse repositories score far below mature repositories
- dangerous workflow permissions reduce security and governance scores
- CI without tests does not receive strong testing credit
- documentation can improve a repo profile without falsely making it `STRONG`
- ignored private/generated/runtime directories do not leak into evidence or improve scores

What needed adjustment before Sprint 80:

- Sprint 79 already widened directory exclusions and improved embedded config detection
- Sprint 80 benchmarking confirmed those earlier adjustments were sufficient for credible ordering without another scorer rewrite

Limitations:

- benchmark fixtures are synthetic and intentionally small
- the current audit remains repository-static and deterministic
- no runtime execution or deep private TopoCore scoring path is involved
- this benchmark supports demo credibility, not formal certification

## 6. Real Repo Observations

- `RepoBrain-Action` local repository: `80 / 100` `GOOD` in current local measurement
- `alexworkingai/Elen-MCP-v.2.2.0` latest live static baseline at Sprint 82 runtime: `78 / 100` `GOOD`
- `alexworkingai/Elen-MCP-v.2.2.0` latest live accepted `v6`-enriched result at Sprint 82 runtime: `77 / 100` `GOOD`

Latest Elen-MCP audit still surfaced a repository-level security improvement around other workflow files that retain `pull-requests: write`.
That finding is useful demo evidence and is separate from the Sprint 80 RepoBrain workflow permission hygiene fix.

These real-repository scores are observational only.
They are not part of the synthetic benchmark fixture ranking and should not be treated as calibration targets.

## 7. Demo Readiness

The current audit is credible as an MVP for demo use because it is:

- deterministic
- evidence-grounded
- bounded to `0-100`
- explicit about limitations
- safe and no-mutation by design

Sprint 81 adds a safe RepoBrain-side `topocore.audit_score.v1` contract boundary.
Sprint 82 adds a real private `run_audit_score_v1` provider behind that contract without exposing TopoCore source.
The benchmark still validates the static scorer independently, and RepoBrain keeps the static baseline as fallback truth whenever private `v6` enrichment is unavailable or rejected.

## 8. Safety

- no mutation
- no patch/autofix
- no security certification
- no merge approval
- no TopoCore source exposure
