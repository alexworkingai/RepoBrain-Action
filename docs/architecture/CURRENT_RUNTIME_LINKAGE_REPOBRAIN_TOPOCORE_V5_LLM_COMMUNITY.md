# Current Runtime Linkage: RepoBrain, TopoCore v5, LLM, and Community Surface

## 1. Purpose

This document records the current RepoBrain-Action runtime wiring before any TopoCore v6 integration work starts.

It is intentionally evidence-based and reflects the code paths that are active today in:

- `.github/workflows/repobrain.yml`
- `action.yml`
- `scripts/run_github.py`
- `repobrain/github_flow.py`
- `repobrain/tky_local.py`
- `repobrain/tkya/engine.py`
- `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
- `repobrain/llm/github_models.py`
- `repobrain-community/templates/repobrain.yml`
- `repobrain-community/.github/workflows/repobrain_external_foundation.yml`

This is a current-state document, not an integration plan. TopoCore v6 is a future integration target and is not described here as active runtime wiring unless RepoBrain-Action code proves it.

See also:

- `docs/architecture/TOPOCORE_V5_TO_V6_CONTROLLED_MIGRATION_BLUEPRINT.md`

## 2. Repository Roles

### RepoBrain-Action

`RepoBrain-Action` is the current primary runtime repository for:

- GitHub Action entrypoints
- command parsing and routing
- TKYA/TopoCore engine bridging
- LLM-driven ask/review/fix orchestration
- patch safety and patch-governance logic
- PR comment and check-run publishing

In current runtime terms, this is the repository that owns the private primary GitHub-mode behavior implemented through `.github/workflows/repobrain.yml`, `action.yml`, `scripts/run_github.py`, and `repobrain/github_flow.py`.

### repobrain-community

`repobrain-community` owns the current public external GitHub foundation surface rather than the private primary RepoBrain runtime. RepoBrain-Action docs already describe this split in:

- `docs/EXTERNAL_MODE.md`
- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`

The public external install/template host lives in:

- `repobrain-community/templates/repobrain.yml`
- `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`

### elen-mcp-prod_v2

`elen-mcp-prod_v2` is a validation-only repository, not a source of current product/runtime truth. RepoBrain-Action already classifies it that way in:

- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/refactor/REFACTOR_PHASE_CLOSEOUT.md`
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`

It matters as a validation surface and historical external-trial reference, but it is not part of the live RepoBrain runtime path.

### topocore v6 private repository

TopoCore v6 currently lives outside RepoBrain-Action as the private repository:

- `https://github.com/alexworkingai/topocore`
- baseline tag: `v0.30.0-rc1`

That repository is the future v6 foundation source of truth, but RepoBrain-Action current runtime code does not yet wire into `topocore_v6`. A repository-wide search for:

- `topocore_v6`
- `create_topocore`
- `decide_external`
- `ExternalDecisionView`

does not show active RepoBrain-Action runtime wiring to TopoCore v6.

## 3. Current High-Level Flow

The current primary GitHub runtime flow is:

`GitHub event`
-> `.github/workflows/repobrain.yml`
-> `action.yml`
-> `python scripts/run_github.py`
-> `repobrain.github_flow.run_github_flow(...)`
-> command parsing via `repobrain.commands.parse_command(...)`
-> command-specific build path
-> TKYA / LLM / patch-safety / verification helpers
-> markdown rendering
-> PR comment and PR check-run publication

At a high level:

1. GitHub receives an `issue_comment` or `workflow_dispatch` event.
2. `.github/workflows/repobrain.yml` checks whether the comment starts with `/repobrain`.
3. The workflow resolves which SHA to check out.
4. `action.yml` installs the package in editable mode and runs `scripts/run_github.py`.
5. `scripts/run_github.py` delegates GitHub mode to `repobrain.github_flow.run_github_flow(...)`.
6. `repobrain/github_flow.py` parses the command and routes to:
   - `_build_qa_markdown(...)`
   - `_build_review_markdown(...)`
   - `_build_verify_markdown(...)`
