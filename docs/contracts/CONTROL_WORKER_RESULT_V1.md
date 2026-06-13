# Control Worker Result v1

Contract name: `repobrain.control_worker_result.v1`

## Purpose

Public-safe result produced after private TopoCore processing.

## Required fields

- `contract_version`
- `request_id`
- `status` with value `completed` or `failed`
- `command`
- `profile`
- `repository_full_name`
- `issue_number`
- `backend`
- `fallback`
- `blockers_summary`
- `warnings_summary`
- `evidence_summary`
- `public_notes`
- `safety_footer`
- `processed_at`
- `producer` with value `RepoBrain private control worker`

## Optional fields

- `pull_request_number`
- `score`
- `verdict`
- `error_code`
- `capability_markers`

## Must not include

- tokens
- private key
- installation token
- raw JWT
- Authorization
- TopoCore path
- TopoCore source
- private checkout path
- `decide_raw`
- internal trace
- raw prompt
- LLM chain
- compression internals
