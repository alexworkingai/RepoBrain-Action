# R&D Track Contracts (R&D-1 .. R&D-9)

This document defines the lightweight R&D path added to RepoBrain without extra dependencies.

## Scope

* Deterministic local code generation via templates.
* Static validation gates before any signing/attestation.
* HMAC-based artifact signing.
* In-memory append-only attestation chain for local/prototype flows.
* Canary rollout helpers for controlled enablement.
* Orchestration pipeline that composes all stages with hash-only diagnostics.

## Modules

* `repobrain/rd_codegen.py`
  * `generate_code(intent, context) -> CodegenResult`
* `repobrain/rd_validation.py`
  * `validate_codegen_artifact(content, language, sandbox_policy) -> ValidationResult`
* `repobrain/rd_crypto.py`
  * `derive_signing_key(secret, ...) -> bytes`
  * `sign_payload(key, payload, ts, nonce) -> SignatureEnvelope`
  * `verify_payload(key, payload, envelope) -> bool`
* `repobrain/rd_blockchain.py`
  * `InMemoryChainAdapter.append_event(...) -> ChainRecord`
  * `InMemoryChainAdapter.export_summary() -> dict`
  * `build_attestation_record(...) -> dict`
* `repobrain/rd_rollout.py`
  * `stable_bucket(key) -> int`
  * `canary_enabled(percent, key) -> bool`
  * `resolve_rollout_mode(...) -> str`
* `repobrain/rd_orchestration.py`
  * `run_rd_pipeline(...) -> RDPipelineResult`

## Privacy and Safety

* No remote/network calls are required for this track.
* Diagnostics are hash-only and numeric; no raw patches/chunks are emitted.
* Validation blocks risky primitives (`eval/exec/os.system/subprocess`) by default.

## Local Dev Commands

```powershell
pip install -e ".[dev]"
ruff check .
pytest -q
```