7. Those paths call TKYA, retrieval/index helpers, GitHub Models LLM calls, verification helpers, and patch-safety helpers as needed.
8. Output is rendered through `repobrain/output_md.py`.
9. The result is posted as:
   - a PR/issue comment through `GitHubClient.create_issue_comment(...)`
   - a PR check-run payload through `build_check_run_payload(...)`
   - optionally deferred check publication through `.github/workflows/repobrain_checks_publisher.yml`

## 4. GitHub Workflows and Command Routing

### 4.1 Primary workflow triggers

The active primary workflow is `.github/workflows/repobrain.yml`.

It triggers on:

- `issue_comment`
- `workflow_dispatch`

It does not currently trigger on `pull_request` directly. PR handling happens through comments on PR discussions, because GitHub PR discussions arrive through the `issue_comment` event.

### 4.2 Deferred check publisher

`.github/workflows/repobrain_checks_publisher.yml` is a separate workflow triggered by:

- `workflow_run` for workflow `RepoBrain`

Its purpose is deferred PR check publication from the artifact payload produced by the main workflow. It reads:

- `artifacts/check-payload/check_run_payload.json`

and then creates the check run from that payload. This means the checks publisher does participate in deferred check publication.

### 4.3 Checkout behavior

Both the primary RepoBrain workflow and the community external workflow contain explicit ref-resolution logic.

In `.github/workflows/repobrain.yml`:

- same-repo open PR comment -> checkout PR `head.sha`
- fork PR comment -> stay on workflow/default runtime SHA
- closed PR comment -> stay on workflow/default runtime SHA

This means runtime code is not always executed from `main`. For same-repo open PR comment flows, RepoBrain executes against the PR head SHA. For fork or closed PR cases, it stays on the default workflow runtime SHA.

### 4.4 action.yml runtime handoff

`action.yml` is a composite action. It:

- sets up Python 3.11
- installs RepoBrain with `pip install -e ".[dev]"`
- runs `python scripts/run_github.py`

It also hard-wires important runtime defaults, including:

- `RB_TKYA_BACKEND=v5`
- `RB_TKYA_ALLOW_REMOTE=0`
- `RB_TKYA_STRICT=0`
- `RB_DISABLE_INTERNAL_REACTIONS=1`

### 4.5 Slash-command detection

There are two layers of slash-command detection:

1. Workflow gate in `.github/workflows/repobrain.yml`
   - job runs only when the comment body starts with `/repobrain`
2. Parser in `repobrain/commands.py`
   - `parse_command(text)` requires the first token to be `/repobrain`

### 4.6 Primary command routing

Current primary command parsing in `repobrain/commands.py` supports:

- `help`
- `ask`
- `locate`
- `explain`
- `review`
- `verify`
- `fix`

`doctor` is not part of `repobrain.commands.parse_command(...)`, so it is not a primary RepoBrain-Action GitHub-mode command in the current private runtime path.

Inside `repobrain.github_flow.run_github_flow(...)`, parsed commands are routed as follows:

- `help` -> help text
- `review` / `fix` -> `_build_review_markdown(...)`
- `verify` -> `_build_verify_markdown(...)`
- `ask` / `locate` / `explain` -> `_build_qa_markdown(...)`

### 4.7 Where PR comments are produced

PR/issue comments are produced by:

- `repobrain.github_flow.GitHubClient.create_issue_comment(...)`
- `repobrain.github_publisher.publish_comment(...)`

Markdown bodies are prepared by:

- `render_answer_markdown(...)`
- `render_review_markdown(...)`
- `render_patch_markdown(...)`
- `render_refuse_markdown(...)`
- `render_wait_markdown(...)`
- `render_error_markdown(...)`
- `format_verify_comment(...)`

### 4.8 Where check runs are produced

PR check runs are built/published by:

- `_publish_pr_check_run(...)` in `repobrain/github_flow.py`
- `build_check_run_payload(...)` in `repobrain/github_publisher.py`
- `publish_check_run(...)` in `repobrain/github_publisher.py`

`repobrain_checks_publisher.yml` is the deferred workflow that materializes those payloads into visible GitHub checks after the main RepoBrain run finishes.

