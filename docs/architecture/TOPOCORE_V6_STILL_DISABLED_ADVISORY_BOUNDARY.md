# TopoCore v6 Still-Disabled Advisory Boundary

## 1. Purpose

Sprint 34 introduces a still-disabled advisory boundary skeleton.

Current truth:

- it is implementation-adjacent but not activation
- it is not live shadow mode
- it is not canary
- it does not change GitHub runtime behavior
- it does not call TopoCore v6
- it does not replace v5/TKYA

This sprint exists to add a narrow boundary around the existing shadow-path skeleton so future work can target a concrete integration seam without changing current RepoBrain behavior.

## 2. Relationship to Sprint 33

See:

- `docs/architecture/TOPOCORE_V6_PHASE_4_CHECKPOINT_RUNTIME_ADJACENT_APPROVAL.md`
- `docs/architecture/TOPOCORE_V6_DISABLED_ADVISORY_PATH_SKELETON.md`
- `docs/architecture/TOPOCORE_V6_ADVISORY_PATH_GUARD_TESTS.md`

Relationship summary:

- Sprint 33 approved one narrowly bounded, still-disabled, non-user-visible runtime-adjacent implementation step
- Sprint 34 implements only that approved boundary skeleton
- it does not activate any advisory experiment

## 3. Boundary Behavior

Current behavior:

- disabled by default
- explicit disabled flag also returns a no-op result
- enabled flag remains non-operational
- artifact flag cannot persist or publish artifacts
- fail-closed flag is recorded only
- the result remains safe, compact, and JSON-serializable

## 4. Boundary Inputs

Allowed safe inputs:

- `command`
- `task_type`
- `safe_query_summary`
- `candidate_ids`
- `v5_primary_snapshot`
- `summary_bundle`
- `validation_run_label`
- `request_id_safe`

Forbidden inputs:

- raw query, code, or diff
- prompts or system prompts
- secrets, tokens, API keys, or private keys
- `.env` contents
- compression stats
- traces
- governance, event, or artifact internals
- `decide_raw`

## 5. Boundary Outputs

Output rules:

- JSON-serializable safe result only
- no raw or internal data
- no user-visible output
- no PR comments/checks
- no artifact persistence

## 6. What This Enables

- future tests can target a concrete advisory boundary
- future implementation can remain isolated behind the boundary
- future Phase 5 checkpoint can decide whether to proceed or stop
- the project can verify no-op and kill-switch behavior before any activation

## 7. What This Does Not Enable

- no live v6 call
- no shadow activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no artifact publication
- no user-visible output change

## 8. Future Follow-Up

- Sprint 35 should add boundary guard tests and Phase 5 checkpoint
- Sprint 35 should decide whether any future controlled advisory experiment activation can even be proposed
- Sprint 35 must not itself become canary or route migration unless separately approved
