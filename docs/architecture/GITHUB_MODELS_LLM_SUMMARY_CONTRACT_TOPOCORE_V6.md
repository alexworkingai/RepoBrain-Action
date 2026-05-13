# GitHub Models LLM Summary Contract for TopoCore v6

## 1. Purpose

Sprint 17 defines the GitHub Models LLM summary contract only.

Current truth:

- the current live provider path is GitHub Models
- the LLM remains in the RepoBrain layer
- the LLM does not move inside TopoCore v6
- the LLM does not become the final decision-maker
- TopoCore v6 remains a future target only and is not wired in this sprint

This sprint is docs-only. It does not implement adapter code, runtime routing, provider changes, or any TopoCore v6 integration.

## 2. Current LLM Runtime Baseline

The authoritative runtime linkage baseline is documented in:

- `docs/architecture/CURRENT_RUNTIME_LINKAGE_REPOBRAIN_TOPOCORE_V5_LLM_COMMUNITY.md`

That document remains the detailed source of truth. This section summarizes only the LLM facts needed for the future summary contract.

Current baseline:

- the active provider family is GitHub Models
- chat provider:
  - `repobrain.llm.github_models.GitHubModelsClient`
- embeddings provider:
  - `repobrain.llm.github_models_embeddings.GitHubModelsEmbeddingsClient`
- current defaults include:
  - `RB_LLM_PROVIDER=github_models`
  - `RB_LLM_MODEL_HIGH=openai/gpt-4.1`
  - `RB_LLM_MODEL_LOW=openai/gpt-4.1-mini`
  - `RB_EMBED_MODEL=openai/text-embedding-3-small`
- ask, review, and fix use the same provider family but different prompt and budget paths
- fix has stricter retry and fallback behavior than ask or review
- tests use fake or monkeypatched provider calls rather than live traffic

## 3. Contract Position in the Future v6 Architecture

Target flow:

`GitHub event / PR context`
-> `RepoBrain context collection`
-> `GitHub Models LLM summary generation`
-> `RepoBrain validation / normalization`
-> `RepoBrainTopoCoreV6Adapter`
-> `TopoCore v6 public facade`
-> `safe RepoBrain product output`

Boundary rules for that flow:

- GitHub Models prepares summaries
- RepoBrain validates and normalizes summaries
- TopoCore v6 evaluates typed summaries and policy payloads
- RepoBrain renders safe GitHub-facing output

## 4. LLM Responsibilities

Allowed LLM responsibilities in the future architecture:

- intent summary
- PR/diff/check summary
- evidence summary
- unknowns summary
- confidence hints
- risk hints
- review explanation draft
- fix or patch draft only under existing Fix-Lite and no-patch governance
- human-readable explanation draft

All LLM output is advisory and preparatory. It must be validated before it can influence any later adapter, policy, or product-layer decision.

## 5. LLM Non-Responsibilities

The LLM must not:

- make final TopoCore decisions
- issue safe-to-merge claims
- issue security verdicts
- approve or reject PRs
- claim full review parity
- decide autonomous patch application
- modify files
- create commits
- create branches
- create PRs
- bypass patch safety
- bypass existing no-patch governance
- expose secrets
- expose raw tokens
- expose hidden prompts
- expose internal traces
- expose governance internals
- expose raw decision internals
- expose `decide_raw`-style data to users

## 6. Summary Families

### A. IntentSummary

Purpose:

- normalize the user command and intent

Suggested fields:

- `command`
- `user_goal`
- `task_type_candidate`
- `ambiguity_level`
- `missing_user_inputs`
- `safety_notes`

### B. PullRequestContextSummary

Purpose:

- summarize PR metadata, changed files, diff scope, and check status

Suggested fields:

- `pr_state`
- `base_ref`
- `head_ref`
- `changed_files_summary`
- `diff_scope`
- `checks_summary`
- `workflow_signal_summary`
- `context_limits`

### C. EvidenceSummary

Purpose:

- separate evidence from guesses

Suggested fields:

- `confirmed_facts`
- `evidence_items`
- `evidence_gaps`
- `source_kinds`
- `confidence_hint`

### D. UnknownsSummary

Purpose:

- list missing or unavailable facts

Suggested fields:

- `unknowns`
- `missing_files_or_checks`
- `insufficient_context_reasons`
- `suggested_next_information`

### E. RiskHintsSummary

Purpose:

- capture possible risk signals without issuing a final verdict

Suggested fields:

- `risk_items`
- `risk_area`
- `severity_hint`
- `likelihood_hint`
- `evidence_link`
- `mitigation_hint`

### F. ReviewDraftSummary

Purpose:

- produce a bounded review explanation draft

Suggested fields:

- `review_focus`
- `candidate_findings`
- `evidence_links`
- `non_claims`
- `suggested_next_steps`

### G. FixDraftSummary

Purpose:

- support a future Fix-Lite and no-patch governed flow

