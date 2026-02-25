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
