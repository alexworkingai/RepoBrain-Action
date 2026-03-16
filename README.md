# RepoBrain Action (MVP Skeleton)

Current release candidate: `0.5.0-rc.1`

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

Environment reference:

* See `docs/env_reference.md` (generated from `repobrain/config.py`).
* Changelog: `CHANGELOG.md`
* Migration guide: `MIGRATION.md`
* Post-merge validation: `docs/post_merge_validation.md`

GitHub Actions note:

* `issue_number`: use digits only; `#` prefix is also accepted (for example `1` or `#1`).
* Action uses `github.token` automatically; ensure workflow has `issues: write` permissions for posting comments.

UX notes:

* On `/repobrain ...` commands from users, the bot adds an `👀` reaction first (non-dry-run), then posts a reply comment.
* Bot comments (for example `github-actions[bot]`) are ignored to avoid loops.

PR Review:

* Use `/repobrain review` in a Pull Request discussion (issue comments on a PR).
* RepoBrain fetches changed files, builds a lightweight risk summary, and posts a markdown PR review comment.
* Review synthesis uses hierarchical payload shaping (PR metadata summary -> targeted evidence -> final synthesis) with automatic compaction/batch fallback for provider safety.
* Findings are normalized/deduplicated and split into semantic layers: `Confirmed findings`, `Risk drivers`, `Possible signals`, `Informational notes`; high-severity findings require explicit evidence.
* Confirmed findings include compact file evidence references when available (for example `file: path` / short `files: ...`) to improve trust and actionability.
* Low-risk reviews render cleanly with `Confirmed findings: none.` (no pseudo-findings) and natural risk-driver wording (no placeholder `n/a` blocks).
* `/repobrain review` is not available in regular Issues (non-PR threads).
* On closed or merged PRs, `/repobrain review` and `/repobrain fix` now return an explicit usersafe skip comment (no silent skip).
* `/repobrain fix <instruction>` can generate a patch proposal (`artifacts/patch.diff`) with usersafe diff snippet.
* `/repobrain fix` uses patch-specific semantics (`llm_intent=patch`, patch reason codes, patch diagnostics) and does not reuse review-only counters in user output.
* `/repobrain fix` narrows patch scope before LLM generation (localized evidence/query-matched files first) and prefers `NO_PATCH` over broad generic diffs when grounding is insufficient.
* `no_patch` is treated as a valid safe outcome when no sufficiently localized evidence-backed target exists.
* Patch targeting caps are configurable via `RB_LLM_PATCH_MAX_TARGET_FILES`, `RB_LLM_PATCH_MAX_TARGET_HUNKS`, and `RB_LLM_PATCH_REQUIRE_LOCALIZED_EVIDENCE`.
* In PR context RepoBrain also publishes a GitHub Check Run (`RepoBrain Review` / `RepoBrain Fix`) with usersafe annotations.
* RepoBrain now publishes command-specific compact checks summaries:
  * `RepoBrain Ask`
  * `RepoBrain Review`
  * `RepoBrain Fix`
  These checks are short, usersafe, and complement comment UX (they do not duplicate full comment markdown).
* Expected neutral check outcomes include safe governed paths such as `fix=no_patch` and `review/fix` on closed/merged PR.

Index cache / prebuild:

* `artifacts/index-package.zip` is reused when present; RepoBrain skips rebuild for `help` and `review`.
* Index build also writes `artifacts/repobrain-index-<commit>.zip` with stable entries: `manifest.json`, `topo_map.json`, `index/chunks.jsonl`.
* GitHub Actions can prebuild/cache the index via `.github/workflows/repobrain_index_cache.yml`.
* The issue-comment workflow restores the Actions cache before running the local action.
* Full artifact contract is documented in `docs/artifacts.md`.

Usersafe Ask output:

