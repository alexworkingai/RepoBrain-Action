# Hotfix Private Checkout Evidence LLM Diagnostics

## 1. Purpose

Sprint 92A hotfixes partner-facing issue-comment defects found after the Sprint 91 public switch.

It does not change runtime policy.
It does not expose TopoCore source.
It does not enable patching or repository mutation.

## 2. Manual Smoke Findings

Manual MCP issue smoke confirmed three blocking partner-facing defects:

- private checkout evidence leaked into user-facing output as `.topocore-v6/...`
- `/repobrain locate` rendered a misleading route label
- issue-mode `/repobrain ask` and `/repobrain explain` could show contradictory LLM diagnostics when policy blocked the LLM path

Secondary cleanup goals were also included:

- remove the deprecated lite alias from the public command surface
- reduce default issue-comment diagnostics noise

## 3. Private Checkout Evidence Leak Fix

Hotfix behavior:

- private checkout paths are filtered before user-facing evidence selection where possible
- unsafe paths are dropped from rendered evidence lists rather than shown as redacted top evidence
- user-facing answer, locate, explain, audit, and score rendering now preserves safe repo-relative evidence only

Forbidden user-facing path patterns include:

- `.topocore-v6`
- private checkout subpaths
- local machine paths
- token-like values

## 4. Deprecated Unsupported Command Removal

`fix-lite` is no longer part of the public command surface.

Current supported commands are:

- `help`
- `ask`
- `locate`
- `explain`
- `review`
- `verify`
- `fix`
- `audit`
- `score`
- `doctor`
- `status`

If a user types the removed lite alias, RepoBrain now returns the generic unsupported-command response without special branding.

## 5. LLM Issue-Mode Behavior Explanation

Current truth:

- issue-mode ask or explain can still answer without an LLM call
- RepoBrain can synthesize a safe response from deterministic retrieval, routing, evidence extraction, workflow inspection, and TopoCore v6 signals
- the LLM is an optional synthesis layer, not the only execution path

Hotfix behavior:

- if policy blocks the LLM path, diagnostics no longer claim that the LLM was used
- visible execution mode now falls back to `retrieval_only` when no LLM call actually happened
- the output explains that the answer came from a deterministic retrieval or template path

## 6. Locate Route Fix

`/repobrain locate` now renders:

- `Route: LOCATE`

This is a presentation correction only.
It does not change the underlying no-mutation behavior.

## 7. Explain Fallback Fix

When LLM usage is blocked in issue mode, `/repobrain explain` now produces explanatory prose instead of a locate-style file list.

Expected deterministic explanation content includes:

- workflow path
- action source
- requested and effective runtime mode
- installed-package proof state
- public-readiness state
- no-mutation safety

## 8. Diagnostics Compaction

Default partner-facing issue output is now compact by default.

- `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=0`:
  - concise answer
  - compact evidence
  - compact runtime and safety summary
  - audit anchors
- `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=1`:
  - expanded runtime diagnostics
  - secondary diagnostics

This preserves trust without overloading issue comments with low-value counters and `n/a` fields.

## 9. Live MCP Retest

Live MCP retest completed after the hotfix was merged to `main`.

Safe issue:

- `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/40`

Completed issue-command smoke:

- help: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26761867497`
- doctor: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26761912206`
- status: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26761961307`
- ask operational status: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762001625`
- locate: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762049849`
- explain: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762105439`
- ask partner-pilot risks: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762147420`
- audit: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762183999`
- score: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762234301`
- deprecated lite alias regression: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26762276927`

Observed result:

- no `.topocore-v6` or private checkout evidence appeared in user-facing output
- help, doctor, and status no longer advertised the deprecated lite alias
- operational ask reported deterministic retrieval truth when the issue-only LLM policy blocked a live LLM call
- locate rendered `Route: LOCATE`
- explain rendered `Route: EXPLAIN` and produced a real workflow/runtime explanation
- audit and score stayed `v6-enriched scoring` with backend `auto -> v6`
- the deprecated lite alias returned the generic unsupported-command response without special branding

## 10. Product Status

Current hotfix result:

- `PARTNER_PILOT_READY_AFTER_MANUAL_SMOKE_HOTFIX`

Blocked states remain:

- `BLOCKED_BY_PRIVATE_EVIDENCE_SANITIZER`
- `BLOCKED_BY_LLM_DIAGNOSTICS`
- `BLOCKED_BY_COMMAND_SURFACE_DRIFT`
- `BLOCKED_BY_LOCATE_EXPLAIN_UX`
- `BLOCKED_BY_LIVE_MCP_RETEST`
- `BLOCKED_BY_VALIDATION`

## 11. Non-Goals

- no TopoCore source exposure
- no TopoCore public visibility change
- no v5 return
- no `repobrain-community` return
- no patch or autofix
- no repository mutation
- no Marketplace work
