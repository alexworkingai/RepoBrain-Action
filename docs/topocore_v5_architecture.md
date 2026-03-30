# TopoCore TCX v5 Architecture (RepoBrain)

## Scope
This document describes the active TKYA architecture in RepoBrain.

- Active local TKYA engines: `v5` and safe fallback `lite`
- Active vendor file: `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
- Security posture: hash-only traces, no raw prompt/code persistence in engine diagnostics

## Runtime entrypoints
- Engine selector: `repobrain/tkya/engine.py`
- Local provider integration: `repobrain/tky_local.py`
- Engine contract: `repobrain/tky_engine.py`

## Decision contract
`TKYEngine.decide(req: EngineRequest) -> EngineDecision`

Key output fields used by RepoBrain:
- `route`
- `selected_chunk_ids`
- `compression_stats`
- `execution_mode`
- `llm_intent`
- `llm_decision_reason_short`
- `llm_decision_reason_code`

## Canonical v5 diagnostics in `compression_stats`
- Route context: `phase1_action`, `top_score`
- Topology: `topology_mode`, `topology_complexity`, `topology_metric_count`
- HUK: `huk_score`, `huk_bars_hash`
- ZigZag: `zigzag_turning_points`, `zigzag_volatility`, `zigzag_trend`
- MorseFlow: `morse_risk`, `morse_verify_required`, `morse_confidence`, `morse_signals`
- Verification ladder: `verification_*`, `verification_gate_decision`, `verification_gate_reason`
- Trace schema: `trace_schema_version`, `trace_schema_policy`, `trace_schema_compatible`
- Hash-only trace payload: `trace`

## Safety and boundedness
- Deterministic routing with explicit thresholds and policy gates
- Hash-only telemetry and diagnostics
- Verification gate summary exported to audit
- Ultra-large PR boundedness handled by orchestration layer, not by hidden engine behavior

## Environment controls
- `RB_TKYA_BACKEND=lite|v5`
- `RB_TKYA_STRICT=0|1`
- `RB_TKYA_STRICT_V5=0|1`
- `RB_TKYA_V5_PATH=<optional override path>`
- `RB_TKYA_V5_CANARY_PERCENT=0..100`
- `RB_TKYA_CANARY_KEY=<stable bucket key>`
- `RB_TKYA_ALLOW_REMOTE=0|1` (guarded, fail-closed when disabled)

## Notes
- RepoBrain keeps `v5` as the sole active vendor generation for TKYA.
- Legacy vendor generations are not part of active runtime wiring.
