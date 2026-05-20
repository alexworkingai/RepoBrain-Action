# TopoCore v6 Authoritative Disable v5 Default

> Sprint 67 status: This file is retained only as a historical checkpoint. For current runtime policy use `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`, `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`, and `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`.

## 1. Purpose

Sprint 64 makes v6 authoritative.
v5 fallback is disabled by default.
v5 remains physically present only as a deprecated emergency opt-in.
This sprint does not remove v5 files.
This sprint does not enable patch or autofix.

## 2. Current Operating State

Latest accepted `main` before Sprint 64:

- `62cfda6 Implement opt-in v5-off simulation`

Current operating state:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`
- v6 active `issue_comment` lab default
- v5 deprecation candidate
- Sprint 64 policy:
  - v5 disabled by default
  - deprecated v5 emergency opt-in only

## 3. New Emergency Opt-In

Emergency opt-in variable:

- `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`

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

Why it exists:

- one-sprint rollback and emergency compatibility seam
- controlled fallback while v5 code still exists

Why it is not normal fallback:

- v5 is deprecated and not authoritative
- default behavior now prefers safe failure over silent v5 execution
- emergency use must be explicit and visible in diagnostics

Interaction with other controls:

- `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`
  - hard-block test mode
  - wins over emergency allow
- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=0`
  - disables the v6 issue-comment lab path
  - no longer means normal v5 runtime by itself

## 4. Behavior Matrix

| Scenario | Default Sprint 64 behavior | With `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1` | With `RB_TOPOCORE_V5_SIMULATE_DISABLED=1` | Reason code |
|---|---|---|---|---|
| explicit `v5` | blocked safely | deprecated v5 may execute | blocked | `deprecated_v5_not_allowed` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |
| legacy `lite` | blocked safely | deprecated lite compatibility may execute | blocked | `legacy_lite_disabled_by_default` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |
| `auto` + v6 available | resolves to v6 | resolves to v6 | resolves to v6 | `none` |
| `auto` + v6 unavailable | safe failure | may fallback to deprecated v5 | blocked | `v6_unavailable_v5_disabled` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |
| explicit `v6` + v6 available | resolves to v6 | resolves to v6 | resolves to v6 | `none` |
| explicit `v6` + v6 unavailable | safe failure | may fallback to deprecated v5 | blocked | `v6_unavailable_v5_disabled` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |
| gate=`1` `issue_comment` | v6 authoritative path | same | same | `none` when healthy |
| gate=`0` `issue_comment` | safe disabled or deprecated-v5-not-allowed result | deprecated v5 emergency path | blocked | `deprecated_v5_not_allowed` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |
| `workflow_dispatch` v6 | supported | supported | supported | `none` when healthy |
| `workflow_dispatch` v5 | blocked safely | deprecated v5 emergency path | blocked | `deprecated_v5_not_allowed` / `v5_deprecated_emergency_allowed` / `v5_simulated_disabled` |

## 5. Changed Meaning of Kill Switch

`RB_ENABLE_ISSUE_COMMENT_V6_LAB=0` no longer automatically means normal v5 runtime.
It disables the v6 `issue_comment` lab path.
Deprecated v5 emergency runtime additionally requires:

- `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`

Without the allow flag, gate=`0` should fail or stop safely rather than silently run deprecated v5.

## 6. Safety Boundaries

- no v5 file deletion
- no workflow private dependency default-CI requirement
- no patch application
- no commit, branch, or PR creation by RepoBrain
- no `decide_raw`
- no production or Marketplace switch
- no `repobrain-community` change

## 7. Test Coverage

Sprint 64 covers:

- v6 authoritative policy tests
- v5 disabled-by-default tests
- emergency deprecated-v5 tests
- simulation-wins-over-allow tests
- auto no-silent-fallback tests
- GitHub action and workflow static alignment tests

## 8. Sprint 65 Entry Criteria

If Sprint 64 validation passes and no post-merge blocker appears:

- Sprint 65 may remove the deprecated v5 runtime path
- removal still needs explicit Sprint 65 approval
- the emergency allow flag may be removed or converted to an unsupported-old-env diagnostic in Sprint 65

## 9. Sprint 65 Follow-Up

Sprint 65 completed the next removal step:

- deprecated emergency v5 runtime execution was removed
- legacy `lite` execution was removed
- old v5 and `lite` env values now fail safely instead of executing

See also:

- `docs/architecture/TOPOCORE_V6_V5_RUNTIME_REMOVAL.md`
## 10. Non-Goals

- no v5 physical removal
- no production or Marketplace switch
- no patch or autofix
- no `repobrain-community` change
