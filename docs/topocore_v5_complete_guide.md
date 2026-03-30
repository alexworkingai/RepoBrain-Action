# TopoCore TCX v5 Complete Guide

## Purpose
TopoCore TCX v5 is the active deterministic TKYA core used by RepoBrain for ask/review/fix routing and evidence compression.

## Active wiring
- Vendor engine: `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
- Selector: `repobrain/tkya/engine.py`
- Provider bridge: `repobrain/tky_local.py`
- Contract types: `repobrain/tky_engine.py`

## Engine flow (high level)
1. Normalize request + policy context.
2. Run security gate.
3. Score/rank candidates.
4. Compute route with topology + risk signals.
5. Build verification ladder summary.
6. Emit hash-only trace payload and stable diagnostics.
7. Return `EngineDecision`.

## `EngineDecision` fields
- `route`
- `selected_chunk_ids`
- `compression_stats`
- `security`
- `rationale`
- `stable_tokens`
- `execution_mode`
- `llm_intent`
- `llm_decision_reason_short`
- `llm_decision_reason_code`

## Canonical `compression_stats` groups
- Selection/routing: `retrieved`, `selected`, `phase1_action`, `top_score`
- Topology: `topology_mode`, `topology_complexity`, `topology_metric_count`
- HUK: `huk_score`, `huk_bars_hash`
- ZigZag: `zigzag_turning_points`, `zigzag_volatility`, `zigzag_trend`
- MorseFlow: `morse_risk`, `morse_verify_required`, `morse_confidence`, `morse_signals`
- Verification: `verification_*`, `verification_gate_decision`, `verification_gate_reason`
- Trace: `trace_schema_version`, `trace_schema_policy`, `trace_schema_compatible`, `trace`
- Safety/perf: `perf_candidates_truncated`, calibration fields

## Hash-only trace contract
`trace` contains hash and schema metadata only.
It does not persist raw prompt text, raw code snippets, or raw candidate payloads.

## Runtime controls
- `RB_TKYA_BACKEND=lite|v5`
- `RB_TKYA_STRICT=0|1`
- `RB_TKYA_STRICT_V5=0|1`
- `RB_TKYA_V5_PATH=<optional path>`
- `RB_TKYA_V5_CANARY_PERCENT=0..100`
- `RB_TKYA_CANARY_KEY=<stable key>`
- `RB_TKYA_ALLOW_REMOTE=0|1`

## Operational guidance
- Use `v5` for repository cognition with deterministic diagnostics.
- Keep fallback `lite` available for resilient startup.
- Export canonical decision truth through audit/evidence artifacts instead of recomputing parallel metrics.
