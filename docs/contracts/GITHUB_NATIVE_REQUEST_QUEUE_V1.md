# GitHub-native Request Queue Contract v1

Contract name: `repobrain.github_native_request_queue.v1`

## 1. Purpose

The queue marker allows the future private control worker to discover a pending RepoBrain request using GitHub APIs and a GitHub App installation token.

## 2. Transport location

Initial 94C queue transport:
- GitHub Issue and PR comments

Do not use:
- external API
- domain
- `hosted_api`
- partner secrets
- GitHub Actions artifacts as a required 94C dependency

## 3. Marker format

Use a machine-readable marker embedded in a GitHub comment.

Preferred format:

```html
<!-- repobrain:queue:v1
{
  "contract_version": "repobrain.github_native_request_queue.v1",
  "request_id": "rbq_example",
  "status": "queued",
  "command": "score",
  "profile": "partner-pilot",
  "repository_full_name": "owner/repo",
  "repository_id_marker": "123456",
  "event_kind": "issue",
  "issue_number": 123,
  "source_comment_id": 456,
  "source_comment_url": "https://github.com/owner/repo/issues/123#issuecomment-456",
  "actor_login": "partner-user",
  "created_at": "2026-06-13T12:00:00Z",
  "producer": "RepoBrain-Action",
  "producer_ref": "main",
  "transport_mode": "github_app_queue"
}
-->
```

The visible comment should say:
- RepoBrain request queued for private control-plane processing.

## 4. Required fields

- `contract_version`
- `request_id`
- `status`
- `command`
- `profile`
- `repository_full_name`
- `event_kind`
- `issue_number` or `pull_request_number`
- `source_comment_id` when available
- `created_at`
- `producer`
- `transport_mode`

## 5. Optional fields

- `repository_id_marker`
- `actor_login`
- `source_comment_url`
- `workflow_run_id`
- `workflow_run_attempt`
- `head_sha`
- `base_sha`
- `changed_files_count`
- `requested_output_kind`

## 6. Idempotency

`request_id` must be deterministic enough to deduplicate retries.

Suggested inputs:
- `repository_full_name` or repository id marker
- issue or PR number
- `source_comment_id`
- command
- profile
- `head_sha` if PR
- `workflow_run_id` as fallback

Use SHA-256 or existing project-safe hashing.
Do not use secrets.

## 7. Public safety

Queue marker must not include:
- GitHub token
- OIDC token
- GitHub App private key
- installation token
- Authorization header
- TopoCore path, source, or runtime
- private checkout path
- `decide_raw`
- raw internal traces
- full private evidence payload
- dependency lockfile contents
- private environment variables

## 8. Evidence strategy

94C does not embed full audit evidence in the public marker.
The future 94D private control worker should fetch repository and PR context through a GitHub App installation token.

The 94C marker contains only enough public-safe metadata for discovery and correlation.

## 9. Status values

Defined values:
- `queued`
- `processing`
- `completed`
- `failed`
- `superseded`

94C only creates `queued`.
94D may later update or add `processing`, `completed`, or `failed` comments.

## 10. Failure behavior

If a queue marker cannot be created:
- return a public-safe error
- do not fall back to `hosted_api`
- do not run TopoCore in the partner repo
- do not ask for an owner token
- do not ask for a TopoCore token
