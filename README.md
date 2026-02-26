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
* Raw chunk text is still omitted by default (`store_text=False`).
