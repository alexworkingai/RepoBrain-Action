# Sprint 83 - v6 Audit UX Hardening and Score Summary

## 1. Purpose

Sprint 83 hardens v6-enriched audit UX and implements `/repobrain score`.
It follows Sprint 82 live v6-enriched audit.
It does not change public visibility, Marketplace, runtime policy, or TopoCore distribution.

## 2. Baseline

- latest main before Sprint 83: `9ede334 Record private v6 audit capability live evidence`
- Sprint 82 status: `V6_AUDIT_LIVE_V6_ENRICHED_PASSED`
- deferred before Sprint 83:
  - score command
  - `[redacted-path]` noise
  - v6 audit UX hardening

## 3. Evidence Path Rendering

Sprint 83 keeps safe repo-relative evidence visible while preserving the existing private-boundary guard.

Safe display rules:

- `README.md`
- `docs/...`
- `tests/...`
- `src/...`
- `repobrain/...`
- `.github/workflows/...`
- repo-relative manifests such as `pyproject.toml` and `package.json`

Redaction rules:

- `.topocore-v6/...`
- absolute Windows or POSIX local paths
- token-like strings
- traceback-style local path frames
- generated, cached, artifacts, or reports directories as primary evidence

No private checkout evidence is shown.

## 4. v6 Audit UX Hardening

Sprint 83 tightens the v6-enriched audit layout around one compact score card:

- static baseline and v6 enriched score shown together
- explicit delta
- bounded adjustments section
- evidence summary with safe paths only
- limitations and runtime evidence remain visible
- no duplicated focus or repeated safety paragraphs

## 5. Score Command

`/repobrain score` is implemented as a compact summary of the same guarded audit engine.
It is supported in issue and PR scope.
It reuses the same:

- static baseline
- optional private `v6` enrichment
- `topocore.audit_score.v1` contract guard
- fallback behavior
- no-mutation safety

It does not introduce a separate scoring model.

## 6. Doctor / Status Truth Updates

Sprint 83 updates doctor and status so they now report:

- score command support
- audit v6 capability truth
- score as a compact summary of the same guarded audit engine
- no expensive audit run requirement just to render status/doctor

## 7. Live Results

Live Elen-MCP smoke is recorded after Sprint 83 merge on `main`:

- audit issue/run: pending Sprint 83 live evidence at doc creation time
- score issue/run: pending Sprint 83 live evidence at doc creation time
- doctor issue/run: pending Sprint 83 live evidence at doc creation time
- status issue/run: pending Sprint 83 live evidence at doc creation time
- backend evidence must remain honest
- safety must remain no-patch/no-mutation

## 8. Product Status

- `V6_AUDIT_UX_SCORE_READY` if audit, score, doctor, and status all pass live after merge
- `V6_AUDIT_UX_READY_SCORE_DEFERRED` only if score must stay out for a documented blocker
- `BLOCKED_ON_PATH_REDACTION` if safe path rendering cannot be fixed without exposure risk
- `BLOCKED_ON_SCORE_COMMAND` if score cannot reuse the same guarded audit engine
- `BLOCKED_ON_EXTERNAL_LIVE_RUN` if post-merge live validation cannot complete

## 9. Next Step

If Sprint 83 passes, the recommended next step is:

- Sprint 84 - Private TopoCore Runtime Packaging / Public-Ready Distribution Gate

## 10. Non-Goals

- no v5
- no repobrain-community
- no runtime policy change
- no patch/autofix
- no visibility switch
- no Marketplace publication
- no public TopoCore distribution
- no TopoCore source exposure
- no Microsoft partnership claim
