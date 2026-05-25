# Support Policy

## Support Status

Current support stage:

- private beta RC
- public support is not guaranteed until explicit public-release approval

## Supported Installation Path

Supported installation path is the documented external pilot baseline:

- `docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md`
- `docs/examples/repobrain_external_pilot_workflow.yml`

## Supported Commands

Supported command surface today:

- `/repobrain audit`
- `/repobrain doctor`
- `/repobrain help`
- `/repobrain ask <query>`
- `/repobrain locate <query>`
- `/repobrain explain <query>`
- `/repobrain review`
- `/repobrain status`
- `/repobrain verify`
- `/repobrain fix`

## Unsupported

Current unsupported or not-approved surfaces:

- `v5`
- `repobrain-community`
- patch/autofix
- RepoBrain-created branch, commit, or PR behavior
- Marketplace install until approved
- `/repobrain score` as a live product command in the current release candidate

## Security Issue Reporting

- do not disclose secrets in GitHub issues or issue comments
- do not paste token values into logs or screenshots
- support channel for private beta security escalation is pending explicit approval if no separate channel exists yet

## Bug Reports Should Include

- command used
- run URL
- sanitized error text
- backend evidence
- repository visibility type

## Known Limitations

- private TopoCore v6 token requirement
- private action access during pilot
- fork restrictions
- verify may report `NOT_RUN` when no checks exist
- audit is implemented as a repository-level MVP
- doctor and status are implemented as report-only diagnostics
- score remains roadmap-only

## Support Boundaries

- no support for untrusted fork workflows with private secrets
- no support for modified internal workflow behavior beyond the documented baseline
- no support promise for public or Marketplace users until approval is made explicit
