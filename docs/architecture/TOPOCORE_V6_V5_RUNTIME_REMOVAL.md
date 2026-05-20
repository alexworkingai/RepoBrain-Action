# TopoCore v6 v5 Runtime Removal

## 1. Purpose

Sprint 65 removes deprecated v5 runtime execution.
v6 is now the only supported TopoCore runtime path.
Legacy v5 and `lite` env values now produce safe unsupported diagnostics instead of execution.
This sprint does not enable patch or autofix.
This sprint does not change `repobrain-community`.

## 2. Baseline

Latest accepted `main` before Sprint 65:

- `21f94f8 Make v6 authoritative and disable v5 fallback`

Sprint 64 state:

- v6 authoritative
- v5 fallback disabled by default
- deprecated emergency v5 still physically present

Sprint 65 removes that deprecated emergency execution path.

## 3. Removed Runtime Paths

Removed from executable runtime behavior:

- explicit `v5` backend execution
- legacy `lite` backend execution
- `auto` fallback to v5
- emergency deprecated-v5 allow execution
- workflow and action advertised `v5` / `lite` choices

## 4. Unsupported Legacy Inputs

| Legacy input | Expected result | Reason code | v5 execution |
|---|---|---|---|
| `RB_TOPOCORE_BACKEND=v5` | safe unsupported diagnostic | `deprecated_v5_removed` or `deprecated_v5_env_unsupported` | no |
| `RB_TKYA_BACKEND=v5` | safe unsupported diagnostic | `unsupported_legacy_backend` or `deprecated_v5_env_unsupported` | no |
| `RB_TKYA_BACKEND=lite` | safe unsupported diagnostic | `legacy_lite_removed` | no |
| `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1` | ignored as runtime re-enable control | `deprecated_v5_env_unsupported` when paired with legacy v5 input | no |
| `RB_TOPOCORE_V5_SIMULATE_DISABLED=1` | obsolete compatibility input; no v5 path remains | `v5_simulated_disabled` only as legacy diagnostic metadata if surfaced | no |

## 5. Current Runtime Policy

Supported backend selectors:

- `auto`
- `v6`

If v6 is unavailable:

- fail safely
- do not fallback to v5
- use bounded diagnostics such as `v6_unavailable` or `v6_required`

`workflow_dispatch` with v6 and `private_checkout` remains supported.
Default CI still does not require private `topocore_v6` unless a v6 path is actually executed.

## 6. Files Removed or Stubbed

Compatibility/runtime status:

- `repobrain/tkya/engine.py`
  - kept as a compatibility stub
  - no v5 execution logic remains
  - raises sanitized removal diagnostics immediately
- `repobrain/tky_engine.py`
  - kept
  - request and decision contract only
  - not a fallback runtime engine

Removed tests:

- `tests/test_tkya_engine.py`
- `tests/test_topocore_v5_vendor.py`
- `tests/test_rd_audit_integration.py`

## 7. Test Migration

Sprint 65 test migration:

- deleted pure v5-execution tests
- migrated backend selection tests from “deprecated v5 emergency allow” to “old env unsupported”
- added runtime-removal coverage:
  - `tests/test_topocore_v5_runtime_removed.py`
- preserved safety tests:
  - no `decide_raw`
  - no patch or autofix
  - no private dependency requirement in default CI
  - safe failure when v6 is unavailable

## 8. Safety Boundaries

- no `decide_raw`
- no patch application
- no file modification by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no unsafe approval or security claim
- no production or Marketplace switch
- no `repobrain-community` change

## 9. Next Step

Recommended next sprint:

- `Sprint 66 - Post-v5 Removal Hardening and Documentation Cleanup`

Recommended scope:

- remove stale documentation mentions
- verify no old env assumptions remain
- optional live v6 sanity
- no patch or autofix

## 10. Sprint 66 Follow-Up

Sprint 66 completes the physical cleanup that Sprint 65 left open:

- orphaned v5 vendor assets are removed
- stale TKYA residue is reduced to compatibility stubs only
- active workflow and test surfaces no longer advertise v5 or `lite` as runnable runtime choices

See also:

- `docs/architecture/TOPOCORE_V6_ORPHANED_V5_VENDOR_ASSET_REMOVAL.md`
## 11. Non-Goals

- no patch or autofix
- no production or Marketplace switch
- no `repobrain-community` change


## 12. Sprint 67 Follow-Up

Sprint 67 removed the remaining standalone v5 guide docs and completed the final residue sweep. See `docs/architecture/TOPOCORE_V6_FINAL_V5_RESIDUE_SWEEP.md`.
