# External Repo Trial Evidence Template

Use this capture template to store Trial evidence in a deterministic format.

## JSON Skeleton

```json
{
  "trial_id": "external-repo-trial-xx",
  "repository": "owner/repo",
  "target_pr": {
    "number": 0,
    "url": "",
    "head_sha": ""
  },
  "operator": {
    "name": "",
    "timestamp_utc": ""
  },
  "readiness": {
    "overall_status": "READY|MISSING_PERMISSION|MISSING_CONFIG|UNSUPPORTED_SETUP",
    "status_reason_code": "",
    "status_reason_short": "",
    "blocking_summary": [],
    "next_steps": []
  },
  "commands": [
    {
      "order": 1,
      "command": "/repobrain help",
      "workflow_run_id": "",
      "workflow_run_url": "",
      "comment_url": "",
      "status": "COMMAND_WORKED|COMMAND_FAILED",
      "artifacts": [
        {
          "name": "repobrain-install-readiness",
          "files": []
        }
      ],
      "notes": ""
    }
  ],
  "operator_blockers": [
    {
      "code": "",
      "summary": "",
      "impact": "",
      "next_step": ""
    }
  ],
  "observations": {
    "ask_quality": "",
    "review_quality": "",
    "fix_or_no_patch_behavior": "",
    "artifact_consistency": ""
  },
  "final_verdict": "TRIAL_PASS|TRIAL_PARTIAL|TRIAL_BLOCKED",
  "next_actions": [
    {
      "owner": "",
      "action": "",
      "due_date": ""
    }
  ]
}
```

## Minimal Required Fields

The following fields are mandatory for every trial report:

1. `trial_id`
2. `repository`
3. `target_pr.number`
4. `readiness.overall_status`
5. `commands[*].command`
6. `commands[*].status`
7. `final_verdict`

## Artifact Link Discipline

For each command step, include at least one reproducible pointer:

- workflow run URL, or
- artifact file path, or
- archived local evidence path.

If a required artifact is missing, record it explicitly in `notes` and `operator_blockers`.
