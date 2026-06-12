# Sprint 93D End-to-End Self-Service Workflow

Correction notice:
After Sprint 93E live validation, the `hosted_api` path was reclassified as experimental and future external-runtime mode because it requires a deployed hosted API.
The default trusted beta path is now the GitHub-native control plane documented in `docs/architecture/SPRINT_94A_GITHUB_NATIVE_BETA_ARCHITECTURE_CORRECTION.md`.

This companion alias file is the canonical Sprint 93D architecture reference name used by later documentation.

For the full Sprint 93D implementation note, see:
- `docs/architecture/SPRINT_93D_END_TO_END_PARTNER_SELF_SERVICE_WORKFLOW.md`

Current truth:
- Sprint 93D wired the hosted self-service implementation path for supported `ask`, `audit`, and `score` commands.
- Those hosted transport foundations remain reusable.
- Sprint 93D did not claim unrestricted public launch, Marketplace readiness, or final trusted-partner validation.
- Default trusted beta direction now shifts to the GitHub-native control plane rather than hosted external runtime.
