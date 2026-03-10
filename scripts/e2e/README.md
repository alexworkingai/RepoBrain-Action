# Local E2E Harness (`scripts/e2e/run_e2e_suite.py`)

This harness runs end-to-end RepoBrain scenarios against the current repository using `gh`.

## Prerequisites

- GitHub CLI installed (`gh --version`)
- Authenticated session (`gh auth status`)
- Permission to push branches and create PRs in this repository
- Optional for scenario 4: GitHub Models access (`models: read`) for LLM/embeddings test path

## Scenarios

- PR comment: `/repobrain review`
- PR comment: `/repobrain fix improve naming in marker file`
- PR comment: `/repobrain ask what files changed in this PR?`
- `workflow_dispatch` with toggles:
  - `enable_llm=true`
  - `enable_embeddings=true`
  - `trusted_context=true`
  - other toggles safe/minimal

## Run

```powershell
python scripts/e2e/run_e2e_suite.py
```

With cleanup (close PR + remove temp branch):

```powershell
python scripts/e2e/run_e2e_suite.py --cleanup
```

Artifacts and summary report are written to:

- `artifacts/e2e/...`
- `artifacts/e2e/e2e_report.md`