Suggested fields:

- `fixability_hint`
- `localized_target_hint`
- `patch_candidate_present`
- `no_patch_reason`
- `patch_safety_notes`
- `grounding_notes`

## 7. Fact Classification Rules

LLM outputs must classify statements as one of:

- `confirmed`
- `inferred`
- `hypothesis`
- `unknown`

Rules:

- `confirmed` requires evidence from available RepoBrain or GitHub context
- `inferred` must identify the basis for the inference
- `hypothesis` must be clearly marked as unverified
- `unknown` must not be converted into a confident claim

## 8. Confidence Rules

Confidence is a hint, not a decision.

Allowed values:

- `high`
- `medium`
- `low`
- `unknown`

Rules:

- confidence must not override evidence
- confidence must not authorize patching
- confidence must not authorize safe-to-merge claims
- low confidence should lead to `needs_more_information` or safe no-result / no-patch behavior

## 9. Retry and Repair Rules

Future repair behavior must stay bounded:

- schema or format issue: maximum `1` LLM repair retry
- weak evidence: maximum `1` repair retry or stop with `needs_more_information`
- policy or security block: `0` retries
- adapter bug: `0` LLM retries
- insufficient GitHub data: ask the user or return a safe no-result / no-patch outcome
- provider unavailable or missing token: controlled disabled or blocked outcome

There must be no infinite retry loop.

## 10. Mapping to Future TopoCore v6 Payloads

| Summary family or signal | Likely future v6 payload concept | Mapping category | Notes |
|---|---|---|---|
| `IntentSummary` | `EngineQuery` / task type candidate | direct candidate | Intent normalization is close to query framing, but the final field shape still belongs to the adapter boundary. |
| `PullRequestContextSummary` | policy context / project or PR context payload | adapter-required | RepoBrain must normalize GitHub facts into a v6-safe context payload. |
| `EvidenceSummary` | `evidence_summary` | adapter-required | Evidence needs shaping before v6 consumption. |
| `UnknownsSummary` | missing information / `needs_more_information` signal | adapter-required | Useful as a structured stop or caution signal, but not as a direct user-visible decision on its own. |
| `RiskHintsSummary` | `risk_items` | adapter-required | Risk hints are inputs to evaluation, not final verdicts. |
| `ReviewDraftSummary` | product-level explanation draft | product-only | This is useful for RepoBrain output rendering, not as a final TopoCore decision object. |
| `FixDraftSummary` | fix governance input | product-only | It may inform fix orchestration, but it must not authorize a patch by itself. |
| checks and test signals | `verification_results` | adapter-required | RepoBrain already understands GitHub verification context and must shape it for v6. |
| repo or project structure hints | `project_audit_scorecard` or `project_audit_findings` | future/open question | Possibly useful later, but not yet part of the minimal bridge. |
| scenario alternatives | `scenario_branches` | future/open question | Worth keeping in mind for future explanation or planning flows. |

## 11. Prompt Contract Principles

Future implementation prompts should follow these principles:

- ask for structured output
- separate facts from interpretations
- require unknowns
- require evidence references where available
- forbid final verdicts
- forbid safe-to-merge and security verdicts
- forbid autonomous patch or action claims
- keep summaries compact and bounded
- never include secrets or hidden or internal data
- never rely on unsupported provider behavior

## 12. Validation Strategy for Later Sprints

Future implementation work should be validated with:

- fake provider tests
- schema-like validation tests
- malformed LLM output tests
- missing token tests
- low-confidence handling tests
- no-final-verdict tests
- no-secret and no-internal-leak tests
- fix no-patch preservation tests
- adapter fixture tests for future v6 payloads

Sprint 17 does not implement those tests. It defines the contract that later tests should enforce.

## 13. Relationship to Sprint 16

See:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`

Relationship:

- Sprint 16 defined the controlled migration blueprint
- Sprint 17 defines the LLM summary contract that should exist before adapter implementation
- Sprint 17 still does not wire TopoCore v6 into RepoBrain runtime

## 14. Explicit Non-Goals for Sprint 17

- no runtime code changes
- no prompt implementation changes
- no provider implementation changes
- no workflow changes
- no `action.yml` changes
- no `topocore_v6` dependency
- no `topocore_v6` import
- no v6 adapter implementation yet
- no shadow mode yet
- no canary yet
- no change to current v5/TKYA behavior
- no change to patch or fix behavior
- no new external community runtime behavior

## 15. Acceptance Criteria

Sprint 17 is complete only if:

- the new LLM summary contract document exists
- it clearly states GitHub Models is the current provider path
- it clearly keeps the LLM in the RepoBrain layer
- it clearly states the LLM is not the final decision-maker
- it defines summary families
- it defines fact classification rules
- it defines bounded retry and repair rules
- it maps summaries to future v6 payload concepts
- it preserves v5 as the current active runtime
- it does not claim v6 is wired
- it introduces no runtime behavior changes
