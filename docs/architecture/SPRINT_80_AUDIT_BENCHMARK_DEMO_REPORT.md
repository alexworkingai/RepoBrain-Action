# Sprint 80 - Audit Benchmark And Demo Report

## 1. Purpose

Sprint 80 benchmarks audit scoring and produces a Microsoft/GitHub-facing demo report.
It follows Sprint 79 audit calibration and doctor/status.
It does not change runtime policy or enable mutation.

## 2. Baseline

- latest main before Sprint 80: `7a4118e Record doctor status live evidence`
- Sprint 79 status: `AUDIT_CALIBRATION_DIAGNOSTICS_PASSED`
- known Sprint 79 observation:
  - Elen-MCP permission drift:
    - `checks: write`
    - `pull-requests: write`

## 3. Benchmark Design

Benchmark fixtures:

- `sparse_repo`
- `docs_only_repo`
- `ci_but_no_tests_repo`
- `read_mostly_workflow_repo`
- `risky_permissions_repo`
- `mature_repo_fixture`
- `private_checkout_boundary_repo`

Expected order:

1. `mature_repo_fixture`
2. `read_mostly_workflow_repo`
3. `ci_but_no_tests_repo`
4. `docs_only_repo`
5. `risky_permissions_repo`
6. `sparse_repo`

Key expectations:

- strong repositories should outrank sparse repositories
- dangerous permissions should reduce security and governance
- CI without tests should not look mature
- ignored private/generated/runtime directories must not improve score or appear in evidence

## 4. Benchmark Results

| Fixture/repo | Score | Band | Expected rank | Observed rank | Pass/fail | Notes |
|---|---:|---|---:|---:|---|---|
| `mature_repo_fixture` | 88 | `STRONG` | 1 | 1 | pass | strongest overall benchmark fixture |
| `read_mostly_workflow_repo` | 72 | `GOOD` | 2 | 2 | pass | read-mostly workflow improves repo posture without full release scaffolding |
| `ci_but_no_tests_repo` | 66 | `NEEDS_ATTENTION` | 3 | 3 | pass | CI score improves, testing remains intentionally weak |
| `docs_only_repo` | 48 | `WEAK` | 4 | 4 | pass | docs help, but no tests/CI keeps the score low |
| `risky_permissions_repo` | 44 | `WEAK` | 5 | 5 | pass | dangerous permissions and trigger penalties land as expected |
| `sparse_repo` | 8 | `WEAK` | 6 | 6 | pass | minimal evidence, low confidence |
| `private_checkout_boundary_repo` | 88 | `STRONG` | n/a | tied with 1 | pass | same score as mature fixture confirms exclusion boundaries |

## 5. Calibration Changes

Sprint 80 code changes are benchmark and evidence oriented:

- benchmark suite added to lock ranking expectations
- no new scoring engine was introduced
- private/generated/runtime exclusion boundaries remain enforced

No overfitting statement:

- Sprint 80 does not tune the scorer to Elen-MCP
- real-repo results are observational only

## 6. Elen-MCP Permission Hygiene

- before permissions:
  - `checks: write`
  - `pull-requests: write`
- change made or deferred:
  - pending live-fix section update after the external workflow patch
- after doctor result:
  - pending live rerun
- PR/commit if any in Elen-MCP:
  - pending live-fix section update

## 7. Microsoft/GitHub Demo Report

- doc path: `docs/release/MICROSOFT_GITHUB_DEMO_REPORT.md`
- core narrative:
  - RepoBrain is GitHub-native repository intelligence and quality scoring, not just PR review
- proof points:
  - external pilot
  - live audit/doctor/status
  - deterministic 100-point audit scorer
  - no-mutation governance
- limitations:
  - current audit is still an MVP static scorer
  - deeper v6-backed scoring remains future work

## 8. Live Demo Results

- audit issue/run:
  - pending live rerun
- doctor issue/run:
  - pending live rerun
- status issue/run:
  - pending live rerun
- optional PR runs:
  - not planned unless needed

## 9. Product Status

Pre-live status target:

- `AUDIT_BENCHMARK_PARTIAL`

Final status will be updated after live audit/doctor/status reruns and Elen-MCP permission hygiene outcome.

## 10. Next Step

If Sprint 80 passes, recommended next step:

- Sprint 81 - Deep v6-backed Audit Scoring Design and TopoCore Contract

Preferred next step remains deeper v6-backed scoring design before any `/repobrain score` alias work.

## 11. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution
- no Microsoft partnership claim