## 5. Current TopoCore v5 / TKYA Path

### 5.1 Embedded vendor v5 is still present

Yes. TopoCore v5 is still embedded as a vendor file in RepoBrain-Action:

- `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`

The primary runtime also explicitly sets:

- `RB_TKYA_BACKEND=v5`

through `action.yml`, so current GitHub-mode runtime is configured to prefer the v5 vendor backend.

### 5.2 Modules that bridge or wrap the vendor engine

The current v5/TKYA path is:

- `repobrain/tky_local.py`
- `repobrain/tky_engine.py`
- `repobrain/tkya/engine.py`
- `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`

`repobrain/tky_local.py`:

- builds `EngineRequest`
- converts retrieval candidates into `EngineCandidate`
- calls `engine.decide(req)` through `get_engine()`
- converts the result back into `TKYResult`

`repobrain/tky_engine.py` defines the canonical local contract:

- `EngineCandidate`
- `EngineQuery`
- `EngineRequest`
- `EngineSecurity`
- `EngineDecision`
- `TKYEngine` protocol

`repobrain/tkya/engine.py`:

- selects backend from `RB_TKYA_BACKEND`
- defaults to `v5` when the vendor file exists
- loads the vendor file through `importlib`
- labels the selected engine with `describe_engine_instance(...)`
- installs remote guards unless `RB_TKYA_ALLOW_REMOTE=1`

The vendor class currently used is:

- `TopoCoreTCXv5AdvanceCASGit`

### 5.3 Diagnostics and current contract shape

Current TKYA diagnostics are still represented through:

- `EngineDecision`
- `TKYResult`
- `compression_stats`

This is not a TopoCore v6 shape yet.

The current contract still includes:

- `route`
- `selected_chunk_ids`
- `compression_stats`
- `rationale`
- `execution_mode`
- `llm_intent`
- `llm_decision_reason_short`
- `llm_decision_reason_code`

### 5.4 Compression stats and hash-only trace

Yes, `compression_stats` is still part of the current contract.

Evidence:

- `repobrain/tky_engine.py` includes `compression_stats` on `EngineDecision`
- `repobrain/tky_provider.py` includes `compression_stats` on `TKYResult`
- `repobrain/tky_local.py` forwards `compression_stats` from engine decision into `TKYResult`
- the vendor v5 file contains trace schema logic and hash-only trace packing
- `tests/test_legacy_runtime_removed_vendor.py` asserts trace schema fields and checks that raw query text does not appear in trace
- `tests/test_tkya_evidence_pack.py` asserts public-safe hash-only evidence-pack behavior

So the current RepoBrain contract still expects both:

- compression statistics
- hash-only trace-style diagnostics

### 5.5 Contract and regression guards around TKYA / TopoCore

The current TKYA/TopoCore contract is guarded by:

- `tests/test_tkya_engine.py`
- `tests/test_legacy_runtime_removed_vendor.py`
- `tests/test_tkya_evidence_pack.py`
- `tests/test_tkya_legacy_references_removed.py`
- `tests/test_contract_guard.py`
- `scripts/check_tkya_contract_guard.py`
- `docs/tkya_contract.md`
- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`

### 5.6 Is TopoCore v6 used anywhere in RepoBrain-Action today?

No evidence of active TopoCore v6 wiring was found in RepoBrain-Action current runtime code.

A repository search did not show active runtime references to:

- `topocore_v6`
- `create_topocore`
- `decide_external`
- `ExternalDecisionView`

Current RepoBrain runtime remains wired to:

- the TKYA local bridge
- the v5 vendor engine
- the lite fallback backend

not to TopoCore v6.

## 6. Current LLM Provider / Model Layer

### 6.1 Current provider family in live GitHub runtime

The current live GitHub Action LLM path is GitHub Models, not a direct OpenAI SDK integration.

Evidence:

- workflow env sets `RB_LLM_PROVIDER=github_models`
- `repobrain.github_flow._llm_runtime_policy(...)` disables the LLM layer unless the provider is exactly `github_models`
- `repobrain/github_flow.py` imports and instantiates:
  - `GitHubModelsClient`
  - `GitHubModelsEmbeddingsClient`

### 6.2 Provider classes and endpoints

Chat/completions path:

- file: `repobrain/llm/github_models.py`
- class: `GitHubModelsClient`
- endpoint: `https://models.github.ai/inference/chat/completions`

