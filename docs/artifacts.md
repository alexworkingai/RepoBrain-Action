# RepoBrain Artifacts & Usersafe Output

## Index Zip Contract

RepoBrain index packages are generated as:

- `artifacts/index-package.zip` (runtime default)
- `artifacts/repobrain-index-<commit>.zip` (explicit commit-tagged copy)

Required entries **inside** the zip:

- `manifest.json`
- `topo_map.json`
- `index/chunks.jsonl`

Backward-compatibility entry is also kept:

- `chunks.jsonl` (legacy loader path)

`manifest.json` fields:

- `format_version`
- `commit_sha`
- `created_at`
- `files_indexed`
- `chunks`
- `embeddings`
- `topo`
- `exclusions`
- `tool_versions`

`topo_map.json` is usersafe and metadata-only (graph counts, metrics, file-level chunk counts).  
No raw source code is embedded by default (`store_text=false`).

## Usersafe Ask Output Rules

QA markdown responses must remain usersafe:

- no env dumps
- no runner-local paths
- no tokens/secrets
- no raw code snippets in comments

Template behavior:

- route-aware headers:
  - `✅ Answer`
  - `⏳ Needs verification`
  - `🚫 Refused`
  - `🛑 Blocked`
- include `What I used` with file locators only (`path + line range`)
- include `Verification` summary (`PASS/WARN/NOT_RUN`)
- include `Route/Mode`, including deep-pass marker when pass-2 was used

Comment size protection:

- if rendered markdown exceeds ~60KB, comment is truncated safely
- full markdown is saved to `artifacts/ask_result.md`
- workflow should publish artifacts for deeper inspection

## Canary Workflow

Workflow: `.github/workflows/canary_v5.yml`

- trigger: `workflow_dispatch`
- env:
  - `RB_TKYA_BACKEND=v5`
  - `RB_TKYA_ALLOW_REMOTE=0`
  - `RB_TKYA_STRICT=0`
- behavior:
  - runs lint/tests for wiring safety
  - if v5 vendor file is present, executes full test suite
  - if v5 vendor file is absent, executes a fallback test subset and does not fail purely because vendor is missing
