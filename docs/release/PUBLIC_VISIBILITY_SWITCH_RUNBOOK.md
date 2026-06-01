# Public Visibility Switch Runbook

## Purpose

This runbook describes how to perform the RepoBrain public visibility switch after explicit owner approval.

## Sprint 91 Boundary

This runbook is executed in Sprint 91 only after pre-switch validation passes.
It was not executed in Sprint 85.

## Prerequisites

- explicit owner approval
- completed approval checklist
- selected-partner runtime/token issuance ready
- public-facing docs verified
- RepoBrain-Action installed-package runtime proof already passed

## Pre-Switch Checks

1. confirm repository is still private
2. confirm README renders correctly
3. confirm LICENSE is present
4. confirm `action.yml` is present
5. confirm partner docs are present
6. confirm no secret, token-like, or private-path residue remains
7. confirm no private TopoCore source is present

## Switch Steps

- perform the GitHub visibility change manually in the GitHub UI or through an approved operator command
- do not run visibility switching automatically from RepoBrain

## Immediate Post-Switch Checks

1. README renders correctly
2. LICENSE is visible
3. no secrets are exposed
4. no private source is exposed
5. `action.yml` is visible
6. install docs are visible
7. partner docs are visible

## Partner Notification Checklist

- send setup pack
- send runtime access runbook
- send feedback template
- confirm testing boundaries and security notes

## Rollback Caveat

Once public, clones may persist even if visibility is switched back later.

## Emergency Response

1. switch back to private if needed
2. rotate credentials if needed
3. revoke partner runtime tokens if needed
4. inspect logs
5. notify affected testers if appropriate
