# Repo Boundary Contract

## 1. Purpose

This document is the active repository ownership contract after Sprint 69.
Use it to keep product runtime, onboarding, and historical materials aligned.

## 2. Current Runtime Truth

Supported TopoCore runtime selectors:

- `auto`
- `v6`

Unsupported legacy selectors and envs:

- `v5`
- `lite`
- `RB_TKYA_BACKEND=v5`
- `RB_TKYA_BACKEND=lite`
- `RB_TOPOCORE_ALLOW_DEPRECATED_V5=1`
- `RB_TOPOCORE_V5_SIMULATE_DISABLED=1`

Mandatory safety boundaries remain in force:

- no autofix
- no patch application by default
- no file modification by RepoBrain behavior
- no commit creation by RepoBrain behavior
- no branch pushing by RepoBrain behavior
- no PR creation by RepoBrain behavior
- no safe-to-merge or approval verdicts
- no security verdicts

## 3. Repository Responsibilities

### 3.1 `topocore`

- private permanently
- engine implementation and decision internals
- not copied into consumer repositories
- not copied into `RepoBrain-Action`

### 3.2 `RepoBrain-Action`

`RepoBrain-Action` is the main product repository. It owns:

- the GitHub Action product surface
- v6-only runtime integration
- action packaging and workflow truth
- external repository onboarding, command docs, and troubleshooting
- docs/tests/current-truth alignment
- governance and regression tests
- external CLI ask-only secondary surface
- MCP ask-only secondary surface

### 3.3 External pilot repositories

External repositories such as `Elen-MCP-v.2.2.0` own:

- their own caller workflow in `.github/workflows/repobrain.yml`
- their own repo secrets/variables
- their own issue/PR smoke evidence
- their own application code and validation lifecycle

### 3.4 `repobrain-community`

`repobrain-community` is retired from the working product architecture.
It is not a runtime bridge, install bridge, docs bridge, template bridge, or dependency.
It may remain only as a historical repository until explicitly archived later.

## 4. Active Product Onboarding

Use these canonical files for current external onboarding:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- `docs/commands/REPOBRAIN_COMMANDS.md`
- `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- `docs/examples/repobrain_external_pilot_workflow.yml`
- `docs/examples/repobrain.instructions.md`

Do not direct current users to `repobrain-community`.

## 5. Historical Docs Policy

Historical trial, migration, and refactor documents may retain older wording when they are clearly labeled as historical or superseded.
They must not override current operator guidance.

## 6. Future Guardrails

Do not reintroduce into active product docs or workflows:

- `repobrain-community` as required install/runtime host
- `v5` or `lite` as supported runtime choices
- stale external workflow copies that contradict current product truth
- patch/autofix claims beyond accepted governance
