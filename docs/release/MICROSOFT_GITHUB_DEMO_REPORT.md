# Microsoft/GitHub Demo Report

## 1. Executive Positioning

RepoBrain is a GitHub-native Repository Intelligence and Quality Scoring Platform.
It is not merely an AI PR reviewer.
It is not an IDE coding assistant.
It is not an LLM reseller.
It uses a BYO-LLM and user-paid LLM model with a private TopoCore v6-powered product strategy.

## 2. Problem

Repositories lack a consistent, evidence-grounded, GitHub-native quality and readiness scoring layer.

Typical gaps:

- repository health is fragmented across CI, docs, security tooling, code review, and tribal knowledge
- PR review surfaces do not provide whole-repository maturity scoring
- generic LLM coding tools do not produce a stable governance or audit score

## 3. RepoBrain Solution

RepoBrain provides:

- `/repobrain audit`
- a 100-point score
- category breakdown
- evidence references
- critical blockers
- top improvements
- a 30/60/90-day roadmap
- `/repobrain score` compact score summary
- `/repobrain doctor` and `/repobrain status` diagnostics
- `/repobrain verify` informational checks
- `/repobrain fix` safe proposal and governance guidance

## 4. Differentiation

Compared with Copilot or Cursor:

- RepoBrain is repository governance and scoring, not IDE autocomplete

Compared with CodeRabbit-style PR review:

- RepoBrain covers whole-repository audit and readiness, not only PR commentary

Compared with autonomous agents:

- RepoBrain prioritizes safe, evidence-bound governance and no-mutation behavior over uncontrolled action-taking

## 5. GitHub/Microsoft Fit

- GitHub Actions-native workflow surface
- GitHub Models-compatible direction
- GitHub Enterprise-compatible direction
- permission-minimal workflow posture
- auditability and evidence-grounded output
- BYO-LLM and user-paid provider model
- private high-value TopoCore engine boundary
- selected partner path can now prefer installed private package mode instead of source checkout

## 6. Current Product Proof

Current proof points:

- external Elen-MCP pilot is live
- command matrix passed
- `/repobrain audit` live result after Sprint 82 private capability wiring:
  - static baseline: `78 / 100` `GOOD`
  - accepted `v6`-enriched result: `77 / 100` `GOOD`
  - backend resolved: `v6`
  - fallback used: `no`
- `/repobrain score` live result after Sprint 83 UX hardening:
  - final score: `77 / 100` `GOOD`
  - backend resolved: `v6`
  - compact summary uses the same guarded audit engine
- `/repobrain doctor` live result after Sprint 82 follow-up truth fix: `PASS`
- `/repobrain status` live result after Sprint 82 follow-up truth fix: `success`
- Sprint 84 live public-ready smoke on Elen-MCP kept `audit` and `score` in real `v6`-enriched mode while `doctor` and `status` truthfully reported controlled `private_checkout` runtime mode
- no patch/autofix
- no v5
- no `repobrain-community`
- private TopoCore v6 boundary preserved
- Sprint 81 adds a safe RepoBrain-side `topocore.audit_score.v1` contract
- Sprint 82 adds and proves a real private `run_audit_score_v1` capability behind that contract without exposing TopoCore source

## 7. Strategic Roadmap

Near-term roadmap:

- benchmark calibration
- safe v6 audit scoring contract adoption
- live v6-backed scoring rollout through the private capability when runtime packaging and contract acceptance succeed
- `/repobrain score` is now implemented as a compact summary of the same guarded audit engine
- private non-source TopoCore distribution strategy
- selected partner testing distribution gate now prefers installed private package mode with explicit readable-wheel caveat
- public visibility approval
- Marketplace preparation later

## 8. What We Want From Microsoft/GitHub Attention

We are looking for:

- technical feedback
- ecosystem fit validation
- GitHub Models and Actions alignment feedback
- partner or incubation discussion if the fit is strong
- security and distribution guidance

This report does not claim Microsoft approval, GitHub approval, or an official partnership.

## 9. Safety And Limitations

- no patch/autofix
- no repository mutation
- no merge approval claim
- no security approval claim
- current audit is an MVP deterministic scorer, not formal certification
- the Sprint 81 and Sprint 82 contract path does not imply live `v6` enrichment unless a real private capability is actually invoked and accepted
- TopoCore v6 remains private and is not distributed through this report

Sprint 83 makes the audit demo more partner-ready by reducing `[redacted-path]` noise, preserving safe repo-relative evidence paths, and shipping `/repobrain score` as a compact view of the same guarded engine.
