# TopoCore v5 Parity (Phase 0 + Phase 1 + Phase 2 + Phase 4)

This document tracks parity targets between:

- `repobrain/tkya/vendor/TopoCore_TCX_v2-CAS.py`
- `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`

## Scope in this increment

- Phase 0: deterministic structure + parity-oriented output fields.
- Phase 1: restored primitives:
  - `Codebook`
  - `CodebookRegistry`
  - `Symbolizer` (+ Hamming gap enforcement)
  - `HUKCore` (fast gate)
  - `TopoRoute` (action-level routing)

## Feature Matrix (current)

| Subsystem | v2 | v5 now | Status |
|---|---|---|---|
| CoreLocked security gate | Yes | Yes | Partial parity |
| Engine contract `decide(req)` | No native (adapter path) | Yes | Added in v5 |
| Codebook/registry/symbolizer | Yes | Yes | Phase 1 restored |
| HUK fast gate | Yes | Yes | Phase 1 restored |
| Action router (`NARROW/VERIFY/...`) | Yes | Yes | Phase 1 restored |
| Deterministic selection/ranking | Partial | Yes | Improved in v5 |
| Review verification flags | Yes (ladder in adapter) | Yes (`PASS/FAIL/PENDING/NOT_RUN`) | Phase 4 expanded |
| GitHub diff-aware hints | No explicit engine layer | Yes (file/range boosts) | Phase 2 started |
| ZigZag/MorseFlow | Yes | Yes (confidence + workflow risk signals) | Phase 4 expanded |
| Blockchain adapter | Yes | No | Pending |
| Verification adapter full ladder | Yes | Partial (planner + ladder stats) | In progress |
| Codegen adapter | Yes | No | Pending |
| Crypto engine | Yes | No | Pending |
| Trace subsystem | Yes | Yes (hash-only trace object) | Phase 4 expanded |
| DS/BigAnalytics kernels | Partial | Yes (series + vector + graph + path metrics) | Phase 4 expanded |

## Runtime signals added in v5

`compression_stats` now includes parity/debug keys:

- `phase1_action`
- `phase1_params`
- `huk_score`
- `huk_bars_hash`
- `codebook_id`
- `topology_mode`
- `topology_complexity`
- `topology_metric_count`
- `zigzag_turning_points`
- `zigzag_volatility`
- `zigzag_trend`
- `morse_risk`
- `morse_verify_required`
- `morse_confidence`
- `morse_signals`
- `morse_workflow_risky`
- `morse_test_disable_signal`
- `diff_boosted_candidates`
- `trace` (hash-only)
- `verified`
- `not_run`
- `verification_ladder`
- `verification_pass_count`
- `verification_fail_count`
- `verification_pending_count`
- `verification_not_run_count`
- `verification_completeness`
- `verification_strict_pass`

## Immediate next parity targets

1. Add optional compatibility shim for selected v2 specialized adapters (without hard dependency).
2. Extend verification planner with branch-protection profiles and required CI sets by task type.
3. Add deeper topology modes for temporal graphs and anomaly windows.
4. Keep hash-only trace stable-token schema versioned for downstream tooling.
