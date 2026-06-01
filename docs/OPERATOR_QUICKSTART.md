# RepoBrain Operator Quickstart

## Scope

This quickstart is for operators validating RepoBrain in:

- GitHub mode
- direct external repository pilot mode
- external CLI ask-only mode

## Canonical Operator References

Use these first:

- Install guide: `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- Command guide: `docs/commands/REPOBRAIN_COMMANDS.md`
- Troubleshooting: `docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md`
- Permissions reference: `docs/onboarding/permissions.md`

## First External Validation Steps

1. install the caller workflow from `docs/examples/repobrain_external_pilot_workflow.yml`
2. configure `TOPOCORE_V6_REPO_TOKEN`
3. run an issue `/repobrain ask ...`
4. run a PR `/repobrain ask ...`
5. if needed, validate `/repobrain verify` and `/repobrain fix` in PR scope

Expected first-smoke backend truth:

- requested backend: `auto` or `v6`
- resolved backend: `v6`
- fallback used: `no`
- fallback reason: `none`

## Stop Conditions

Stop and resolve setup if:

- public action resolution is not working because Actions policy blocks external actions or the ref is wrong
- `TOPOCORE_V6_REPO_TOKEN` is missing or invalid
- the workflow permissions are tighter than the read-mostly baseline
- unsupported commands are being treated as supported
- docs and observed command behavior diverge
