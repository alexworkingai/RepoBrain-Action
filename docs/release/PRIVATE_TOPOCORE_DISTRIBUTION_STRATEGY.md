# Private TopoCore Distribution Strategy

## Purpose

This document records the allowed runtime distribution shapes for private TopoCore v6 and the current decision for RepoBrain partner testing.

## Boundary

- TopoCore v6 remains private.
- RepoBrain-Action does not include TopoCore v6 source.
- No TopoCore source license is granted through RepoBrain-Action.
- No v5 fallback is permitted.

## Distribution Modes

### 1. `private_checkout`

Status:
- controlled private beta only

Use:
- owner-controlled repos
- current Elen-MCP pilot
- narrow debugging or migration cases

Why it is not the preferred public-ready path:
- checks out private source into the consumer workflow workspace
- expands source exposure surface
- couples partner setup to repo/ref access instead of a narrower runtime artifact

### 2. `installed_private_package`

Status:
- selected near-term partner-testing mode

Meaning:
- TopoCore v6 is provided as an installed private package or approved runtime artifact
- consumer workflows do not need a private TopoCore source checkout in the workspace
- RepoBrain consumes the existing public facade including `run_audit_score_v1`

Observed Sprint 84 result:
- private runtime wheel build is feasible
- installed artifact import is feasible in a clean environment
- public API and `run_audit_score_v1` capability remain available after install
- package artifact excludes tests/docs from the installed wheel payload

Honest limitation:
- a normal Python wheel can still contain readable `.py` implementation files
- this reduces repository/source-checkout exposure, but it is not equivalent to strong source secrecy
- selected partner testing may use this mode under scoped access and explicit approval
- broader public or Marketplace distribution may still need stronger hardening later

### 3. `managed_runtime`

Status:
- future stronger enterprise/public model

Meaning:
- RepoBrain calls a controlled hosted TopoCore runtime
- no TopoCore code enters the consumer repository workspace

Sprint 84 status:
- not implemented

### 4. `compiled_or_signed_runtime_artifact`

Status:
- future hardening option if package readability becomes unacceptable

Meaning:
- signed, minimized, or otherwise hardened runtime artifact beyond a plain wheel

Sprint 84 status:
- not required for selected partner testing
- still a future option for broader rollout

## Current Decision

Distribution decision:
- `INSTALLED_PRIVATE_PACKAGE_SELECTED`

Implication:
- `private_checkout` remains beta-only
- selected partner testing should prefer installed private package mode
- RepoBrain-Action can become public later without exposing the TopoCore source repository itself
- stronger secrecy than a plain wheel remains future work, not Sprint 84 work

## Token And Access Model

Minimum policy:
- per-partner token or equivalent scoped credential
- read-only access
- expiration required
- rotation on a defined schedule
- immediate revocation after incident or partner offboarding
- no shared broad PAT
- no source-repo collaborator access unless explicitly approved
- package/artifact scope preferred over source-repo scope where feasible

## Public-Ready Implication

Sprint 84 result:
- public readiness is no longer blocked by lack of any non-checkout runtime path
- public visibility still requires explicit owner approval
- Marketplace remains out of scope and not ready

## Non-Goals Preserved

- no public TopoCore source distribution
- no TopoCore source exposure in RepoBrain-Action
- no v5
- no `repobrain-community`
- no patch/autofix
