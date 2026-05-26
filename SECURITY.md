# Security Policy

## Supported Versions And Current Status

Current product stage:

- private pre-public release candidate
- RepoBrain-Action remains private in Sprint 86
- public visibility is not yet approved or executed
- GitHub Marketplace publication has not started

Current supported runtime/product truth:

- v6-only runtime policy
- no v5
- no repobrain-community dependency
- no patch/autofix
- no RepoBrain-created branch, commit, or PR behavior

## Reporting Security Issues

Do not disclose security issues, secrets, token values, or private runtime details in public issues or public comments.

Until a broader public channel is explicitly approved, use a private maintainer-controlled reporting path.
If no dedicated channel is available, escalate privately to the repository owner/maintainer rather than opening a public issue with sensitive detail.

## Sensitive Disclosure Rules

Never disclose:

- TopoCore v6 source
- private TopoCore repository contents
- runtime token values
- API keys
- private keys
- local private checkout paths
- partner runtime access credentials

RepoBrain outputs are not security approval, legal approval, safe-to-merge guidance, or production certification.

## Partner Pilot Security Reporting

Selected partners should:

- report suspected leaks privately
- provide sanitized run URLs and error messages
- avoid posting credentials or private paths in screenshots, issues, or logs
- pause testing if runtime-token handling is uncertain

## Token And Runtime Incident Guidance

If a runtime credential or private token is suspected compromised:

1. revoke the affected credential immediately
2. rotate any related credentials
3. inspect audit logs and recent workflow runs
4. verify no private TopoCore source was copied into consumer repositories or artifacts
5. notify affected partner testers if appropriate

## TopoCore Boundary

- TopoCore v6 source remains private
- no TopoCore source rights are granted through RepoBrain-Action
- no source checkout into partner repositories is preferred for selected partner testing
- installed private package mode is preferred over private_checkout where feasible

## Marketplace And Public Status

- RepoBrain-Action is not yet Marketplace-published
- Sprint 86 does not execute the public visibility switch
- any public switch still requires explicit owner approval after enterprise P0 hardening
