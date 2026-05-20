# TopoCore v6 Opt-In v5-Off Simulation

## 1. Purpose

Sprint 63 implements opt-in v5-off simulation.
v6 remains the active `issue_comment` lab default.
v5 remains fallback-only and a deprecation candidate.
This sprint does not remove v5.
This sprint does not disable fallback by default.

## 2. Current Operating State

Latest accepted `main` before Sprint 63:

- `a89976e Prepare code-level v5 deprecation`

Current operating state:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- v6 active lab default
- v5 fallback-only
- v5 removal not approved

## 3. Simulation Variable

Simulation variable:

- `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`

Default:

- off

Truthy values:

- `1`
- `true`
- `yes`
- `on`
- `y`

Falsey values:

- unset
- `0`
- `false`
- `no`
- `off`
- empty string

Safe diagnostic reason:

- `v5_simulated_disabled`

## 4. Behavior Matrix

| Backend selection | Simulation off | Simulation on | Expected reason / marker | Notes |
|---|---|---|---|---|
| explicit `v5` | executes current v5-side path | blocked safely | `v5_simulated_disabled` | no v5 execution |
| legacy `lite` via `RB_TKYA_BACKEND` | executes current v5-side compatibility path | blocked safely | `v5_simulated_disabled` | `lite` remains treated as v5-side |
| `auto` + v6 available | resolves to v6 or falls back to v5 if needed | resolves to v6 | `fallback_used=false` | no behavior drift when v6 is healthy |
| `auto` + v6 unavailable | may fall back to v5 | fails safely | `v5_simulated_disabled` | no silent fallback to simulated-disabled v5 |
| explicit `v6` + v6 available | resolves to v6 | resolves to v6 | `fallback_used=false` | unchanged healthy path |
| explicit `v6` + v6 unavailable | safe failure or existing strict behavior | safe failure | existing v6-unavailable handling | simulation does not change v6 path itself |
| gate=`0` kill switch | still resolves to v5 | blocked safely | `v5_simulated_disabled` | only when simulation is explicitly enabled |
| `workflow_dispatch` v6 | unchanged | unchanged | v6 path remains available | workflow defaults unchanged |

## 5. Safety Boundaries

- no v5 deletion
- no fallback disablement by default
- no workflow or `action.yml` change
- no repository variable change
- no `decide_raw`
- no patch application
- no file modification
- no commit, branch, or PR creation
- no production or Marketplace switch
- no `repobrain-community` change

## 6. Test Coverage

Sprint 63 adds coverage for:

- simulation helper defaults, truthy values, and falsey values
- metadata policy helper exposure
- explicit `v5` blocked safely when simulation is enabled
- legacy `lite` blocked safely when simulation is enabled
- `auto` plus v6 available still resolving to v6
- `auto` plus v6 unavailable no longer silently falling back to v5
- gate=`0` semantics with simulation off and with simulation on
- no import side-effect assumptions for the metadata layer
- existing fallback tests remaining valid when simulation is off

## 7. Next Step

Recommended next sprint:

- `Sprint 64 - Run v5-Off Simulation Checkpoint`

Recommended scope:

- run targeted local tests with simulation enabled
- optionally run `workflow_dispatch` or `issue_comment` diagnostics if safe
- decide whether code-level v5 deprecation can be activated
- still no removal

## 8. Sprint 64 Follow-Up

Sprint 64 supersedes the normal fallback semantics from Sprint 63:

- v5 is now disabled by default
- deprecated v5 emergency allow is a separate control:
  - `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`
- simulation remains the hard-block test mode:
  - `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`
- if both are set, simulation wins and v5 remains blocked with:
  - `v5_simulated_disabled`

See also:

- `docs/architecture/TOPOCORE_V6_AUTHORITATIVE_DISABLE_V5_DEFAULT.md`
