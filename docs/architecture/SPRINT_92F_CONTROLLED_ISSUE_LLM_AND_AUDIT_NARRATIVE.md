# Sprint 92F Controlled Issue LLM And Audit Narrative

## Purpose

Sprint 92F adds controlled trusted issue LLM support for ask/explain, optional audit narrative layers, and the last compact-output cleanup items before broader selected-partner onboarding.

## Current Branch Status

- current public readiness decision on this Sprint 92F branch: `SPRINT_92F_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`
- RepoBrain-Action remains public
- TopoCore remains private
- Elen-MCP remains the private consumer repository for live retest

## Controlled Issue LLM

- default issue policy: `RB_REPOBRAIN_ENABLE_ISSUE_LLM=1`
- explicit disable: `RB_REPOBRAIN_ENABLE_ISSUE_LLM=0`
- scope:
  - trusted issue `/repobrain ask --profile balanced|premium`
  - trusted issue `/repobrain explain --profile balanced|premium`
  - trusted issue audit narrative modes
- non-bypass rule:
  - user text such as "use LLM" does not bypass repository policy

## Quota And Fallback Truth

- quota exhaustion must not fail the command
- deterministic fallback remains valid
- LLM block must say whether the call was:
  - used
  - not called
  - attempted but not completed
- exhausted state must be visible without exposing raw provider error details

## Audit Narrative Modes

- `/repobrain audit --narrative`
- `/repobrain audit --executive`
- `/repobrain audit --profile premium`

Rules:

- TopoCore remains score authority
- narrative LLM is explanation-only
- score modified by LLM: `no`
- `/repobrain score` remains compact and TopoCore-first

## Compact Output Cleanup

- review default omits detailed verification counters
- fix default omits patch validation, patch artifact, apply status, and detailed verification counters
- verbose/artifact paths keep deeper diagnostics

## Expected Post-Retest Status

- target post-evidence status: `SELECTED_PARTNER_PILOT_READY_AFTER_CONTROLLED_ISSUE_LLM_AND_AUDIT_NARRATIVE`

## Non-Goals

- no TopoCore source exposure
- no `.topocore-v6` user-facing leakage
- no v5
- no repobrain-community
- no patch/autofix
- no RepoBrain-created branch/commit/PR behavior
