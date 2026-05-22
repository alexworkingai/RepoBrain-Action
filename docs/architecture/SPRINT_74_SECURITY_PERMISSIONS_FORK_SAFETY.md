# Sprint 74 - Security, Permissions, and Fork Safety

## 1. Purpose

Sprint 74 hardens the external RepoBrain product path around permissions, secrets, private action access, and fork safety.
It follows Sprint 73 fix productization.
This sprint does not enable patch/autofix.

## 2. Baseline

Baseline before Sprint 74:

- RepoBrain-Action latest main before Sprint 74:
  - `c0ce8a4 Productize external fix command`
- Sprint 70 command matrix passed.
- Sprint 71 retrieval quality passed.
- Sprint 72 verify productionization passed.
- Sprint 73 fix product path passed.

## 3. Security Model

Current external product security model:

- `topocore`
  - private TopoCore v6 repository
- `RepoBrain-Action`
  - private product action during pilot
- external consumer repository
  - owns caller workflow and repository secrets
- `repobrain-community`
  - not used
- `v5`
  - unsupported and not part of the external path

Secret model:

- `TOPOCORE_V6_REPO_TOKEN`
  - required for private TopoCore checkout
  - name may appear in setup logs
  - value must never appear in logs, comments, or artifacts
- missing or invalid private token access is a sanitized setup failure, not a runtime fallback

Private action access model:

- `RepoBrain-Action` is private during the pilot
- consumer repositories must be allowed to resolve that private action
- Actions policy can block resolution even when the `uses:` ref is correct

## 4. Permissions Model

Current direct external pilot baseline:

- `contents: read`
- `models: read`
- `issues: write`
- `pull-requests: read`
- `checks: read`
- `statuses: read`
- `actions: read`

Why each permission is needed:

- `contents: read`
  - repository files and diff context
- `models: read`
  - current GitHub Models-backed runtime path
- `issues: write`
  - issue comments and PR issue-comment replies
- `pull-requests: read`
  - PR metadata and changed files
- `checks: read`
  - check-run visibility for `/repobrain verify`
- `statuses: read`
  - combined commit status visibility
- `actions: read`
  - workflow-run visibility for `/repobrain verify`

Permissions explicitly not required for the current external product path:

- `contents: write`
- `pull-requests: write`
- `checks: write`
- `pull_request_target`
- deployment/package write permissions

## 5. Secret / Token Degradation

Current truth:

- missing `TOPOCORE_V6_REPO_TOKEN`
  - fails during private checkout/install before RepoBrain runtime executes
- invalid token or missing private-repo access
  - fails as a sanitized setup problem
- private checkout failure
  - does not justify fallback to `v5`
  - does not justify switching away from the direct `RepoBrain-Action` path

Expected sanitized behavior:

- secret name may appear
- secret value must not appear
- no raw token dump
- no private local path leak beyond generic bounded diagnostics

Live missing-secret mutation on `main` was intentionally not run in Sprint 74.
That scenario remains covered by docs, readiness guidance, and static security guards because the real pilot secret must stay intact.

## 6. Private Action Access Troubleshooting

Known external failure:

- `Unable to resolve action ... repository not found`

Possible causes:

- wrong action ref
- private action sharing not enabled for the consumer repository owner
- consumer repository Actions policy is too strict

Known Sprint 69 root cause on `alexworkingai/Elen-MCP-v.2.2.0`:

- `allowed_actions=local_only`

Fix path:

1. confirm the workflow uses `alexworkingai/RepoBrain-Action@main`
2. confirm the action repository is shared to repositories owned by `alexworkingai`
3. confirm the consumer repository Actions policy allows external/private action resolution

## 7. Fork Safety Policy

Current pilot fork policy:

- no `pull_request_target` by default
- do not expose `TOPOCORE_V6_REPO_TOKEN` to untrusted fork code
- do not checkout untrusted fork head code with the private TopoCore token
- prefer restricted or default-branch runtime behavior instead of widening trust

Current example workflow stays conservative:

- same-repo PR comments use PR head SHA
- fork PR comments stay on default workflow/runtime SHA with reason `fork_pr_uses_default_branch_runtime`
- no patch/autofix path is enabled

Live fork testing was not run in Sprint 74 because creating an untrusted secret-bearing fork scenario would exceed the safe pilot boundary.

## 8. Live Security Checks

Baseline ask:

- issue URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/21`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26246272758`
- conclusion:
  - `success`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `v6`
  - fallback used: `no`
  - fallback reason: `none`
- safety result:
  - no secret exposure
  - no v5
  - no `repobrain-community`
  - no patch/autofix behavior

PR verify:

- PR URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/22`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26279115987`
- conclusion:
  - `success`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `not_applicable`
  - fallback reason: `verify_report_only`
- safety result:
  - informational verify only
  - no safe-to-merge claim
  - no secret exposure

Unsafe fix mutation:

- PR URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/pull/22`
- run URL:
  - `https://github.com/alexworkingai/Elen-MCP-v.2.2.0/actions/runs/26279356340`
- conclusion:
  - `success`
- backend evidence:
  - requested backend: `auto`
  - resolved backend: `v6`
  - fallback used: `no`
- safety result:
  - `BLOCKED_BY_SAFETY`
  - no patch
  - no branch/commit/PR creation by RepoBrain behavior
  - no secret exposure

Missing secret live test:

- not run on `main`
- intentionally deferred to isolated future fixture work if needed

Fork live test:

- not run
- policy and static guards only in Sprint 74

## 9. Tests / Static Guards

Sprint 74 adds or updates:

- `tests/test_external_security_permissions_fork_safety.py`
- `tests/test_install_readiness.py`
- `tests/test_github_app_onboarding_docs.py`
- `scripts/check_install_readiness.py`

Static guard coverage now includes:

- no `pull_request_target` in the external workflow example
- no `contents: write` in the external workflow example
- no `checks: write` or `pull-requests: write` in the external workflow example
- explicit private-action troubleshooting
- explicit token-degradation and fork-safety documentation
- preserved no-patch/no-mutation product truth

## 10. Defects / Gaps

Fixed now:

- external example and onboarding no longer overstate `checks: write` or `pull-requests: write`
- private action access troubleshooting is now explicit in current onboarding docs
- fork policy is now explicit in the external pilot docs
- unsafe mutation prompt matching now catches `Apply a patch and commit it.` and returns `BLOCKED_BY_SAFETY`
- the external pilot rerun after pushing `a19f0a3 Harden fix mutation safety matching` confirmed the fix on `RepoBrain-Action@main`

Deferred:

- live missing-secret degradation was not exercised on `main`
- live untrusted-fork secret-withholding was not exercised in the pilot repo

Not defects:

- issue/PR live checks still ran under the existing healthy pilot installation
- verify remains informational and may legitimately resolve `not_applicable` when it is report-only
- the first unsafe-fix run on old `origin/main` returned `PROPOSAL_READY`; this was a sequencing and matcher hardening gap that Sprint 74 closed before final evidence capture

## 11. Product Status

- `SECURITY_PERMISSION_FORK_SAFETY_PASSED`

## 12. Next Step

Recommended next sprint:

- Sprint 75 - UX, Onboarding, and Troubleshooting Polish

Focus:

- tighten user-facing troubleshooting
- make product status expectations easier to understand
- preserve current runtime and safety boundaries

## 13. Non-Goals

- no v5
- no repobrain-community
- no patch/autofix
- no production/Marketplace switch
- no RepoBrain-created branch/commit/PR behavior