Embeddings path:

- file: `repobrain/llm/github_models_embeddings.py`
- class: `GitHubModelsEmbeddingsClient`
- endpoint: `https://models.github.ai/inference/embeddings`

### 6.3 Environment variables and model knobs

Current model/provider configuration is defined in:

- `repobrain/config.py`
- `docs/env_reference.md`

Key variables in current runtime include:

- `GITHUB_TOKEN`
- `RB_LLM_ENABLED`
- `RB_LLM_PROVIDER`
- `RB_LLM_MODEL_HIGH`
- `RB_LLM_MODEL_LOW`
- `RB_EMBED_ENABLED`
- `RB_EMBED_MODEL`
- `RB_LLM_MAX_INPUT_TOKENS`
- `RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL`
- `RB_LLM_MAX_INPUT_TOKENS_PATCH`
- `RB_LLM_MAX_OUTPUT_TOKENS_*`
- `RB_LLM_EXECUTION_PROFILE`
- governor/quota knobs under `RB_AI_*`

The current workflow defaults set:

- `RB_LLM_MODEL_HIGH=openai/gpt-4.1`
- `RB_LLM_MODEL_LOW=openai/gpt-4.1-mini`
- `RB_EMBED_MODEL=openai/text-embedding-3-small`

These are used through GitHub Models, so the model IDs are OpenAI-family names while the provider transport is GitHub Models.

### 6.4 Which files call the LLM provider

Direct chat-model call path:

- `repobrain/github_flow.py`

Direct embeddings call paths:

- `repobrain/github_flow.py`
- `repobrain/index_store.py`

Prompt shaping and token budgeting live in:

- `repobrain/llm/prompts.py`
- `repobrain/llm/model_selector.py`

### 6.5 Which commands use LLM output

Current command behavior is split:

- `help`: no LLM
- `verify`: builds verification report from checks/status/workflow data, not from GitHub Models synthesis as its primary output path
- `ask` / `locate` / `explain`: may use the LLM path in `_build_qa_markdown(...)`
- `review` / `fix`: use LLM synthesis in `_build_review_markdown(...)`

So `ask`, `review`, and `fix` all share the same current provider family:

- GitHub Models

but they do not share the same prompt/budget path:

- ask/explain/locate use the QA prompt path
- review uses review synthesis prompts
- fix uses patch-generation prompts with stricter output constraints

### 6.6 Missing token behavior

Missing GitHub token is handled explicitly.

Evidence:

- `repobrain/github_flow.py` returns LLM meta with `missing_github_token`
- `repobrain/index_store.py` returns disabled embeddings metadata with `missing_github_token`
- `run_github_flow(...)` requires `GITHUB_TOKEN` when `dry_run=False`

Current behavior is controlled block/skip, not hidden fallback to another provider.

### 6.7 Timeout, retry, and fallback behavior

Current GitHub Models timeouts in provider clients:

- chat: `timeout=(5, 30)`
- embeddings: `timeout=(5, 30)`

Primary fix-path retries:

- `_attempt_model(... retry_count=3 if is_fix_path else 0)`

Current fix path may also fall back to the alternate model when the primary provider error is eligible for fallback.

This means:

- ask/review normally do not get the same retry count as fix
- fix is the most defensive LLM path

### 6.8 Test doubles / mocks

Tests use monkeypatched fake provider behavior rather than live provider calls.

Examples include:

- `tests/test_issue_comment_llm_policy.py`
- `tests/test_review_governor_tuning.py`
- `tests/test_fix_llm_fallback.py`
- `tests/test_fix_llm_http_debug_artifact.py`
- `tests/test_embeddings_client_parsing.py`
- `tests/test_github_models_client_parsing.py`

These tests patch:

