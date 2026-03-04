# RepoBrain Action (MVP Skeleton)

This repository contains a minimal, GitHub-Actions-friendly skeleton for:

* indexing a repo (placeholder),
* answering questions with evidence trail (placeholder),
* pluggable TKY provider modes: baseline / remote / local (local is a stub).

No secrets, keys, or proprietary TKY internals are included.

Quick start (PowerShell):

1. Create venv (VS Code UI) with Python 3.11
2. Install deps:
   pip install -e ".[dev]"
3. Run tests:
   pytest -q
4. Lint:
   ruff check .

GitHub Actions note:

* `issue_number`: use digits only; `#` prefix is also accepted (for example `1` or `#1`).
* Action uses `github.token` automatically; ensure workflow has `issues: write` permissions for posting comments.

UX notes:

* On `/repobrain ...` commands from users, the bot adds an `👀` reaction first (non-dry-run), then posts a reply comment.
* Bot comments (for example `github-actions[bot]`) are ignored to avoid loops.

PR Review:

* Use `/repobrain review` in a Pull Request discussion (issue comments on a PR).
* RepoBrain fetches changed files, builds a lightweight risk summary, and posts a markdown PR review comment.
* `/repobrain review` is not available in regular Issues (non-PR threads).

Index cache / prebuild:

* `artifacts/index-package.zip` is reused when present; RepoBrain skips rebuild for `help` and `review`.
* GitHub Actions can prebuild/cache the index via `.github/workflows/repobrain_index_cache.yml`.
* The issue-comment workflow restores the Actions cache before running the local action.

Retrieval quality / privacy:

* Index stores hashed token signatures (no raw text by default) to improve retrieval quality safely.
* Retrieval Pro uses a hybrid score (signature overlap + path overlap + exact identifier hits) and file diversity caps.
* Signatures are built from chunk metadata and can be compared without storing source text.
* Unicode-friendly tokenization improves RU/EN queries.
* Retrieval uses Jaccard over hashed signatures plus small path-based boosts.
* If TKY returns `route=DEEP`, RepoBrain performs a second retrieval pass with a larger `topK`.
* Raw chunk text is still omitted by default (`store_text=False`).

Security:

* RepoBrain does not index common secret files, large files, or binary files.
* Prompt-injection / exfiltration-like requests are blocked with a safe refusal response.
* Trace data is hash/signature-based; raw text is not stored by default.

Merge safety:

* CI blocks merge conflict markers automatically (`<<<<<<<`, `=======`, `>>>>>>>`).
* `.gitattributes` normalizes line endings to reduce Windows/Linux conflicts.
* `README.md` uses `merge=union`; this can duplicate lines, so review README diffs in PRs.

Remote TKY mode:

* Endpoint contract: `POST /v1/tky/decide` (JSON payload contract `v1`).
* Privacy mode is `signatures_only`: outbound payload includes query text + query signature + candidate metadata/signatures (no raw code snippets).
* `tky_mode=auto` is the default. In `auto`, RepoBrain uses remote only when rollout policy allows it and a remote URL is available.
* Configure action inputs for explicit remote mode: `tky_mode=remote`, `remote_url`, `api_key` (optional), `enable_hmac=true|false`, `hmac_secret` (optional).
* HMAC signing adds `x-ts`, `x-nonce`, `x-signature` headers over the exact JSON body.
* If remote TKY fails (network/HTTP), RepoBrain falls back to baseline selection and records fallback diagnostics in audit summary.
* Contract compatibility supports both response formats:
  * flat: `route` + `selected_chunk_ids`
  * nested: `decision.route` + `selection.selected_chunk_ids`

Remote TKY rollout controls:

* `tky.remote_enabled` toggles remote globally (default `false`).
* `tky.remote_url` is optional and can be used for local/stub setups; production should pass `remote_url` via workflow input/secrets.
* `tky.remote_allow_commands` limits where remote can run (default `ask`, `explain`).
* `tky.remote_allow_branches` limits branches (default `main`; empty list means any branch).
* `tky.remote_allow_repos` limits repositories (empty list means any repo).
* `tky.remote_fail_open`:
  * `true` (default): fallback to baseline on remote errors.
  * `false`: return REFUSE when remote is unavailable.

Reliability:

