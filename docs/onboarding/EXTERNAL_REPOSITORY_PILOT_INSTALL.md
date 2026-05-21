# External Repository Pilot Install

## Purpose

This document defines the direct external repository pilot install path after Sprint 68 v6-only closeout and Sprint 69 product transition.

## Supported Architecture

Current supported install shape:

- `topocore`: private TopoCore v6 repository
- `RepoBrain-Action`: main product action repository
- external repository: consumer project with its own caller workflow
- `repobrain-community`: retired and not used

`repobrain-community` is not required for current pilot onboarding or runtime wiring.

## Repository Roles

- `topocore`: private engine and decision internals; do not copy into consumer repositories
- `RepoBrain-Action`: product action, workflow truth, docs, tests, and pilot onboarding
- external repository: installs the caller workflow and owns smoke evidence
- `repobrain-community`: retired from runtime, install, docs, onboarding, and bridge responsibilities

## Required Secrets and Variables

Required secret in the consumer repository:

- `TOPOCORE_V6_REPO_TOKEN`
  - must grant read access to the private `topocore` repository
  - do not print or commit the token

Current RepoBrain-Action repository variable:

- `RB_ENABLE_ISSUE_COMMENT_V6_LAB=1`

Operator note:

- this variable remains part of the current RepoBrain-Action repository setup
- the direct external pilot workflow documented here does not depend on `repobrain-community`
- if you keep the direct issue_comment private-checkout steps unconditional, the external caller repository does not need a separate `RB_ENABLE_ISSUE_COMMENT_V6_LAB` gate variable

## Minimal Workflow

Start from:

- `docs/examples/repobrain_external_pilot_workflow.yml`

Install it as:

- `.github/workflows/repobrain.yml`

Optional repo guidance example:

- `docs/examples/repobrain.instructions.md`
- copy to `.github/repobrain.instructions.md` only if you want concise repo-specific review hints

## TopoCore v6 Private Dependency Setup

The consumer workflow must:

1. checkout the consumer repository at the correct PR/issue ref
2. checkout private `alexworkingai/topocore`
3. expose the private checkout path through `RB_TOPOCORE_V6_LOCAL_PATH` and `PYTHONPATH`
4. call `alexworkingai/RepoBrain-Action@main`

Do not vendor or copy TopoCore v6 into `RepoBrain-Action` or the consumer repository.

## Commands For First Smoke

Safe first smoke on issue:

```text
/repobrain ask Summarize current RepoBrain TopoCore backend status.
```

Safe first smoke on PR:

```text
/repobrain ask Summarize this PR with RepoBrain backend diagnostics.
```

## Expected Backend Evidence

Expected evidence in a healthy smoke run:

- requested backend: `auto` or `v6`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`
- no `repobrain-community` dependency
- no v5 fallback
- no patch/autofix behavior
- no commit/branch/PR creation by RepoBrain behavior

## Troubleshooting

### Missing private dependency access

Symptoms:

- private checkout step fails
- runtime import diagnostics fail
- backend does not resolve to `v6`

Check:

- `TOPOCORE_V6_REPO_TOKEN` exists in the consumer repository
- token has read access to `alexworkingai/topocore`
- workflow still checks out the private repo before running RepoBrain

### Wrong action install shape

Symptoms:

- workflow tries to execute consumer-repo scripts instead of RepoBrain-Action scripts

Check:

- caller workflow uses `alexworkingai/RepoBrain-Action@main`
- RepoBrain-Action action steps run from `GITHUB_ACTION_PATH`, not consumer workspace paths

### Missing backend evidence

Symptoms:

- comment appears but backend evidence is absent or incomplete

Check:

- current caller workflow still passes `topocore_backend`
- private TopoCore v6 install completed
- workflow did not silently downgrade to a different install path

## What Not To Use

Do not use:

- `repobrain-community`
- `v5`
- `lite`
- patch/autofix by default