- `GitHubModelsClient.chat`
- `GitHubModelsEmbeddingsClient.embed`

### 6.9 What is not proven

The current code makes GitHub Models very clear for the active GitHub workflow runtime.

What is less clear from the live path is whether RepoBrain intends to keep a broader multi-provider abstraction later, because:

- `RB_LLM_PROVIDER` exists as a config field
- `_llm_runtime_policy(...)` currently disables any non-`github_models` provider rather than routing to a second provider implementation

So the current runtime truth is:

- GitHub Models is the active provider path
- no second live provider implementation is currently evidenced in the main GitHub runtime flow

## 7. Current Fix Safety Stack

### 7.1 High-level shape

Current patch/fix safety is implemented through:

- `repobrain/fix/patch_extract.py`
- `repobrain/fix/patch_guard.py`
- `repobrain/patch_targeting.py`
- `repobrain/patch_validator.py`
- `repobrain/patch_governance.py`
- `repobrain/output_md.py`
- review/fix orchestration inside `repobrain/github_flow.py`

### 7.2 How patch text is constrained

The fix prompt path in `repobrain/llm/prompts.py` explicitly asks for only one of:

- a unified diff in a ```diff fence
- exactly `NO_PATCH`
- a strict JSON patch envelope only if the provider requires it

It also explicitly says:

- no prose before/after diff
- no explanations
- no secrets

### 7.3 How patch extraction works

`repobrain/fix/patch_extract.py`:

- normalizes output
- accepts diff-fence payloads
- accepts raw unified diff payloads
- accepts JSON patch envelopes
- accepts `NO_PATCH`
- otherwise returns `PATCH_MISSING`

It does not treat generic prose as an acceptable patch.

### 7.4 How placeholder/generic output is blocked

`repobrain/fix/patch_guard.py` blocks:

- placeholder/template-style patch text
- generic “here is the patch/apply this patch” prose without real diff content

It emits reason codes such as:

- `PATCH_PLACEHOLDER_DETECTED`
- `PATCH_GENERIC_TEXT`

### 7.5 How localized target selection works

`repobrain/patch_targeting.py` narrows patch scope to likely fixable files/hunks using:

- changed file metadata
- diff hunk structure
- review evidence paths
- query/file matching

It downranks or blocks broad/non-patchable contexts such as:

- docs-only paths
- workflow/config-style paths without localized evidence
- broad PR surfaces without evidence-backed localization

This is the current high-level localization gate for fix.

### 7.6 How patch grounding/validation works

`repobrain/patch_validator.py` validates that a candidate patch:

- is a unified diff
- names touched files
- is not placeholder content
- stays within the PR changed-file set for fix mode

It can fail with reason codes such as:

- `INVALID_PATCH_FORMAT`
- `PATCH_WITHOUT_TOUCHED_FILES`
- `PLACEHOLDER_PATCH`
- `PATCH_NOT_GROUNDED_IN_PR_FILES`

### 7.7 How safe no_patch is produced

Safe `no_patch` is a first-class outcome, not an error-only fallback.

Current review/fix orchestration in `repobrain/github_flow.py` explicitly emits safe no-patch outcomes when:

- no localized evidence-backed target is found
- placeholder/generic patch output is rejected early
- provider output does not yield a grounded diff
- validation fails

`repobrain/output_md.py` renders the primary private fix UI with:

- `### 🛠️ Patch operation`

and the tests in:

- `tests/test_fix_no_patch_rendering.py`
- `tests/test_fix_governance_localized_evidence.py`

guard safe no-patch phrasing and localized-evidence rules.

### 7.8 What prevents actual patch apply / file modification / push / PR creation

Current protection is a combination of:

1. workflow defaults
   - `.github/workflows/repobrain.yml` sets:
     - `RB_APPLY_PATCH=0`
     - `RB_CREATE_PR=0`
     - `RB_TRUSTED_CONTEXT=0`
