# TopoCore v6 Manual Evidence Collection and Phase 7 Checkpoint

## 1. Purpose

Sprint 40 defines the manual evidence collection checklist and Phase 7 checkpoint.

Current truth:

- Sprint 40 is docs-only
- Sprint 40 does not implement dependency strategy
- Sprint 40 does not add or import TopoCore v6
- Sprint 40 does not activate advisory behavior
- Sprint 40 does not change runtime behavior
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- Phase 6 NO-GO remains in effect

This sprint exists to define the exact manual evidence bundle expected from local or private TopoCore v6 validation and to close Phase 7 as a stabilization baseline.

See also:

- `docs/architecture/TOPOCORE_V6_REAL_INTEGRATION_CONTRACT_LOCK.md`

## 2. Current Accepted Baseline

Current accepted baseline:

- latest accepted `main` before Sprint 40:
  - `47215d2 Docs: propose private TopoCore v6 dependency strategy`
- Phase 7 started with:
  - Sprint 38 - Documentation and Test Index Consolidation
  - Sprint 39 - Private TopoCore v6 Dependency Strategy Proposal
- Sprint 39 validation:
  - `pytest` passed with `725` tests
- current state:
  - still-disabled advisory boundary exists
  - manual/local validation harness exists
  - advisory experiment implementation remains blocked
  - dependency strategy is proposal-only
  - default CI does not require `topocore_v6`
  - runtime behavior remains unchanged

See:

- `docs/architecture/TOPOCORE_V6_MIGRATION_DOCUMENTATION_INDEX.md`
- `docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md`
- `docs/architecture/TOPOCORE_V6_PRIVATE_DEPENDENCY_STRATEGY_PROPOSAL.md`
- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

## 3. Phase 7 Scope Recap

Phase 7 definition:

- Phase 7 - Stabilization and Evidence Collection

Scope:

- documentation consolidation
- test coverage indexing
- private dependency strategy proposal
- manual evidence checklist
- current state stabilization
- no runtime activation

Explicit non-scope:

- no advisory experiment implementation
- no shadow activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no user-visible output change

## 4. Sprint 38 Review

Sprint 38 summary:

- added migration documentation index
- added test coverage index
- mapped phases, docs, tests, safety areas, and current NO-GO state
- improved navigation without changing runtime behavior

Decision:

- accepted as documentation and test index consolidation

## 5. Sprint 39 Review

Sprint 39 summary:

- added private TopoCore v6 dependency strategy proposal
- recommended local or manual-first access
- preserved default CI independence
- rejected vendoring, private git, and submodule approaches as the current strategy
- kept dependency work proposal-only

Decision:

- accepted as private dependency strategy proposal only
- no dependency implementation approved

## 6. Manual Evidence Collection Purpose

Manual evidence is needed because:

- current tests prove safety and inertness, not real TopoCore v6 runtime compatibility
- fake and stub tests do not prove real v6 facade behavior
- manual or local validation is the safest next evidence source
- evidence is required before reopening any controlled advisory experiment implementation discussion
- evidence must remain sanitized and non-user-visible

## 7. Manual Evidence Bundle Definition

Expected evidence bundle for each manual or local validation run:

- `evidence_bundle_id`
- `collection_date`
- `collector`
- `local_environment_label`
- RepoBrain commit
- TopoCore v6 source type
  - local editable install
  - local wheel outside repo
  - other approved local or private mode
- dependency mode
- command family
  - ask
  - review
  - weak-context
  - blocked or safety
  - fix-like governance
- fixture or scenario label
- adapter preview status
- v6 local validation status
- v6 advisory snapshot status
- decision-diff severity
- advisory artifact go or no-go hint
- failure category if any
- forbidden-output scan result
- `decide_raw` exposure result
- patch authorization result
- reviewer notes
- stop or go recommendation

Current truth:

- evidence bundle is a manual record format only
- Sprint 40 does not generate evidence automatically

## 8. Required Scenario Coverage

Minimum scenario coverage before reopening implementation discussion:

A. ask-like scenario

- safe query summary
- safe candidate IDs
- expected non-user-visible advisory output

B. review-like scenario

- PR context summary
- evidence summary
- verification signal summary
- risk hints

C. weak-context scenario

- missing evidence
- unknowns
- expected needs-more-information style advisory outcome

D. blocked or safety scenario

- unsafe or policy-sensitive request shape
- expected blocked or stop style advisory outcome

E. fix-like governance scenario

- `no_patch_reason` or patch safety notes
- expected no patch authorization
- no commit, branch, or PR creation

## 9. Evidence Sanitization Rules

Allowed evidence:

- safe labels
- safe command family
- safe status or action categories
- safe reason codes
- safe selected chunk IDs if already sanitized
- severity
- go or no-go hint
- sanitized failure category
- dependency or install status
- reviewer notes without raw payloads

Forbidden evidence:

- raw query text
- raw code
- raw diff
- raw prompts
- system prompts
- hidden prompts
- secrets
- tokens
- api keys
- private keys
- `.env` contents
- `decide_raw` output
- `compression_stats`
- raw traces
- governance internals
- event internals
- artifact internals
- raw exception dumps
- private repo URLs
- package tokens
- registry credentials

## 10. Evidence Review Checklist

For each evidence bundle, reviewer must confirm:

