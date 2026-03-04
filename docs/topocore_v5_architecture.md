# TopoCore v5 Architecture for RepoBrain-Action

This document is the permanent architecture reference for:

* `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
* integration flow via `repobrain/tkya/engine.py`
* local provider wiring via `repobrain/tky_local.py`

It also contains a migration and parity map against legacy v2.

## 1) Purpose and scope

TopoCore v5 is the primary local TKYA engine for RepoBrain-Action. It is designed for:

* deterministic routing and selection in RepoBrain runtime flows,
* hash-only diagnostics and audit safety,
* GitHub-aware behavior (PR/diff/risk signals),
* support for complex DataScience and BigAnalytics workloads through structural metrics.

### Non-goals

* no mandatory remote/network behavior,
* no raw candidate text or patch content persistence in engine traces,
* no secrets in code or audit artifacts.

## 2) Runtime contract

RepoBrain expects the engine contract from `repobrain/tky_engine.py`:

* `TKYEngine.decide(req: EngineRequest) -> EngineDecision`
* request fields:
  * `task_type`: `ask | locate | explain | review`
  * `query`: `{text, signature}`
  * `candidates`: list of `EngineCandidate`
  * `limits`: runtime tuning dictionary
  * `policy`: runtime policy dictionary
* decision fields:
  * `route`
  * `selected_chunk_ids`
  * `compression_stats`
  * `security`
  * `rationale`
  * `stable_tokens`

Local provider integration:

* `repobrain/tky_local.py` converts RepoBrain candidates to `EngineRequest`.
* `repobrain/github_flow.py` consumes route and selected ids and runs 1-pass/2-pass logic.

## 3) High-level decision flow

`TopoCoreTCXv5AdvanceCASGit.decide(req)` executes this sequence:

1. normalize task and inputs,
2. security check and possible immediate `REFUSE`,
3. apply performance budgets to candidate set,
4. compute topology/analytics metrics,
5. compute HUK gate score and symbolic codes,
6. run diff-aware ranking with GitHub context boosts,
7. compute ZigZag and MorseFlow risk signals,
8. choose route/action (`FAST | DEEP | REVIEW | REFUSE`),
9. select chunk ids under limits,
10. compute verification ladder and gate decision,
11. enrich diagnostics from optional v2 compatibility shim,
12. build hash-only trace payload (`trace_schema_version=1.1`),
13. optionally run R&D pipeline telemetry (feature-flagged),
14. return `EngineDecision`.

## 4) Core modules in v5

### 4.1 Security layer

* `detect_injection_or_exfiltration` integration (when available in repo).
* internal security markers for defense-in-depth.
* deterministic `REFUSE` route with explicit `EngineSecurity`.

### 4.2 Symbolization and HUK gate

* `Codebook`, `CodebookRegistry`, `Symbolizer`
* `HUKCore.fast_gate` computes:
  * entropy-like signal,
  * token density/smoothness proxies,
  * score and symbolic codes.

### 4.3 Routing

`TopoRoute` maps confidence and risk to actions:

* `NARROW_RETRIEVAL`
* `REDUCE_BRANCHING`
* `EXPAND`
* `VERIFY`

Action plus task/risk context determines route:

* `FAST` for high-confidence and low risk,
* `DEEP` for low-confidence or elevated risk,
* `REVIEW` for review tasks,
* `REFUSE` for blocked requests.

### 4.4 DataScience topology kernel

`DataScienceTopologyKernel` computes unified metrics across:

* temporal series,
* vectors,
* graph edges,
* path lengths.

Outputs:

* `mode` (for example `analytics_graph_vector_temporal`),
* `complexity` (`low | medium | high`),
* metric dictionary,
* perf truncation counters.

### 4.5 ZigZag and MorseFlow

* `ZigZagAnalyzer`: turning points, volatility, trend.
* `MorseFlowGate`: PR/diff risk signals:
  * conflict markers,
  * secret-like patterns,
  * workflow-risk patterns,
  * test-disable signals,
  * TODO/FIXME counts.

### 4.6 Verification planner

`VerificationPlanner` tracks:

* observed PASS/FAIL/PENDING checks,
* required checks by task/profile/branch,
* NOT_RUN coverage,
* gate decision:
  * `PASS`
  * `WARN`
  * `WAIT`
  * `BLOCK`

### 4.7 v2 compatibility shim

`V2CompatibilityShim` is optional and disabled by default.

Capabilities:

* loads legacy `TopoCore_TCX_v2-CAS.py` on demand,
* runs selected adapters under policy allow/deny,
* exports hash-only diagnostics and adapter states.

No raw legacy outputs are stored.

### 4.8 Optional R&D telemetry

When enabled, v5 can call local R&D pipeline and embed hash-only summary:

* codegen template id,
* policy hash,
* signature/attestation flags,
* error/warning counters,
* record hash.

This does not change default behavior when disabled.

## 5) GitHub and RepoBrain integration behavior

### 5.1 Two-pass retrieval loop

RepoBrain (`repobrain/github_flow.py`) uses route from TKYA:

* pass 1 with `topk_fast`,
* if route is `DEEP` for `ask/explain`, run pass 2 with `topk_deep`,
* use final decision from last pass.

### 5.2 Evidence and audit

* v5 returns selected chunk ids only, not raw code text.
* audit stores hash-only or numeric diagnostics.
* formatting prints compact status lines and never injects raw candidate text.

## 6) Safety and privacy model

* default remote/network disabled unless explicit `RB_TKYA_ALLOW_REMOTE=1`,
* no secrets in repository code paths,
* no raw text persistence in trace data,
* route-level refusal for injection/exfiltration signals.

## 7) Environment controls

### 7.1 Engine selection and strictness

Managed in `repobrain/tkya/engine.py`:

* `RB_TKYA_BACKEND`:
  * `lite`
  * `v5`
  * `original`
* `RB_TKYA_STRICT_V5=1` for fail-fast v5 startup.
* `RB_TKYA_STRICT_ORIGINAL=1` for fail-fast original startup.
* `RB_TKYA_V5_PATH` optional custom path override.

### 7.2 Remote guards

* `RB_TKYA_ALLOW_REMOTE=0` by default.
* with remote disabled, guarded methods raise controlled runtime error.

### 7.3 Canary rollout

* `RB_TKYA_V5_CANARY_PERCENT=0..100`
* `RB_TKYA_CANARY_KEY=<stable key>`

### 7.4 v2 compatibility shim

* `RB_TKYA_ENABLE_V2_SHIM=1`
* `RB_TKYA_V2_SHIM_PATH=/path/to/TopoCore_TCX_v2-CAS.py`
* `RB_TKYA_V2_SHIM_STRICT=1`

### 7.5 Optional R&D telemetry

* `RB_TKYA_ENABLE_RD_PIPELINE=1`
* `RB_TKYA_RD_SIGNING_SECRET=<secret>`
* `RB_TKYA_RD_ENABLE_CHAIN=1`

## 8) Why v5 replaced v2 as primary engine

Primary reasons:

* strict compatibility with RepoBrain engine contract,
* deterministic machine-level output (route + selected ids),
* richer PR-aware and audit-aware diagnostics,
* better operational control (budgets, gating, rollout controls),
* safer privacy posture in CI/runtime.

v2 remains useful as legacy logic source and optional shim input.

## 9) v2 to v5 migration summary by subsystem

| Subsystem | v2 status | v5 status | Migration intent |
|---|---|---|---|
| API surface | `handle_request` oriented | `decide(req)` contract-native | Match RepoBrain runtime needs |
| Routing output | action-centric | route-centric (`FAST/DEEP/REVIEW/REFUSE`) | Feed 2-pass flow deterministically |
| Candidate selection | indirect | direct `selected_chunk_ids` | Improve evidence precision and token economy |
| Security | internal detector stack | unified with RepoBrain security + route refuse | Single policy model |
| GitHub context | limited | first-class PR/diff context | Better relevance in issue/PR workflows |
| Verification ladder | adapter-based | planner + branch/profile gating | CI-like governance semantics |
| DS analytics | domain adapters | unified topology kernel | Generalized analytics support |
| Trace | hash-only concept | versioned hash-only schema (`1.1`) | Stable observability contract |
| Legacy support | native | optional shim | Controlled backward compatibility |
| Remote safety | mixed | explicit fail-closed defaults | Stronger secure-by-default behavior |

## 10) Full comparative matrix (v2 vs v5)

| Attribute | v2 | v5 |
|---|---|---|
| Primary class | `TopoCoreTCXv2CAS` | `TopoCoreTCXv5AdvanceCASGit` |
| File role | standalone orchestration core | RepoBrain-native decision engine |
| Main entry | `handle_request(...)` | `decide(req)` |
| Native RepoBrain contract | partial | full |
| Route model | action-oriented | explicit `FAST/DEEP/REVIEW/REFUSE` |
| Selection output | not primary | `selected_chunk_ids` primary |
| Determinism | moderate | strong deterministic behavior |
| PR diff awareness | limited | built-in (`GitHubContext`, diff boosts) |
| Verification representation | basic ladder | ladder + gate decision + branch profiles |
| Security refusal route | indirect | explicit `REFUSE` route |
| Trace schema versioning | minimal | explicit `trace_schema_version=1.1` |
| Perf budgets | limited | candidate/data truncation controls |
| DS kernel breadth | adapters and heuristics | unified temporal/vector/graph/path metrics |
| ZigZag component | `ZigZagTDA` | `ZigZagAnalyzer` |
| Morse component | `MorseFlowCore` | `MorseFlowGate` (PR-risk aware) |
| Legacy compatibility | native | optional `V2CompatibilityShim` |
| Optional R&D telemetry | none | supported behind feature flags |
| Remote behavior default | not strictly centralized | fail-closed by env guard |
| Audit friendliness | moderate | high (rich `compression_stats`) |
| RepoBrain two-pass loop compatibility | indirect | direct by route result |
| Operational rollout controls | limited | canary + strict/fallback controls in loader |

## 11) Operational guidance

Recommended production-like local posture:

* backend: `RB_TKYA_BACKEND=v5`
* keep remote disabled unless explicitly required:
  * `RB_TKYA_ALLOW_REMOTE=0`
* use strict startup in controlled environments:
  * `RB_TKYA_STRICT_V5=1`
* keep v2 shim disabled unless migration testing:
  * `RB_TKYA_ENABLE_V2_SHIM=0`

Recommended migration posture:

1. run v5 as primary with current tests,
2. enable shim only for targeted parity checks,
3. remove shim dependencies once parity targets are met.

## 12) Testing and quality loop

Baseline commands:

```powershell
pip install -e ".[dev]"
ruff check .
pytest -q
```

Optional focused checks:

```powershell
pytest -q tests/test_topocore_v5_vendor.py
pytest -q tests/test_tkya_engine.py
pytest -q tests/test_rd_audit_integration.py
```