* Ask/Explain/Locate comments use route-aware templates (`Answer`, `Needs verification`, `Refused`, `Blocked`).
* Comments include only file locators and usersafe diagnostics (no raw source snippets, no env/token dumps).
* Diagnostics are grouped for readability (Decision, Runtime/Policy, LLM, Embeddings, Retrieval, Verification, Provider/Quota) with full detail preserved in artifacts.
* In PR context, changed-files metadata is authoritative grounding and appears before retrieval-only evidence when relevant.
* If rendered output is too large, RepoBrain truncates the comment and writes full markdown to `artifacts/ask_result.md`.

Retrieval quality / privacy:

* Index stores hashed token signatures (no raw text by default) to improve retrieval quality safely.
* Retrieval Pro uses a hybrid score (signature overlap + path overlap + exact identifier hits) and file diversity caps.
* Optional embeddings retrieval can be enabled with `RB_EMBED_ENABLED=1` (GitHub Models, default model `openai/text-embedding-3-small`).
* Index embeds chunks in batches and caches vectors by chunk hash in `artifacts/.repobrain_cache/embeddings.sqlite`.
* Index package stores vectors in `index/embeddings.jsonl` (metadata + vectors), while raw chunk text remains disabled by default.
* Runtime hybrid ranking blends lexical and vector scores:
  * `RB_RETRIEVAL_W_LEX` (default `0.55`)
  * `RB_RETRIEVAL_W_VEC` (default `0.45`)
  * `RB_RETRIEVAL_VECTOR_TOPK` (default `30`)
* Signatures are built from chunk metadata and can be compared without storing source text.
* Unicode-friendly tokenization improves RU/EN queries.
* Retrieval uses Jaccard over hashed signatures plus small path-based boosts.
* If TKY returns `route=DEEP`, RepoBrain performs a second retrieval pass with a larger `topK`.
* Raw chunk text is still omitted by default (`store_text=False`).

Security:

* RepoBrain does not index common secret files, large files, or binary files.
* Security orchestration is calibrated into:
  * protected-zone hard guard (`TKYA` internals, hidden prompts, protected files/secrets) -> hard block/refuse
  * general repo-analysis guard (ask/review/fix over repo/PR metadata) -> allowed unless explicit exfiltration intent is detected
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
* Active documented backend path is v5; `lite` stays as safe fallback.
* `RB_TKYA_BACKEND=original` is retained for internal legacy-compatibility only and is not part of the recommended production setup.
* Remote/network path is disabled by default for local vendor backends: `RB_TKYA_ALLOW_REMOTE=0`.
* Strict startup flags:
  * `RB_TKYA_STRICT_V5=1` for v5
  * `RB_TKYA_STRICT_ORIGINAL=1` for legacy original
* `RB_TKYA_V5_PATH` and `RB_TKYA_ORIGINAL_PATH` can override vendor file paths when needed.
* Optional canary rollout for v5 backend:
  * `RB_TKYA_V5_CANARY_PERCENT=0..100`
  * `RB_TKYA_CANARY_KEY=<stable-bucket-key>`
* v5 trace is hash-only and versioned (`trace_schema_version=1.1`, policy `1.x`).
* Detailed permanent architecture doc: `docs/topocore_v5_architecture.md`.

Canary workflow:

* `.github/workflows/canary_v5.yml` provides `workflow_dispatch` canary for v5 wiring.
* It runs v5-specific checks only when vendor file is present; otherwise runs fallback smoke checks.

R&D track (R&D-1..R&D-9, local-safe):

* `repobrain/rd_codegen.py`: deterministic template-first codegen.
* `repobrain/rd_validation.py`: static policy validation gates.
* `repobrain/rd_crypto.py`: HMAC signing helpers (no secrets in repo).
* `repobrain/rd_blockchain.py`: in-memory attestation chain adapter.
* `repobrain/rd_rollout.py`: canary helpers for controlled enablement.
* `repobrain/rd_orchestration.py`: `generate -> validate -> sign -> attest` pipeline.
* TopoCore v5 integration is opt-in: set `RB_TKYA_ENABLE_RD_PIPELINE=1`.
* Optional signing/attestation flags:
  * `RB_TKYA_RD_SIGNING_SECRET=<secret>` (not stored in repo)
  * `RB_TKYA_RD_ENABLE_CHAIN=1`
