# TKYA Contract Baseline (RepoBrain-Action)

## Scope
This document captures the **actual runtime contract** between RepoBrain and the TKYA engine/providers as implemented in the current codebase.

## Where TKYLite/TopoCoreLite Is Used
- Provider factory:
  - `repobrain/ask.py` (`make_provider`) returns `LocalTKYProvider` for `mode=local`.
- Local provider execution:
  - `repobrain/tky_local.py` calls `get_engine()` from `repobrain/tkya/engine.py`.
  - Default backend is `v5` when vendor file exists, otherwise `lite` (`TopoCoreLite` fallback).
  - Advanced backend is `v5` (`RB_TKYA_BACKEND=v5`), loaded from vendor file.
  - Legacy vendor backend remains available via `RB_TKYA_BACKEND=original`.
- Engine direct usage points:
  - `repobrain/tky_local.py` -> `engine.decide(req)`.
  - `repobrain/tky_stub_server.py` -> `get_engine().decide(req)` for stub response generation.
- Legacy/direct `TopoCoreLite` usage remains in tests and engine fallback internals:
  - `repobrain/topocore_lite.py`
  - `repobrain/tkya/engine.py`
  - `tests/test_topocore_lite_*.py`, `tests/test_tkya_engine.py`

## Index / Ask / issue_comment Flow Locations

### Index mode
- CLI entrypoint: `scripts/run_index.py`
- Index builder: `repobrain/index_store.py::build_index`
- Output file (current implementation):
  - `artifacts/index-package.zip`
- Build/load in GitHub flow:
  - `repobrain/github_flow.py::load_or_build_chunks_with_meta`

### Ask mode
- Local CLI entrypoint: `scripts/run_ask.py`
- GitHub flow orchestration:
  - `repobrain/github_flow.py::run_github_flow`
  - Ask/locate/explain path: `_build_qa_markdown` -> `run_qa_two_pass`
  - TKY decision call path: `_answer_with_remote_fallback` -> `answer_question` -> `provider.compress_context`

### issue_comment handling (`/repobrain ask`)
- Workflow trigger:
  - `.github/workflows/repobrain.yml` (`on.issue_comment.types: [created]`)
- Command parsing:
  - `repobrain/commands.py::parse_command`
- Runtime command handling:
  - `repobrain/github_flow.py::run_github_flow`
  - Ignores non-`/repobrain` and bot comments
  - Handles `help|ask|locate|explain|review|verify`

## Index Artifact vs Expected Names
- **Found in code:** `artifacts/index-package.zip`
  - created by `scripts/run_index.py`
  - loaded/reused in `scripts/run_ask.py` and `repobrain/github_flow.py`
- **Found in code:** `artifacts/repobrain-index-<commit>.zip` (commit-tagged copy)
- **Found in code:** zip entries `manifest.json` + `topo_map.json` + `index/chunks.jsonl`
- Artifact contract reference: `docs/artifacts.md`

## TKYA Engine Contract (Expected by RepoBrain)

### Provider-level contract
Defined in `repobrain/tky_provider.py`:
- Protocol method:
  - `compress_context(*, question: str, candidates: list[CandidateChunk], limits: dict[str, Any]) -> TKYResult`

#### Input model: `CandidateChunk`
- `chunk_id: str`
- `file_path: str`
- `line_start: int`
- `line_end: int`
- `score: float`
- `text: str | None = None`
- `signature: list[int] | None = None`

#### Output model: `TKYResult`
- `selected_chunk_ids: list[str]`
- `route: str` (supported set: `FAST`, `DEEP`, `WAIT`, `REFUSE`, `BLOCK`, `REVIEW`)
- `compression_stats: dict[str, Any]`
- `rationale: str`

### Engine-level contract (local TKYA engine)
Defined in `repobrain/tky_engine.py` and used by `repobrain/tky_local.py`:
- Engine method:
  - `decide(req: EngineRequest) -> EngineDecision`

#### Engine input model: `EngineRequest`
- `task_type: Literal["ask","locate","explain","review"]`
- `query: EngineQuery` (`text`, `signature`)
- `candidates: list[EngineCandidate]` (`chunk_id`, `score_local`, optional signature/path/lines)
- `limits: dict[str, Any]`
- `policy: dict[str, Any]`

Policy keys used by TopoCore v5 wiring:
- `corelocked: bool`
- `github_context: dict` (event/repo/sha/ref/issue/pr/base/head/changed_files/diff_hunks when available)
- `verification_context: dict` (capability summary: pytest/ruff/time budget/mode/patch/network)
- `runtime: dict` (safe runtime metadata, no secrets)

#### Engine output model: `EngineDecision`
- `route: str`
- `selected_chunk_ids: list[str]`
- `compression_stats: dict[str, Any]`
- `security: EngineSecurity`
- `rationale: str`
- `stable_tokens: list[str]`

Route compatibility contract:

- `FAST` -> single-pass retrieval is sufficient
- `DEEP` -> caller should run second-pass retrieval with larger candidate budget
- `WAIT` -> caller should return pending/verification-needed response
- `REFUSE` -> caller should safely refuse request
- `BLOCK` -> caller should block request by policy
- `REVIEW` -> caller should use review-style rendering and checks summary

