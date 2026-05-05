# RepoBrain Current Capabilities Matrix

This matrix reflects accepted product behavior after Sprint 59.

## Execution Surfaces

| Surface | Ask | Review | Fix | Help | Notes |
|---|---|---|---|---|---|
| GitHub mode (`issue_comment` PR flow) | Supported | Supported | Supported | Supported | Primary runtime surface with readiness/audit/evidence artifacts. |
| External GitHub mode foundation (`workflow_call` reusable path) | Supported | Supported (bounded read-only Review Candidate) | Supported (bounded Fix-Lite suggestion-only) | Supported | Third-party GitHub-native bounded foundation using reusable workflow and explicit command boundary. |
| External CLI mode (`scripts/run_github.py --mode external`) | Supported | Unsupported (explicit block) | Unsupported (explicit block) | N/A (use CLI docs) | Ask-first trial path for third-party repo execution without full PR-native runtime. |
| MCP surface (`scripts/run_mcp_surface.py`) | Supported | Unsupported (explicit block) | Unsupported (explicit block) | N/A (request/response contract) | Thin ask-first structured adapter over accepted external ask runtime. |

## Profile Control Plane

| Capability | Status | Notes |
|---|---|---|
| Command-level `--profile cheap|balanced|premium` | Supported | User-facing for ask/review/fix in GitHub mode. |
| Default profile | `balanced` | Preserved when no command override provided. |
| Review/fix cheap guardrail | Supported | Requested `cheap` normalized to used `balanced` with explicit policy truth. |

## Readiness / Onboarding

| Capability | Status | Notes |
|---|---|---|
| Readiness contract v2 | Supported | Operator-readable status + reason + next steps. |
| Missing vs invalid config distinction | Supported | Includes invalid App ID classification. |
| Selected-repo mismatch detection | Supported | Explicitly surfaced in readiness truth. |

## External Trial Status

| Trial | Repository | Outcome | Interpretation |
|---|---|---|---|
| Trial #01 | `alexworkingai/Elen-MCP-v.2.2.0` | External ask success; external review now bounded to read-only Review Candidate; external fix now bounded to Fix-Lite suggestion-only | External execution path validated; full external command parity and autofix are still not delivered. |
