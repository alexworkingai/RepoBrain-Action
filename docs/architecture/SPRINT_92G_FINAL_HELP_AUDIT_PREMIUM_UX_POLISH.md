# Sprint 92G Final Help Audit Premium UX Polish

## Purpose

Sprint 92G finishes the remaining partner-facing UX and semantics issues after the Sprint 92F live retest.

It does not change TopoCore score authority, does not expose private runtime source, and does not enable patch/autofix.

## Current Branch Status

- current public readiness decision on this Sprint 92G branch: `SPRINT_92G_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`
- RepoBrain-Action remains public
- TopoCore remains private
- Elen-MCP remains the private consumer repository for final live retest

## Help Structure

- `/repobrain help` is restructured into four blocks:
  - command list
  - command reference
  - environment / policy
  - safety notes
- every supported command now has its own reference block
- every supported extension now explains how it changes the base command

## Audit Premium Semantics

- `/repobrain audit --profile premium` now implies a premium narrative/explanation layer by itself
- TopoCore scoring still runs first
- score authority remains `TopoCore contract`
- premium narrative remains explanation-only
- `/repobrain score` remains compact and TopoCore-only

## PR Narrative De-Duplication

- PR audit narrative/executive modes now split overall interpretation from PR-specific impact
- duplicate narrative paragraphs are avoided
- PR impact stays focused on changed-file impact, runtime/security implications, validation needs, and partner-pilot effect

## Final Compact Output Polish

- review default no longer renders a minimal diagnostics shell
- fix default no longer renders a minimal diagnostics shell
- PR ask default hides evidence/verification counters while keeping compact evidence, LLM, runtime, and safety truth
- verbose mode still preserves sanitized details and deeper diagnostics

## Explain Relevance Polish

- RepoBrain-connection explain queries now use the same workflow-focused rerank pattern as locate
- unrelated deployment workflow padding is filtered for RepoBrain connection questions
- default explain wording keeps partner-facing runtime language and avoids raw private runtime mode terms where feasible

## Expected Post-Retest Status

- target post-evidence status: `SELECTED_PARTNER_PILOT_READY_AFTER_FINAL_HELP_AUDIT_PREMIUM_AND_UX_POLISH`

## Non-Goals

- no TopoCore source exposure
- no `.topocore-v6` user-facing leakage
- no v5
- no repobrain-community
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