- RepoBrain commit is recorded
- dependency mode is local or manual only
- default CI independence is preserved
- evidence is sanitized
- no forbidden fields are present
- `decide_raw` was not called or exposed
- no patch authorization appears
- no user-visible output changed
- v5/TKYA remains primary
- v6 advisory remains non-user-visible
- decision-diff severity is recorded
- go or no-go hint is recorded
- failure category is sanitized
- high-severity mismatch is reviewed
- v6 more permissive than v5 is blocked or escalated
- missing dependency behavior is understood
- rollback or no-op behavior remains available

## 11. Evidence Acceptance Levels

Level 0 - Not collected

- no real local or private evidence exists

Level 1 - Collected but unreviewed

- evidence exists but has not been reviewed

Level 2 - Reviewed with blockers

- evidence reviewed
- blockers exist
- implementation discussion remains closed

Level 3 - Reviewed and clean

- evidence reviewed
- no forbidden-output findings
- no `decide_raw` exposure
- no patch authorization
- no high-severity unresolved mismatch

Level 4 - Sufficient for reopening discussion

- all required scenario families have Level 3 evidence
- dependency strategy is accepted
- default CI independence is confirmed
- human approval exists

Current truth:

- Level 4 does not automatically authorize implementation
- Level 4 only allows reopening a discussion

## 12. Reopen Criteria

Implementation discussion may be reopened only if:

- all five scenario families have reviewed evidence
- all required evidence is sanitized
- zero forbidden-output findings
- zero `decide_raw` exposure
- zero unauthorized patch or fix behavior
- missing `topocore_v6` does not affect default CI
- dependency or install strategy is accepted
- rollback or no-op behavior is confirmed
- explicit human approval is given

## 13. NO-GO Preservation

See:

- `docs/architecture/TOPOCORE_V6_PHASE_6_NO_GO_CHECKPOINT.md`

Current truth:

- Sprint 40 does not reverse the Phase 6 NO-GO
- advisory experiment implementation remains blocked
- runtime advisory activation remains blocked
- canary remains blocked
- route migration remains blocked
- v5 replacement remains blocked
- fix migration remains blocked

## 14. Phase 7 Decision

Decision:

- Phase 7 complete as stabilization baseline

GO:

- continue manual or local evidence collection outside runtime
- maintain docs and test indexes
- refine dependency proposal only as docs
- revisit implementation only after evidence reaches Level 4

NO-GO:

- advisory experiment implementation now
- runtime activation now
- canary
- route migration
- v5 replacement
- fix migration
- default CI private dependency

## 15. Next Safe Phase Placeholder

Placeholder only:

- Phase 8 - Manual Evidence Review and Reopen Decision

Purpose:

- review collected evidence if and when it exists
- decide whether the Phase 6 NO-GO can be revisited
- remain docs and checkpoint first

Current truth:

- Phase 8 is not automatically approved
- Phase 8 must not begin without explicit approval
- Phase 8 must not mean activation
- Phase 8 must not mean canary or route migration

## 16. Repository Boundary Confirmation

Repository boundaries:

RepoBrain-Action owns:

- primary/private GitHub runtime
- current v5/TKYA contract truth
- future v6 adapter around public facade
- GitHub Models LLM orchestration
- safe product-level output mapping
- tests/docs/regression guards
- manual/local advisory validation and artifact helpers
- disabled advisory skeleton and guard tests
- still-disabled advisory boundary and guard tests
- manual evidence checklist and current stabilization state

TopoCore v6 owns:

- foundation decision library
- public facade
- decision contracts
- typed-summary ingestion
- safe external decision boundary

`repobrain-community` owns:

- public external GitHub foundation host
- reusable external workflow
- public install template
- bounded external command surface

`elen-mcp-prod_v2`:

- validation-only surface

## 17. Explicit Non-Goals for Sprint 40

Current non-goals:

- no runtime code changes
- no tests required unless a documentation validation issue requires it
- no dependency implementation
- no implementation-adjacent code in Sprint 40
- no shadow-mode activation
- no advisory experiment activation
- no canary
- no route migration
- no v5 replacement
- no fix migration
- no patch behavior change
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency
- no `topocore_v6` import
- no `create_topocore` call
- no `decide` call
- no `decide_external` call
- no `decide_raw` call
- no LLM provider change
- no GitHub Models prompt behavior change
- no `repobrain-community` change
- no live GitHub API usage
- no live GitHub Models usage
- no artifact disk write, upload, or publish behavior
- no user-visible PR comment or check changes

## 18. Acceptance Criteria

Sprint 40 is complete only if:

- the new manual evidence collection and Phase 7 checkpoint document exists
- it clearly states Sprint 40 is docs-only
- it reviews Sprint 38 and Sprint 39
- it defines manual evidence bundle format
- it defines required scenario coverage
- it defines evidence sanitization rules
- it defines evidence review checklist
- it defines evidence acceptance levels
- it defines reopen criteria
- it preserves Phase 6 NO-GO
- it makes the Phase 7 checkpoint decision explicit
- it defines the next phase only as a placeholder
- repository boundaries are confirmed
- v5/TKYA remains the active primary runtime
- TopoCore v6 remains disabled, manual, local, and advisory only
- no runtime behavior changes are introduced