2. runtime gates in `repobrain/github_flow.py`
   - `_maybe_apply_patch(...)` returns immediately when:
     - `RB_APPLY_PATCH=0`
     - or `RB_TRUSTED_CONTEXT=0`
   - `_maybe_create_patch_pr(...)` returns immediately when:
     - `RB_CREATE_PR=0`
     - or patch was not auto-applied
     - or `RB_TRUSTED_CONTEXT=0`
3. patch extraction/guarding/grounding gates before apply is even considered

So current primary baseline does not claim automatic patch application as the normal workflow behavior. The code contains an opt-in auto-apply path, but the live workflow baseline disables it.

## 8. repobrain-community External Foundation Linkage

### 8.1 What repobrain-community owns

Current ownership split is explicit in RepoBrain-Action docs:

- `repobrain-community` owns the canonical public external GitHub runtime host
- `repobrain-community` owns the reusable workflow host
- `repobrain-community` owns the canonical public install template

Evidence:

- `docs/EXTERNAL_MODE.md`
- `docs/REPO_BOUNDARY_CONTRACT.md`
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`
- `tests/test_external_github_foundation_workflow.py`

### 8.2 How external users are expected to install/use it

External GitHub users are expected to use:

- `repobrain-community/templates/repobrain.yml`

That template delegates to:

- `alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main`

So the external GitHub surface is intentionally hosted outside RepoBrain-Action.

### 8.3 What RepoBrain-Action no longer owns

RepoBrain-Action no longer owns:

- the canonical public external GitHub workflow host
- the canonical public install template
- the current public external GitHub runtime contract

RepoBrain-Action still owns:

- the primary/private GitHub runtime
- core docs/tests/current truth around TKYA, routing, fix safety, and regression coverage

### 8.4 Current external command truth

Current external foundation command truth in `repobrain-community` is:

- `help`
- `doctor`
- `ask`
- `review`
- `fix`

But the external meanings are intentionally bounded:

- `review` -> bounded read-only Review Candidate
- `fix` -> bounded Fix-Lite Candidate manual-only patch suggestion

The community reusable workflow explicitly renders and audits:

- `## RepoBrain Review Candidate`
- `## RepoBrain Fix-Lite Candidate`
- `No patch was applied. No files were modified.`

### 8.5 External review/fix boundaries

The current external foundation does not claim:

- full review parity with the private primary runtime
- autofix
- patch application
- file modification
- commit creation
- branch push
- PR creation
- security verdicts

That boundary is explicit both in RepoBrain-Action docs and in the community reusable workflow implementation.

## 9. Current External vs Primary Contract Split

### 9.1 Primary RepoBrain-Action PR UI

The private primary RepoBrain-Action runtime currently renders richer private-mode PR surfaces, including:

- `### ✅ PR Review`
- `### 🛠️ Patch operation`

This is the GitHub-mode path produced through `repobrain/output_md.py` and `repobrain/github_flow.py`.

### 9.2 External public foundation UI

The public external foundation hosted through `repobrain-community` uses bounded product labels:

- `Review Candidate`
- `Fix-Lite Candidate`

It also makes the no-action guarantee explicit:

- `No patch was applied. No files were modified.`

### 9.3 Why the split matters

Current private primary mode is closer to the full RepoBrain internal runtime path:

- PR metadata
- retrieval/indexing
- TKYA/TopoCore path
- GitHub Models synthesis
- verification helpers
- patch safety/governance stack
- check-run publishing

Current external mode is deliberately product-shaped and narrower:

- bounded visible PR context
- read-only Review Candidate
- manual-only Fix-Lite Candidate
- no internal patch execution path

## 10. What TopoCore v6 Will Change Later

TopoCore v6 is not active in RepoBrain-Action current runtime wiring.

The likely future integration target is:

`RepoBrain adapter`
-> `EngineRequest` / policy payload construction
-> `topocore_v6` public facade
-> safe RepoBrain mapping of result fields

At a high level, that later integration would likely replace or wrap the current:

- local TKYA bridge
- vendor v5 engine contract
- v5-flavored compression/trace contract

with a v6 public-facade path such as:

- `create_topocore()`
- safe facade call
- safe RepoBrain-side mapping into private primary surfaces and external bounded surfaces

