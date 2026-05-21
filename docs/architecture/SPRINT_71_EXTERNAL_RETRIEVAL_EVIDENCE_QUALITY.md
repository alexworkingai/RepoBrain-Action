# Sprint 71 - External Retrieval and Evidence Quality on Elen-MCP

## Purpose

Sprint 71 validates and improves v6 retrieval and evidence quality on the external `alexworkingai/Elen-MCP-v.2.2.0` repository.
It follows the Sprint 70 external command-matrix pass.
This sprint does not change runtime policy and does not enable patch/autofix.

## Baseline

- RepoBrain-Action latest main before Sprint 71:
  - `0d12a39 Record external command matrix`
- Sprint 70 product status:
  - `EXTERNAL_COMMAND_MATRIX_PASSED`
- external issue and PR `ask` smoke already passed
- no `v5`
- no `repobrain-community`

## Quality Rubric

Quality categories:

1. Evidence relevance
   - selected files should match the user question
   - changed files should be prioritized on PR commands
2. Evidence precision
   - file references should be specific and not misleading
   - missing or deleted files must not appear
3. Answer grounding
   - summary claims should be traceable to cited evidence
   - uncertainty should be explicit
4. Command-specific usefulness
   - `ask` should answer directly
   - `locate` should find likely files
   - `explain` should explain setup/logic without hallucination
   - `review` should note real risks
   - `fix` should stay conservative and useful without patching
5. Runtime evidence
   - requested/resolved backend should be visible
   - `v6` should resolve when backend is used
   - fallback should remain `none`
6. Safety
   - no patch application
   - no RepoBrain-created branch/commit/PR behavior
   - no secret exposure
   - no unsafe approval or safe-to-merge claims

Decision labels:

- `PASS_QUALITY`
- `PASS_WITH_MINOR_UX_GAP`
- `QUALITY_DEFECT`
- `BLOCKED`
- `NOT_APPLICABLE`

## Issue Quality Results

