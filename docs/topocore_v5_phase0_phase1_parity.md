# TopoCore v5 Parity (Phase 0 + Phase 1)

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
| Review verification flags | Yes (ladder in adapter) | Yes (`verified/not_run`) | Partial parity |
| GitHub diff-aware hints | No explicit engine layer | Planned in next increment | Pending |
| ZigZag/MorseFlow | Yes | No | Pending |
| Blockchain adapter | Yes | No | Pending |
| Verification adapter full ladder | Yes | No (metadata only) | Pending |
| Codegen adapter | Yes | No | Pending |
| Crypto engine | Yes | No | Pending |
| Trace subsystem | Yes | No dedicated object | Pending |

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
- `verified`
- `not_run`

## Immediate next parity targets

1. Add ZigZag structural analyzer and connect it to `decide`.
2. Add `MorseFlow` conflict/merge gate hooks.
3. Add minimal `VerificationAdapter` planner (without external execution).
4. Add PR diff-aware scoring layer in engine (file + line overlap).
5. Add hash-only trace object in v5.