This is future-state only. Nothing in current RepoBrain-Action runtime proves that this integration is already active.

## 11. Open Questions for the Next Integration Sprint

1. Should TopoCore v6 first replace the current `ask`/QA TKYA path, or should review/fix governance paths move first?
2. What is the private dependency/install strategy for bringing `topocore` into RepoBrain-Action CI/GitHub Action runtime without breaking the current private baseline?
3. Which current TKYA/TopoCore v5 outputs map directly into TopoCore v6 typed summaries, and which require an explicit adapter layer?
4. How should current `compression_stats`, hash-only trace, and evidence-pack fields map into v6-style typed summaries and safe outputs?
5. Should the first v6 integration target feed only private primary mode, or also prepare the later external bounded mapping?
6. Although the active provider path is clearly GitHub Models today, should future integration keep that provider assumption fixed or make the control-plane/provider split more explicit?

## 12. Evidence Index

Key files inspected for this document:

- `.github/workflows/repobrain.yml`
  - primary GitHub runtime trigger surface, checkout logic, env defaults
- `.github/workflows/repobrain_checks_publisher.yml`
  - deferred check-run publisher
- `action.yml`
  - composite action handoff into Python runtime and TKYA backend defaults
- `scripts/run_github.py`
  - GitHub-mode entrypoint
- `repobrain/github_flow.py`
  - central runtime orchestration, command routing, LLM/TKYA/fix/check-run wiring
- `repobrain/commands.py`
  - slash-command parser and supported private primary commands
- `repobrain/tky_local.py`
  - bridge from retrieval candidates into local TKYA engine request
- `repobrain/tky_engine.py`
  - engine request/decision contract
- `repobrain/tkya/engine.py`
  - backend selection, vendor loading, remote guards
- `repobrain::tkya::vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`
  - embedded v5 vendor runtime
- `repobrain/tky_provider.py`
  - `TKYResult` contract still used by RepoBrain
- `repobrain/llm/github_models.py`
  - current chat-model provider path
- `repobrain/llm/github_models_embeddings.py`
  - current embeddings provider path
- `repobrain/llm/model_selector.py`
  - current model tier selection
- `repobrain/llm/prompts.py`
  - prompt constraints and patch-format constraints
- `repobrain/index_store.py`
  - embeddings-based index path
- `repobrain/fix/patch_extract.py`
  - patch extraction contract
- `repobrain/fix/patch_guard.py`
  - placeholder/generic patch rejection
- `repobrain/patch_targeting.py`
  - localized target narrowing
- `repobrain/patch_validator.py`
  - patch grounding validation
- `repobrain/patch_governance.py`
  - safe governance interpretation of patch outcomes
- `repobrain/output_md.py`
  - private primary markdown contract (`PR Review`, `Patch operation`)
- `tests/test_tkya_engine.py`
  - TKYA backend-selection and remote-guard coverage
- `tests/test_legacy_runtime_removed_vendor.py`
  - vendor-v5 contract and trace/compression evidence
- `tests/test_tkya_evidence_pack.py`
  - public-safe evidence-pack behavior
- `tests/test_patch_extract.py`
  - patch extraction regression coverage
- `tests/test_patch_guard.py`
  - generic/placeholder patch guard coverage
- `tests/test_patch_targeting.py`
  - localized patch targeting coverage
- `tests/test_patch_validator.py`
  - patch grounding coverage
- `tests/test_fix_no_patch_rendering.py`
  - safe no-patch rendering
- `tests/test_fix_governance_localized_evidence.py`
  - localized-evidence enforcement for fix
- `docs/REPO_BOUNDARY_CONTRACT.md`
  - current repo-role and ownership split
- `docs/refactor/SPRINT_8_RUNTIME_ENTRYPOINT_DEPENDENCY_MAP.md`
  - current dependency map and ownership model
- `docs/EXTERNAL_MODE.md`
  - current public external GitHub foundation contract
- `repobrain-community/templates/repobrain.yml`
  - canonical public install template
- `repobrain-community/.github/workflows/repobrain_external_foundation.yml`
  - current public external workflow host and bounded external command contract