* Audit now includes hash-only `rd` diagnostics (`rd_status`, signature/attestation flags, counters).

Local CLI behavior:

* `scripts/run_ask.py --tky-mode auto|remote` falls back to baseline when remote is down if `tky.remote_fail_open: true`.
* If `tky.remote_fail_open: false`, local CLI exits with non-zero and prints a short actionable error (no stacktrace dump).

Verification runner safety:

* Real verification checks write `artifacts/verification_report.json`.
* `ruff` can run as static verification when available.
* `pytest` is dynamic verification and runs only when both are true:
  * `RB_TRUSTED_CONTEXT=1`
  * `RB_ALLOW_DYNAMIC_VERIFY=1`
* In untrusted context (default for `issue_comment`), dynamic checks are marked `NOT_RUN`.
* Quality gate env flags:
  * `RB_REQUIRE_VERIFY_FOR_PATCH=0|1`
  * `RB_FAIL_ON_NOT_RUN=0|1`
* Auto PR after patch push is opt-in:
  * `RB_CREATE_PR=1` (requires `RB_APPLY_PATCH=1` and `RB_TRUSTED_CONTEXT=1`).

GitHub Models LLM (optional):

* Enable only when needed:
  * workflow permission: `models: read`
  * env: `RB_LLM_ENABLED=1`, `RB_LLM_PROVIDER=github_models`
* RepoBrain uses GitHub Models endpoint with `GITHUB_TOKEN`:
  * `https://models.github.ai/inference/chat/completions`
* Model selection is deterministic:
  * review/fix/patch and complex DEEP synthesis -> `openai/gpt-4.1` (high tier)
  * simple tasks -> `openai/gpt-4.1-mini` (low tier)
  * governor can downgrade to mini when remaining budget is low (reported explicitly)
  * complex ask/explain (`retrieval_plus_llm`) can retain preferred `gpt-4.1` when quota is comfortably above ask downgrade threshold (`RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_ASK`) and `RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK=1`
  * review can retain preferred `gpt-4.1` when quota remains above review threshold (`RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW`) and payload stays compact after shaping
  * diagnostics keep model/budget reporting consistent: when preferred model is retained, downgrade-only budget actions are normalized to a neutral retained message
* Strict gating (safe default):
  * LLM is never called for routes `WAIT`/`REFUSE`/`BLOCK`
  * `locate` skips LLM by default; opt-in via `RB_LLM_ALLOW_LOCATE=1`
* Semantic coupling:
  * TKYA sets `execution_mode` (`retrieval_only|retrieval_plus_llm|verification_first|refuse`) and short reason fields.
  * Reports always show `TKYA LLM decision` + `Reason`; when runtime blocks desired LLM usage, report adds `Runtime override`.
* Main `issue_comment` policy (governed):
  * LLM can run on real `issue_comment` path only when semantic mode is `retrieval_plus_llm` and runtime policy allows it.
  * Policy flags:
    * `RB_LLM_ENABLE_ISSUE_COMMENT=1`
    * `RB_LLM_ENABLE_PR_COMMENTS=1`
    * `RB_LLM_ENABLE_ISSUE_ONLY=0` (conservative default for non-PR issues)
  * Manual verification target after merge:
    * In PR discussion run `/repobrain ask what files changed in this PR?`
    * Expect `TKYA LLM decision: used`, non-empty `Reason`, no `Runtime override` disabled message, and visible model/tokens.
* Reports include LLM diagnostics:
  * preferred model, final synthesis model, per-model call distribution, model selection reason, downgrade reason
  * clear distinction between intermediate downgrade (auxiliary calls) and final synthesis model retention
  * token usage (`prompt/completion/total`, reported or estimated)
  * remaining requests / reset time (from `x-ratelimit-*` headers when available)
  * if headers are missing, remaining is shown as `(estimated)`
* Output budget env controls:
  * `RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL` (default `2000`)
  * `RB_LLM_MAX_OUTPUT_TOKENS_ASK` (default `1000`)
  * `RB_LLM_MAX_OUTPUT_TOKENS_REVIEW` (default `1400`)
  * `RB_LLM_MAX_OUTPUT_TOKENS_FIX` (default `2000`)
