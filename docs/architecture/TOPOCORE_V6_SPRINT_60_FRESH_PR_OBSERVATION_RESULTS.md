# TopoCore v6 Sprint 60 Fresh PR Observation Results

## 1. Purpose

Sprint 60 validates Sprint 59 PR output and backend evidence on a fresh PR based on current `main`.
This fixes the stale-fixture problem from PR `#87`.
Sprint 60 decides whether v6 lab mode can become the active lab default.
Sprint 60 does not remove v5.
Sprint 60 does not enable patch application.

## 2. Baseline

Latest accepted `main` before Sprint 60:

- `b6e3fd2 Expose PR TopoCore backend evidence`

Sprint 59 result:

- `PARTIAL_PASS`

Reason:

- PR `#87` was stale and not usable as current-main promotion evidence

Starting variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`

## 3. Fixture PR

- Branch: `codex/sprint-60-v6-pr-evidence-fixture`
- PR number: `112`
- PR URL: `https://github.com/alexworkingai/RepoBrain-Action/pull/112`
- Head SHA: `f17325b783bf376372bcaaad5ea59e594ccfb544`
- Base SHA: `b6e3fd2c20d4c01161beb0acaf5fe3a4c667b3b8`
- Changed files: `1`
- Fixture file: `docs/architecture/TOPOCORE_V6_SPRINT_60_PR_FIXTURE.md`
- Final PR state: `closed`

## 4. Gate=1 PR Evidence

| Scenario | Command | Run URL | Conclusion | Requested backend | Resolved backend | Fallback used | Fallback reason | TKYA mode | Scope status | Visible evidence present | Safety result | Decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PR ask | `/repobrain ask Summarize this PR with TopoCore backend diagnostics.` | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26110006182` | `success` | `auto` | `v6` | `no` | `none` | `topocore_v6` | `n/a` | `yes` | `pass` | `pass` |
| PR review | `/repobrain review Summarize review risks for this PR.` | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26110060523` | `success` | `auto` | `v6` | `no` | `none` | `topocore_v6` | `n/a` | `yes` | `pass` | `pass` |
| PR verify | `/repobrain verify Summarize verification status for this PR.` | `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26110126004` | `success` | `auto` | `not_applicable` | `not_applicable` | `verify_report_only` | `scoped_unsupported` | `verify_report_only` | `yes` | `pass` | `pass` |

Supporting observations:

- PR ask visible output included `Runtime backend evidence` with:
  - `TKY mode requested: local`
  - `TKY mode used: local`
  - `TKYA mode: topocore_v6`
  - `TopoCore backend requested: auto`
  - `TopoCore backend resolved: v6`
  - `TopoCore fallback used: no`
  - `TopoCore fallback reason: none`
- PR review visible output included the same promoted TopoCore evidence fields and did not claim approval, security clearance, or safe-to-merge status.
- PR verify remained report-only, but it exposed explicit safe scope evidence:
  - `TopoCore backend requested: auto`
  - `TopoCore backend resolved: not_applicable`
  - `TopoCore fallback used: not_applicable`
  - `TopoCore fallback reason: verify_report_only`
  - `Scope status: verify_report_only`

## 5. workflow_dispatch Sanity

- Run URL: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26110183422`
- `requested_backend=v6`
- `resolved_backend=v6`
- `fallback_used=false`
- `fallback_reason=none`
- Result: `pass`

## 6. Gate=0 Kill Switch

- Run URL: `https://github.com/alexworkingai/RepoBrain-Action/actions/runs/26110248716`
- `requested_backend=v5`
- `resolved_backend=v5`
- private checkout/install status: `skipped`
- Result: `pass`

Visible gate=`0` issue output confirmed:

- `TKY mode requested: auto`
- `TKY mode used: baseline`
- `TKYA backend: v5`
- `TKYA mode: baseline-policy`
- `TopoCore backend requested: v5`
- `TopoCore backend resolved: v5`
- `TopoCore fallback used: no`
- `TopoCore fallback reason: none`

## 7. Safety Evidence

- `decide_raw` used: `no`
- patch application: `no`
- file modification by RepoBrain: `no`
- commit, branch, or PR creation by RepoBrain: `no`
- unsafe approval, security, or safe-to-merge claims: `no`
- secret or private URL exposure: `no`

## 8. Decision

Decision:

- `PROMOTE_V6_LAB_DEFAULT`

Final variable state:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Reason:

- fresh PR `ask` output showed visible TopoCore backend evidence with `resolved_backend=v6`
- fresh PR `review` output showed visible TopoCore backend evidence with `resolved_backend=v6`
- fresh PR `verify` output showed explicit `verify_report_only` scoped evidence without ambiguity
- `workflow_dispatch` sanity resolved to v6
- gate=`0` kill switch still resolved cleanly to v5
- no safety failures were observed

v5 status:

- temporary fallback only

Whether v5 deprecation candidate can be proposed next:

- `yes`

## 9. Non-Goals

- no v5 removal
- no v5 code deprecation
- no production or Marketplace switch
- no patch application
- no commit, branch, or PR creation by RepoBrain behavior
- no `repobrain-community` change
