# Sprint 92C Permission Classification and Diagnostics Tiering

## 1. Purpose

Sprint 92C hardens partner-facing output quality without changing runtime architecture or safety policy.

## 2. Baseline After Hotfix 92A and Manual PR Matrix

- RepoBrain-Action is public.
- TopoCore remains private.
- manual issue command matrix passed after Hotfix 92A.
- manual PR command matrix passed only after `pull-requests: write` was added in Elen-MCP.
- audit and score still over-classified that permission as broad workflow risk.
- default GitHub comments still exposed too many raw runtime and retrieval internals.

## 3. Problem 1

Justified PR comment response permission was scored too harshly.

The product needed to distinguish:

- dangerous mutation-capable workflow posture
- write-heavy review-required workflow posture
- narrowly justified `pull-requests: write` used only to publish RepoBrain PR command response comments

## 4. Problem 2

Default diagnostics were still too noisy for partner-facing GitHub comments.

The product kept useful evidence, but raw TKY/TKYA/runtime internals, retrieval plumbing, and repeated boolean matrices were crowding the operational message.

## 5. Permission Classification Model

Sprint 92C introduced a dedicated workflow permission classifier with these classes:

- `SAFE_READ_MOSTLY`
- `JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION`
- `WRITE_HEAVY_REVIEW_REQUIRED`
- `DANGEROUS_WORKFLOW_POLICY`

`JUSTIFIED_PR_COMMENT_RESPONSE_PERMISSION` applies only when:

- `pull-requests: write` is present
- `issues: write` is present
- `contents: write` is absent
- `checks: write` is absent
- `pull_request_target` is absent
- RepoBrain no-mutation policy remains active
- permission purpose is documented or product-constrained to PR command response comments

## 6. Diagnostics Tiers

Sprint 92C standardizes three diagnostics tiers:

- compact default:
  - posted to GitHub issue and PR comments
  - developer/partner-facing
  - decision-relevant only
- verbose:
  - enabled with `RB_REPOBRAIN_VERBOSE_DIAGNOSTICS=1`
  - expanded sanitized runtime/retrieval/provenance detail
- artifact/debug:
  - full sanitized trace remains in workflow artifacts/logs

## 7. Compact LLM Block

Default comments now show:

- whether the LLM was used
- final model when used
- short reason
- token total
- downgrade yes/no with short reason when relevant

Default comments no longer show:

- remaining request counters
- reset timestamps
- prompt-budget internals
- dropped-context internals
- model-selection plumbing

## 8. Compact Runtime/Safety Block

Default comments now show:

- runtime summary
- backend summary
- fallback summary
- command scope
- compact no-mutation safety statement
- no merge/security/production approval statement

Default comments no longer show raw TKY/TKYA fields unless verbose diagnostics are enabled.

## 9. Command Output Shape Changes

- review keeps TL;DR, risk, changed files, findings, signals, notes, compact LLM, and compact runtime/safety
- ask keeps the answer, compact evidence paths, compact LLM, and compact runtime/safety
- explain keeps operational explanation plus compact LLM/runtime truth
- locate keeps route, top locations, and direct-retrieval note
- audit and score keep repository scoring substance while using compact runtime/safety by default
- verify stays informational and compact
- fix stays proposal/governance only and compact

## 10. Tests

Sprint 92C adds targeted coverage for:

- justified PR comment permission classification
- compact vs verbose diagnostics tiers
- compact LLM block
- compact runtime/safety block
- compact command output shapes
- audit/score permission scoring behavior

## 11. Live Retest

Live retest is required after merge:

- PR review / verify / fix / audit / score
- issue ask / locate / explain
- confirmation that default comments stay compact
- confirmation that justified PR comment permission is not overstated as broad write-heavy risk

## 12. Product Status

Target status after live retest:

- `PARTNER_PILOT_READY_AFTER_DIAGNOSTICS_AND_PERMISSION_CLASSIFICATION`

## 13. Non-Goals

- no TopoCore source exposure
- no runtime architecture change
- no patch/autofix enablement
- no `pull_request_target`
- no `contents: write`
- no Marketplace work
