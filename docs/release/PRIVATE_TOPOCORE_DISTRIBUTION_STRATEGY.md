# Private TopoCore Distribution Strategy

## Boundary

TopoCore v6 remains private.
RepoBrain-Action does not include TopoCore v6 source.

## Current Private Beta Model

Current private beta uses:

- `TOPOCORE_V6_REPO_TOKEN`
- private checkout of the private TopoCore v6 repository

## Current Model Risk

The current private-checkout model is acceptable for a controlled private beta only.
Its risks include:

- source checkout expands the exposure surface
- per-consumer tokens can be stolen or misused
- private GitHub visibility is not sufficient as the only control
- source checkout into consumer workflows is not the desired long-term public distribution shape

## Public Repository Implication

A public `RepoBrain-Action` repository may still require authorized private TopoCore access.
That public or Marketplace path requires an approved private dependency strategy or non-source distribution strategy.

## Distribution Options

Possible future options include:

- private checkout
- private package registry
- signed wheel or artifact
- licensed binary or runtime artifact
- managed hosted runtime later

## Current Decision

- private checkout is acceptable for private beta only
- public or Marketplace distribution requires owner approval on distribution strategy
- no fallback to v5 is permitted

## Security Expectations

- per-consumer read-only token
- short expiration
- routine rotation
- immediate rotation after incident
- no shared broad token
- no source checkout into public artifacts
