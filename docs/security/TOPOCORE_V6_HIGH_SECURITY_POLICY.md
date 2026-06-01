# TopoCore v6 High Security Policy

## 1. Purpose

TopoCore v6 is the primary proprietary asset and must be treated as a high-value secret asset.

## 2. Threat Model

Threats to plan against include:

- private GitHub repository compromise
- developer workstation compromise
- malicious or poisoned IDE extension
- stolen PAT or fine-grained token
- GitHub Actions secret exfiltration
- workflow supply-chain compromise
- overbroad GitHub App, OAuth app, or deploy key access
- stale token not rotated
- accidental source checkout into consumer repositories

## 3. Security Principle

Assume private GitHub visibility is not sufficient by itself.
Access control, token discipline, workstation discipline, and distribution discipline all matter.

## 4. Access Policy

- keep collaborators to the minimum necessary set
- require strong account protection such as 2FA or passkeys
- review outside collaborators regularly
- review GitHub Apps and OAuth apps regularly
- review deploy keys regularly
- use CODEOWNERS, rulesets, and branch protection where feasible

## 5. Token Policy

- no broad long-lived PATs
- per-consumer tokens
- read-only access where possible
- expiration required
- rotation on a defined schedule
- immediate rotation after incident
- no token reuse across consumer repositories
- no token values in docs or logs

## 6. Developer Workstation Policy

- use a separate trusted workspace or profile for TopoCore work when practical
- maintain an extension allowlist
- do not use untrusted AI or code extensions in a TopoCore workspace
- avoid casual local clones on untrusted machines
- do not store tokens in plaintext
- use a separate admin browser or session when practical

## 7. GitHub Actions Policy

- disable Actions in the TopoCore repository unless required
- no `pull_request_target` for untrusted code
- no untrusted workflow execution with secrets
- no unnecessary secrets in the TopoCore repository
- enable secret scanning and push protection where available

## 8. Distribution Policy

- `private_checkout` is beta-only
- target public or Marketplace distribution should avoid source checkout
- future approved options may include:
  - private package registry
  - signed wheel or artifact
  - licensed binary or runtime artifact
  - managed hosted runtime
- no v5 fallback

## 9. Incident Response

- revoke and rotate tokens
- review audit logs
- review repository access
- review Apps, OAuth apps, and deploy keys
- verify no source was copied into consumer repositories
- notify and update affected consumers

## 10. Current Sprint 77 Decision

- TopoCore v6 source remains private
- no source license is granted
- `private_checkout` remains private beta only
- non-source distribution is a public-readiness blocker and next-stage task

## 11. Sprint 84 Distribution Gate Update

- near-term selected partner mode: `installed_private_package`
- `private_checkout` remains beta-only
- package/artifact scope is preferred over source-repo scope where feasible
- a normal Python wheel may still contain readable implementation files, so partner testing stays controlled and approval-based
- stronger managed-runtime or hardened-artifact protection remains future work

## 12. Sprint 86 Enterprise P0 Hardening Update

- SECURITY / CONTRIBUTING / CODEOWNERS now reinforce the public-switch boundary from the RepoBrain side
- installed-package live proof remains a hard gate before public visibility approval
- Sprint 86 attempted that proof without `private_checkout`; the result stayed blocked on external package delivery, not on source secrecy policy
- Sprint 88 selected a GitHub-supported minimum-scope artifact-read credential path, but the proof still cannot proceed until the owner issues that credential into the external workflow
- no TopoCore source rights are granted through partner runtime access
- no public switch is executed in Sprint 86