* Remote calls use separate connect/read timeouts (`5s/15s` by default).
* Retries with backoff are applied for timeout/network errors, HTTP `429`, and `5xx`.
* `Retry-After` is respected for `429` (capped wait).
* Diagnostics in audit: latency, retries, rate limit flag, error class, fallback reason code.

Remote modes:

* `issue_comment`/PR workflow (`.github/workflows/repobrain.yml`) runs with `tky_mode: auto` and intentionally does not set `remote_url`.
* Remote stub testing uses `.github/workflows/repobrain_remote_stub_test.yml` with `remote_url: http://127.0.0.1:8787/v1/tky/decide`.
* Production remote should pass `remote_url` (and credentials) via workflow inputs/secrets, not hardcoded in repo workflows.

Local TKYA backend options:

* Safe default remains `RB_TKYA_BACKEND=lite`.
* Advanced local core: set `RB_TKYA_BACKEND=v5` and use `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`.
* Legacy/proprietary backend remains optional via `RB_TKYA_BACKEND=original` with `repobrain/tkya/vendor/TopoCore_TCX_v2-CAS.py`.
* Remote/network path is disabled by default for local vendor backends: `RB_TKYA_ALLOW_REMOTE=0`.
* Strict startup flags:
  * `RB_TKYA_STRICT_V5=1` for v5
  * `RB_TKYA_STRICT_ORIGINAL=1` for legacy original
* `RB_TKYA_V5_PATH` and `RB_TKYA_ORIGINAL_PATH` can override vendor file paths when needed.
* Optional canary rollout for v5 backend:
  * `RB_TKYA_V5_CANARY_PERCENT=0..100`
  * `RB_TKYA_CANARY_KEY=<stable-bucket-key>`
* Optional v2 compatibility shim for targeted adapters:
  * `RB_TKYA_ENABLE_V2_SHIM=1`
  * `RB_TKYA_V2_SHIM_PATH=/path/to/TopoCore_TCX_v2-CAS.py`
  * `RB_TKYA_V2_SHIM_STRICT=1`
* v5 trace is hash-only and versioned (`trace_schema_version=1.1`, policy `1.x`).

Local CLI behavior:

* `scripts/run_ask.py --tky-mode auto|remote` falls back to baseline when remote is down if `tky.remote_fail_open: true`.
* If `tky.remote_fail_open: false`, local CLI exits with non-zero and prints a short actionable error (no stacktrace dump).

Example `.repobrain.yml`:

```yaml
tky:
  remote_enabled: false
  remote_url: ""
  remote_allow_commands: ["ask", "explain"]
  remote_allow_branches: ["main"]
  remote_allow_repos: []
  remote_fail_open: true
```

Example workflow/action inputs:

* `tky_mode: auto` (default)
* `remote_url: https://your-service.example/v1/tky/decide`
* `api_key: ${{ secrets.REPOBRAIN_TKY_API_KEY }}`
* `enable_hmac: "true"`
* `hmac_secret: ${{ secrets.REPOBRAIN_TKY_HMAC_SECRET }}`

PR Review Pro:

* Review output includes file links pinned to PR head SHA and risk-level scoring (low/medium/high).
* Patch-based heuristics detect conflict markers, TODO/FIXME, possible secret leakage, and workflow risk signals.
* Patch text is analyzed at runtime only and is not stored in audit artifacts.

2-minute setup:

1. Copy `docs/repobrain_template.yml` into your repository workflow (for example `.github/workflows/repobrain.yml`) with:
   * `issue_comment` + `workflow_dispatch`
   * permissions: `contents`, `issues`, `pull-requests`, `checks`, `statuses`
2. Trigger in PR/Issue comments with:
   * `/repobrain help`
3. Find audit output in workflow artifacts:
   * artifact name: `repobrain-audit` (hash-only JSON)

Demo scenarios:

1. `/repobrain ask Где реализована логика TKYProvider?`
2. `/repobrain locate TKYProvider`
3. `/repobrain review` (inside PR discussion)
4. `/repobrain verify` (PR checks/status verification)
5. Security-blocked request (e.g. asking for secrets/system prompt) -> safe refusal
6. Download `repobrain-audit` artifact to inspect timings, route, cache source, and TKY diagnostics

Release versioning:

* Tag a release:
  * `git tag v0.1.0`
  * `git push origin v0.1.0`
* Consumers can pin the action version:
  * `uses: OWNER/REPO@v0.1.0`
