# Pilot Kickoff Plan

## 1. Purpose

This plan defines the selected partner pilot kickoff path after the RepoBrain public visibility switch.

## 2. Pilot Status

- owner approval received for public RepoBrain-Action visibility
- Sprint 91 starts with the switch still pending execution
- Marketplace is not started

## 3. Partner Selection Criteria

- repositories where GitHub Actions are permitted
- teams comfortable with scoped private runtime credentials
- repos that benefit from audit, score, doctor, status, and ask
- partners willing to provide structured feedback

## 4. Partner Onboarding Steps

1. confirm partner repository admin contact
2. provide public RepoBrain action reference and setup docs
3. provision partner-scoped runtime credential
4. validate workflow permissions
5. run first smoke commands
6. collect feedback in the agreed cadence

## 5. Runtime Access

- `installed_package` is preferred
- partner credential should be equivalent to `TOPOCORE_V6_ARTIFACT_TOKEN` in scope model
- per-partner credentials only
- no shared broad PAT
- no TopoCore source checkout by default

## 6. Required Workflow Permissions

- read-mostly baseline
- no `pull_request_target`
- no broad write scopes

## 7. First Smoke Commands

- `/repobrain doctor`
- `/repobrain status`
- `/repobrain audit`
- `/repobrain score`
- `/repobrain ask`

## 8. Feedback Cadence

- initial setup feedback after first run
- first quality review after audit/score usage
- weekly or agreed pilot check-ins during early rollout

## 9. Feedback Template Link

- `docs/partner/PARTNER_FEEDBACK_TEMPLATE.md`

## 10. Incident and Security Reporting

- use the partner security notes and runtime access runbook
- report suspected token or source-exposure issues immediately

## 11. Exit Criteria For Marketplace Planning

- selected partner pilot is stable
- feedback loop is active
- no material source-secrecy or runtime-delivery regressions
- owner explicitly approves Marketplace planning as a later phase
