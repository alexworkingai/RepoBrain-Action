# Control Worker Request v1

Contract name: `repobrain.control_worker_request.v1`

## Purpose

Internal private-control-plane request built from a public queue marker.

## Required fields

- `contract_version`
- `request_id`
- `queue_contract_version`
- `repository_full_name`
- `repository_owner`
- `repository_name`
- `issue_number`
- `event_kind`
- `command`
- `profile`
- `source_comment_id`
- `installation_identity_marker`
- `created_at`
- `observed_at`
- `requested_by`
- `transport_mode` with value `github_app_queue`

## Optional fields

- `pull_request_number`
- `actor_login`
- `source_comment_url`
- `head_sha`
- `base_sha`
- `changed_files_summary`
- `diff_summary`
- `repository_metadata_summary`
- `workflow_run_id`
- `workflow_run_attempt`
- `capability_request`

## Public safety

This request may exist in private control repo memory or minimized logs, but if serialized publicly it must be redacted.

Do not expose:
- tokens
- private keys
- JWTs
- Authorization headers
- private TopoCore paths
- private checkout paths
- raw internal traces
