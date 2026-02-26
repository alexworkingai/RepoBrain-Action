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
* Signatures are built from chunk metadata and can be compared without storing source text.
* Unicode-friendly tokenization improves RU/EN queries.
* Retrieval uses Jaccard over hashed signatures plus small path-based boosts.
* If TKY returns `route=DEEP`, RepoBrain performs a second retrieval pass with a larger `topK`.
* Raw chunk text is still omitted by default (`store_text=False`).

Security:

* RepoBrain does not index common secret files, large files, or binary files.
* Prompt-injection / exfiltration-like requests are blocked with a safe refusal response.
* Trace data is hash/signature-based; raw text is not stored by default.

Remote TKY mode:

* Endpoint contract: `POST /v1/tky/decide` (JSON payload contract `v1`).
* Privacy mode is `signatures_only`: outbound payload includes query text + query signature + candidate metadata/signatures (no raw code snippets).
* Configure action inputs for remote mode: `tky_mode=remote`, `remote_url`, `api_key` (optional), `enable_hmac=true|false`, `hmac_secret` (optional).
* HMAC signing adds `x-ts`, `x-nonce`, `x-signature` headers over the exact JSON body.
* If remote TKY fails (network/HTTP), RepoBrain falls back to baseline selection and records fallback diagnostics in audit summary.

2-minute setup:

1. Add a workflow (see `.github/workflows/repobrain_template.yml`) with:
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
