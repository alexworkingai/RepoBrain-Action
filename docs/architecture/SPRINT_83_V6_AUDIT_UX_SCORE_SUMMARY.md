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

Live Elen-MCP smoke after Sprint 83 merge on `main`:

- issue:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/30`
- audit:
  - run: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26408575224`
  - mode: `v6-enriched scoring`
  - static baseline: `78 / 100 GOOD`
  - v6 enriched score: `77 / 100 GOOD`
  - backend: `auto -> v6`
  - fallback: `no / none`
  - contract: `topocore.audit_score.v1 accepted`
  - safe repo-relative evidence paths were visible and `[redacted-path]` noise did not appear
- score:
  - run: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26408632493`
  - mode: `v6-enriched scoring`
  - final score: `77 / 100 GOOD`
  - backend mode: `audit_v6_enriched_score_summary`
  - fallback: `no / none`
  - compact summary remained tied to the same guarded audit engine
- doctor:
  - run: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26408670815`
  - result: `PASS`
  - score command listed as supported
  - audit capability truth remained accurate
- status:
  - run: `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26408702699`
  - result: `success`
  - supported commands include score
  - score is described as a compact summary of the same guarded audit engine
- safety:
  - no secret exposure
  - no TopoCore source exposure
  - no patch/autofix
  - no mutation

## 8. Product Status

- `V6_AUDIT_UX_SCORE_READY`

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