| Command | Run URL | Conclusion | Selected evidence count | Top evidence files | Backend requested/resolved | Fallback | Quality label | Notes |
|---|---|---|---:|---|---|---|---|---|
| `/repobrain ask Summarize the repository structure, primary entry points, and RepoBrain backend status.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224524120` | `success` | `5` | `.github/workflows/repobrain.yml`, `.github/repobrain.instructions.md`, `tests/endpoints.frontend-backend.test.ts`, `scripts/dev-entrypoint.sh` | `auto` / `v6` | `no` / `none` | `PASS_WITH_MINOR_UX_GAP` | Fixed now: workflow file became top evidence. Minor gap: answer still carries some support/test noise for a high-level overview. |
| `/repobrain ask Where is the RepoBrain pilot workflow configured and how does it connect to RepoBrain-Action?` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224563308` | `success` | `5` | `.github/workflows/repobrain.yml`, `.github/workflows/build_docker_and_deploy.yaml` | `auto` / `v6` | `no` / `none` | `PASS_WITH_MINOR_UX_GAP` | Fixed now: correct workflow file is top evidence. Minor gap: a secondary deployment workflow still appears ahead of pilot docs. |
| `/repobrain locate RepoBrain workflow configuration.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224606804` | `success` | `3` | `.github/workflows/repobrain.yml`, `.github/workflows/build_docker_and_deploy.yaml`, `.github/repobrain.instructions.md` | `auto` / `v6` | `no` / `none` | `PASS_QUALITY` | Direct locate answer now leads with the correct workflow file and keeps file refs precise. |
| `/repobrain explain RepoBrain pilot setup.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224646313` | `success` | `5` | `.github/workflows/repobrain.yml`, `.github/repobrain.instructions.md`, `docs/repobrain_pilot.md`, `docs/repobrain_pr_smoke_fixture.md`, `tests/setup.ts` | `auto` / `v6` | `no` / `none` | `PASS_QUALITY` | Explanation now includes the actual workflow file and stays grounded in pilot docs and repo guidance. |

## PR Quality Results

| Command | Run URL | Conclusion | PR metadata used | Selected evidence count | Changed files considered | Top evidence files | Backend requested/resolved | Fallback | Patch/verification status | Quality label | Notes |
|---|---|---|---|---:|---|---|---|---|---|---|---|
| `/repobrain ask Summarize this PR and identify the most relevant changed files.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224057784` | `success` | `yes` | `3` | `3` | `.github/repobrain.instructions.md`, `docs/repobrain_quality_fixture.md`, `docs/repobrain_quality_notes.md` | `auto` / `v6` | `no` / `none` | `NOT_RUN` | `PASS_QUALITY` | Changed files were correctly prioritized and segmented as docs plus `.github` support. |
| `/repobrain review Summarize review risks for this PR and cite the most relevant evidence.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224089453` | `success` | `yes` | `3` | `3` | `.github/repobrain.instructions.md`, `docs/repobrain_quality_fixture.md`, `docs/repobrain_quality_notes.md` | `auto` / `v6` | `no` / `none` | `Verification NOT_RUN: PASS=0, FAIL=0, NOT_RUN=2` | `PASS_QUALITY` | Review stayed conservative, identified the PR as docs-only, and did not invent approval or merge claims. |
| `/repobrain locate retrieval quality fixture notes.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224127145` | `success` | `yes` | `3` | `3` | `docs/repobrain_quality_fixture.md`, `docs/repobrain_quality_notes.md`, `docs/QUALITY_GATES.md` | `auto` / `v6` | `no` / `none` | `NOT_RUN` | `PASS_QUALITY` | Locate prioritized the changed fixture docs and kept references precise. |
| `/repobrain explain the retrieval quality fixture changes in this PR.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224156827` | `success` | `yes` | `3` | `3` | `docs/repobrain_quality_fixture.md`, `docs/repobrain_quality_notes.md`, `docs/QUALITY_GATES.md` | `auto` / `v6` | `no` / `none` | `NOT_RUN` | `PASS_WITH_MINOR_UX_GAP` | Grounding was correct and changed files were prioritized, but the prose was more generic than ideal for a small docs-only PR. |
| `/repobrain fix Propose a safe documentation-only improvement for this PR, but do not apply any patch.` | `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26224192433` | `success` | `yes` | `3` | `3` | `docs/repobrain_quality_fixture.md`, `docs/repobrain_quality_notes.md`, `.github/repobrain.instructions.md` | `auto` / `v6` | `no` / `none` | `no_patch` | `PASS_QUALITY` | Conservative `no_patch` behavior stayed grounded and explicitly non-mutating. |

## Defects / UX Gaps

Fixed now:

- Issue-side workflow discovery quality defect:
  - `.github/workflows/repobrain.yml` was not indexed by default because `repobrain/scan.py` did not include `.github/workflows/**`.
  - issue-side workflow queries therefore over-weighted docs and support files, including `.topocore-v6` support paths for non-TopoCore questions.
  - Sprint 71 fix:
    - added `.github/workflows/**` to the default scan include set
    - added targeted workflow-query boosts and private dependency penalties in retrieval ranking
    - reran affected issue commands and confirmed workflow evidence moved to the top

Deferred:

- Issue-side high-level overview still includes some support/test noise after the primary workflow evidence.
- Issue-side workflow setup ask still surfaces a secondary deployment workflow before pilot docs.
- PR explain output is grounded but still somewhat generic for a small docs-only fixture PR.

Not defects:

- issue-side `ask` and `explain` still report `issue_only_policy_disabled` for LLM usage; this is the current policy guard, not a retrieval defect
- PR `fix` returned `no_patch`, which is the intended safe outcome

## Backend / Safety Evidence

- `v6` resolved where applicable:
  - issue `ask` overview
  - issue `ask` workflow setup
  - issue `locate`
  - issue `explain`
  - PR `ask`
  - PR `review`
  - PR `locate`
  - PR `explain`
  - PR `fix`
- no `v5`
- no `repobrain-community`
- no patch application
- no RepoBrain-created branch/commit/PR behavior
- no unsafe approval or safe-to-merge claim
- no secret exposure

## Product Status

`EXTERNAL_RETRIEVAL_QUALITY_PASSED`

## Next Step

Sprint 72 should focus on:

- verify command productionization on the external repo
- tightening issue-side overview signal quality
- sharpening PR explain prose when the PR is docs-heavy but low risk

Sprint 72 follow-up:

- external PR `verify` now reports explicit `PASS/WARN/FAIL/PENDING/NOT_RUN/UNKNOWN` semantics
- live external verify now records source availability, limitations, and head-SHA audit anchors
- see `docs/architecture/SPRINT_72_VERIFY_COMMAND_PRODUCTIONIZATION.md`

## Non-Goals

- no `v5`
- no `repobrain-community`
- no patch/autofix
- no production/Marketplace switch
