# TopoCore v6 Orphaned v5 Vendor Asset Removal

## 1. Purpose

Sprint 66 removes orphaned v5 vendor assets and TKYA residue after Sprint 65 runtime removal.
v6 is the only supported TopoCore runtime.
This closes the physical cleanup gap left after runtime removal.

## 2. Baseline

Latest accepted `main` before Sprint 66:

- `7747954 Remove deprecated v5 runtime path`

Sprint 65 removed executable v5 runtime paths but did not explicitly remove every orphaned vendor asset on disk.
Sprint 66 addresses that gap.

## 3. Discovery Results

Discovery found:

- `repobrain/tkya/vendor` still existed on disk
- the legacy vendor file under that directory still existed on disk
- `.github/workflows/canary_v5.yml` still existed
- active code and tests still contained a small amount of legacy labeling and historical residue

Discovery did not find:

- any remaining active runtime import that executed vendor-backed v5 logic
- any supported workflow-dispatch choice that still exposed `v5` or `lite`

## 4. Files Deleted / Stubbed / Kept

| File / path | Action | Reason |
|---|---|---|
| `repobrain/tkya/vendor/` | deleted | orphaned v5 vendor assets were no longer needed after Sprint 65 runtime removal |
| `.github/workflows/canary_v5.yml` | deleted | old v5 canary workflow no longer reflected supported runtime behavior |
| `repobrain/tkya/engine.py` | kept as stub | import compatibility only; no v5 execution remains |
| `repobrain/tky_engine.py` | kept | stable request/decision contract, not a v5 runtime engine |
| `repobrain/tkya/__init__.py` | kept | compatibility export surface only |

## 5. Remaining Compatibility Stubs

Remaining compatibility stubs:

- `repobrain/tkya/engine.py`
  - remains only to preserve stable imports
  - contains no vendor import
  - contains no v5 execution logic
  - raises sanitized removal diagnostics immediately

## 6. Unsupported Legacy Inputs

Legacy inputs remain unsupported:

- `RB_TOPOCORE_BACKEND=v5`
- `RB_TKYA_BACKEND=v5`
- `RB_TKYA_BACKEND=lite`
- `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`
- `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`

Behavior:

- safe unsupported diagnostics only
- no v5 execution
- no vendor import

## 7. Verification

Sprint 66 verification proves:

- no `repobrain/tkya/vendor` directory remains
- no active runtime file imports a vendor-backed v5 engine
- no workflow file advertises `v5` or `lite` as supported runtime choices
- no active v5 vendor execution tests remain
- v6-focused runtime tests remain green

## 8. Safety Boundaries

- no patch application
- no file modification by RepoBrain behavior
- no commit, branch, or PR creation by RepoBrain behavior
- no production or Marketplace switch
- no `repobrain-community` change

## 9. Next Step

Recommended next sprint:

- `Sprint 67 - Post-v5 Removal Hardening and Live v6 Sanity`

Recommended scope:

- run bounded live v6 sanity
- final doc cleanup
- remove stale historical wording
- no v5 runtime work remains

## 10. Non-Goals

- no patch or autofix
- no production or Marketplace switch
- no `repobrain-community` change
