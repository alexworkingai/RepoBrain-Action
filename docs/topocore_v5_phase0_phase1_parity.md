# TopoCore v5 Parity (Phase 0 + 1 + 2 + 4 + 5 + 6 + 7 + 8 + 9 + 10 + 11)

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
| Verification adapter full ladder | Yes | Yes (planner + branch profiles + ladder gate) | Phase 8 expanded |
| Codegen adapter | Yes | No | Pending |
| Crypto engine | Yes | No | Pending |
| Trace subsystem | Yes | Yes (hash-only trace object + schema policy) | Phase 11 expanded |
| DS/BigAnalytics kernels | Partial | Yes (series + vector + graph + path + temporal/anomaly) | Phase 9 expanded |
| v2 specialized compatibility | Yes | Optional shim + explicit adapter registry + policy control | Phase 7 expanded |
| Versioned trace schema | No explicit schema key | Yes (`trace_schema_version=1.1`) | Phase 6 added |
| Perf/capacity safeguards | Limited | Yes (candidate/data truncation budgets) | Phase 10 added |
| Rollout controls | N/A | Canary-ready runtime policy | Phase 11 added |

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
- `verification_profile`
- `verification_branch`
- `verification_required_checks`
- `v2_compat_used`
- `v2_compat_reason`
- `v2_compat_caps`
- `v2_compat_adapters`
- `v2_compat_adapter_results`
- `v2_compat_adapter_results_hash`
- `v2_compat_policy`
- `v2_compat_policy_hash`
- `v2_compat_path_hash`
- `v2_compat_topology_call`
- `v2_compat_topology_hash`
- `v2_compat_topology_keys_count`
- `trace_schema_version`
- `trace_schema_policy`
- `trace_schema_compatible`
- `verification_gate_decision`
- `verification_gate_reason`
- `topology_perf`
- `perf_candidates_truncated`
- `calibration_min_fast_score`
- `calibration_verify_threshold`
- `calibration_zigzag_turning_threshold`

## Immediate next parity targets

1. Add richer branch policy presets with severity mapping by repository tier.
2. Add execution budgets/timeouts per shim adapter.
3. Extend temporal analytics to multi-entity drift windows.
4. Keep trace schema migration backward-compatible for upcoming `2.x`.