* Review synthesis input caps:
  * `RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL` (default `3600`)
  * `RB_LLM_MAX_FILES_REVIEW_CONTEXT` (default `40`)
  * `RB_LLM_MAX_FINDINGS_CONTEXT` (default `24`)
  * `RB_LLM_MAX_HUNKS_REVIEW_CONTEXT` (default `24`)

Batch LLM for large PRs (optional):

* Enable map-reduce mode for `review`/`fix`:
  * `RB_LLM_BATCH_ENABLE=1`
* Batch controls:
  * `RB_LLM_BATCH_MAX_CALLS_PER_RUN` (default `6`)
  * `RB_LLM_BATCH_REDUCE_ENABLE` (default `1`)
  * `RB_LLM_BATCH_REDUCE_MODEL` (optional override)
* Planner is deterministic and budgeted (file/hunk-first, token reserve).
* For `fix`, per-batch patch parts are merged into `artifacts/patch.diff`.
* If patch parts conflict on overlapping ranges, RepoBrain keeps partial artifacts and returns a safe WAIT-style outcome.

Embeddings usage artifact:

* When embeddings are enabled, RepoBrain writes `artifacts/embeddings_usage.json` with usersafe metrics only:
  * model, calls/tokens totals, remaining/reset, chunks embedded, query embedded.

AI Budget Governor:

* RepoBrain uses a unified budget governor for LLM + embeddings calls.
* Governor is conservative by default and can only throttle/disable calls (it never auto-enables AI).
* It can:
  * deny calls when remaining/buffer is too low
  * downgrade model to `gpt-4.1-mini`
  * disable batch reduce when quota is low
  * stop embeddings early and continue with lexical fallback
* Main env knobs:
  * `RB_AI_STOP_AT_REMAINING` (default `1`)
  * `RB_AI_MIN_REMAINING_BUFFER` (default `2`)
  * `RB_AI_MAX_LLM_CALLS_PER_RUN` (default `6`)
  * `RB_AI_MAX_EMBED_CALLS_PER_RUN` (default `10`)
  * `RB_AI_DISABLE_REDUCE_WHEN_REMAINING_LT` (default `3`)
  * `RB_AI_SWITCH_TO_MINI_WHEN_REMAINING_LT` (default `5`)
  * `RB_AI_DISABLE_EMBED_WHEN_REMAINING_LT` (default `3`)
  * `RB_AI_MAX_TOKENS_PER_RUN_LLM` (default `12000`)
  * `RB_AI_MAX_TOKENS_PER_RUN_EMBED` (default `200000`)
  * `RB_AI_ESTIMATE_MODE_CONSERVATIVE` (default `1`)
  * `RB_AI_TIME_BUDGET_S` (default `240`)
* Each run writes `artifacts/config_snapshot.json` (usersafe effective config + validation warnings).

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
* Review findings are split into:
  * confirmed findings (evidence-backed)
  * possible signals (heuristic indicators downgraded when evidence is weak)
* Fix patch output is validated before publication (`valid_patch|no_patch|patch_validation_failed|provider_failed`); placeholder or unrelated patches are suppressed.
* Patch text is analyzed at runtime only and is not stored in audit artifacts.

2-minute setup:

1. Copy `docs/repobrain_template.yml` into your repository workflow (for example `.github/workflows/repobrain.yml`) with:
   * `issue_comment` + `workflow_dispatch`
   * permissions: `contents`, `issues`, `pull-requests`, `checks`, `statuses`
2. Trigger in PR/Issue comments with:
   * `/repobrain help`
3. Find audit output in workflow artifacts:
   * artifact name: `repobrain-audit` (hash-only JSON)

Enable features:

* Configure RB_* flags via `docs/env_reference.md`.
* Start with safe defaults, then enable LLM/embeddings/patch features incrementally.

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
* Release mechanics/checklists:
  * `docs/release_final_checklist.md`
  * `docs/release_merge_plan.md`