## Expected Exceptions / Error Handling

### Remote TKY
- `repobrain/tky_remote.py` raises `RemoteTKYError` with:
  - `status_code`
  - `error_class`
  - `fallback_reason_code`
  - `diagnostics` (`latency_ms`, `retry_count`, etc.)

### Fallback behavior
- In GitHub flow (`repobrain/github_flow.py::_answer_with_remote_fallback`):
  - If `tky_mode_requested == "remote"` and remote fails:
    - fail-open (`tky_remote_fail_open=True`) => fallback to baseline provider
    - fail-open disabled => returns REFUSE-style response
- In local CLI (`scripts/run_ask.py`):
  - remote failure + fail-open true => fallback baseline
  - remote failure + fail-open false => exit code `2` with short message

### Original TKYA backend loading
- `repobrain/tkya/engine.py::get_engine`
  - default: `lite`
  - `RB_TKYA_BACKEND=v5` loads `TopoCore_TCX_v5-Advance_CAS+Git.py` with `importlib`
  - `RB_TKYA_BACKEND=original` loads legacy `TopoCore_TCX_v2-CAS.py` with `importlib`
  - missing/broken vendor file:
    - fallback to lite by default
    - strict fail when `RB_TKYA_STRICT_V5=1` for v5
    - strict fail when `RB_TKYA_STRICT_ORIGINAL=1` for original

## Files/Artifacts Expected by Index and Ask

### Index step
- Input: repository root files scanned/chunked
- Output:
  - `artifacts/index-package.zip`
  - `artifacts/repobrain-index-<commit>.zip`
  - contains:
    - `manifest.json`
    - `topo_map.json`
    - `index/chunks.jsonl`
    - `chunks.jsonl` (legacy compatibility)

### Ask step
- Requires:
  - existing `artifacts/index-package.zip`, or
  - auto-build through `load_or_build_chunks_with_meta`
- Ask reads chunks, retrieves top-k, calls TKY provider, emits usersafe markdown:
  - route-aware headers (`Answer/Needs verification/Refused/Blocked`)
  - file locators only (no raw code snippets)
  - verification summary (`PASS/WARN/NOT_RUN`)
  - deep-pass marker for 2-pass retrieval
- If rendered markdown is oversized, output is truncated for comment safety and full body is written to `artifacts/ask_result.md`.

## Existing Env/Config Knobs

### Core runtime env
- `GITHUB_REPOSITORY`, `GITHUB_SHA`, `GITHUB_REF_NAME`, `GITHUB_REF`, `GITHUB_EVENT_PATH`
- `GITHUB_TOKEN` (post mode only)
- `RB_DISABLE_INTERNAL_REACTIONS`
- `RB_INDEX_CACHE_RESTORED`

### TKYA backend env
- `RB_TKYA_BACKEND=lite|v2|v5|original`
  - `v2` is alias for `original`
  - default behavior: if backend is not explicitly set and v5 vendor file exists, loader prefers `v5`; otherwise `lite`
- `RB_TKYA_ALLOW_REMOTE=0|1` (default guarded as disabled)
- `RB_TKYA_STRICT=0|1` (common strict mode for vendor initialization)
- `RB_TKYA_STRICT_V5=0|1`
- `RB_TKYA_V5_PATH` (optional override path)
- `RB_TKYA_V5_CANARY_PERCENT=0..100` (optional canary rollout gate for `v5`)
- `RB_TKYA_CANARY_KEY` (optional stable canary bucket key)
- `RB_TKYA_ENABLE_V2_SHIM=0|1` (optional compatibility shim for selected v2 adapters)
- `RB_TKYA_V2_SHIM_PATH` (optional override path for v2 shim source)
- `RB_TKYA_V2_SHIM_STRICT=0|1` (optional strict init for v2 shim)
- `RB_TKYA_STRICT_ORIGINAL=0|1`
- `RB_TKYA_ORIGINAL_PATH` (optional override path)

### Remote TKY inputs/env
- CLI/action inputs used by `scripts/run_github.py` and `scripts/run_ask.py`:
  - `--tky-mode auto|baseline|remote|local`
  - `--remote-url`
  - `--api-key`
  - `--hmac-secret`
  - `--enable-hmac`
- `.repobrain.yml` parsed by `repobrain/config.py`:
  - `tky.remote_enabled`
  - `tky.remote_url`
  - `tky.remote_allow_commands`
  - `tky.remote_allow_branches`
  - `tky.remote_allow_repos`
  - `tky.remote_fail_open`

## Dependencies and Quality Configuration
- Build/deps/lint/test config is in `pyproject.toml`:
  - Runtime deps: `PyYAML`, `requests`, `orjson`
  - Dev deps: `pytest`, `ruff`
  - Ruff config: `[tool.ruff]`
  - Pytest config: `[tool.pytest.ini_options]`
- `requirements*.txt` not used in current repo root.

## Local Dev Commands
From current `pyproject.toml` (pip editable install):

```powershell
python -m pip install -U pip
pip install -e ".[dev]"
ruff check .
pytest -q
```
