# Sprint 94D Private Control Worker + TopoCore Entrypoint

## 1. Purpose

Sprint 94D adds the private-control-side processing foundation for queued requests.

It connects:
- GitHub-native queue marker from 94C
- GitHub App installation token boundary from 94B
- private TopoCore entrypoint
- public-safe result posting

## 2. Correct scope

94D implements:
- queue marker discovery and parsing
- queue request validation
- idempotency and deduplication strategy
- TopoCore entrypoint request contract
- TopoCore response normalization
- public-safe final result rendering
- private control repo workflow template

94D does not claim:
- trusted partner beta is complete
- public developer beta is ready
- Marketplace is ready
- production, security, or legal approval

## 3. Runtime location

Worker runs only in the owner-controlled private RepoBrain control repo.

It does not run in the partner repo.
It does not require partner secrets.
It does not expose TopoCore.

## 4. GitHub App token boundary

Worker uses a GitHub App installation token minted inside the private control repo.

Rules:
- token is short-lived
- token is never printed
- token is never written to artifacts
- token is never embedded in queue marker
- token is never stored in partner repo

## 5. Queue discovery

Initial strategy:
- scan installed or allowlisted repositories for comments containing the 94C queue marker
- parse marker
- validate `contract_version`
- process only `status=queued`
- ignore completed, failed, and superseded markers
- deduplicate by `request_id`

No external database is required in 94D.
Idempotency is comment-marker-based:
- before processing `request_id`, check whether a completed or failed control-worker result marker already exists for that request

## 6. TopoCore boundary

TopoCore is a separate team and system.
RepoBrain does not implement TopoCore internals.
RepoBrain invokes a configured private TopoCore entrypoint through a stable adapter.

The adapter may call:
- a configured CLI command
- a configured Python module
- a configured private script
- or a future service inside private control infrastructure

Public `RepoBrain-Action` does not contain private TopoCore source.

## 7. TopoCore request and response

The worker builds a sanitized EngineRequest-like payload from:
- queue marker
- repository identity
- PR or issue context
- command and profile
- fetched diff and metadata when available and bounded

The worker receives TopoCore result and maps it into public-safe fields:
- score
- verdict
- blockers
- warnings
- evidence_summary
- profile
- backend
- fallback
- command
- request_id
- contract_version
- capability markers when provided

Not included:
- raw traces
- `decide_raw`
- private compression stats
- private paths
- TopoCore internal chain data

## 8. Failure behavior

If worker cannot process request:
- post a public-safe failed result when possible
- include a stable error code
- do not expose tokens, private paths, or raw exceptions with secrets

Failure statuses:
- `CONTROL_WORKER_GITHUB_TOKEN_MISSING`
- `CONTROL_WORKER_QUEUE_SCAN_FAILED`
- `CONTROL_WORKER_QUEUE_MARKER_INVALID`
- `CONTROL_WORKER_REQUEST_ALREADY_PROCESSED`
- `CONTROL_WORKER_REPO_NOT_INSTALLED`
- `CONTROL_WORKER_PERMISSION_MISSING`
- `TOPOCORE_ENTRYPOINT_NOT_CONFIGURED`
- `TOPOCORE_ENTRYPOINT_FAILED`
- `TOPOCORE_RESPONSE_INVALID`
- `RESULT_POST_FAILED`
- `CONTROL_WORKER_SECRET_LEAKAGE_GUARD`

## 9. Next sprint

Sprint 94E performs trusted partner beta validation on selected installed GitHub App repositories such as:
- `alexworkingai/Elen-MCP-v.2.2.0`
- one additional trusted partner repository chosen by the owner at validation time

94E validates the complete path live.

## 10. Status

Expected:
- `SPRINT_94D_PRIVATE_CONTROL_WORKER_TOPOCORE_ENTRYPOINT_READY`

Not:
- `TRUSTED_PARTNER_BETA_READY`
