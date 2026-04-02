# MCP Surface (v1, Ask-First)

## Scope

RepoBrain exposes a thin MCP-facing capability surface on top of the accepted external ask runtime.

Current scope:

- supported capability: `ask`
- unsupported capabilities: blocked explicitly
- output: public-safe structured response

This is intentionally bounded and does not expose protected kernel internals.

## CLI Adapter

```bash
python scripts/run_mcp_surface.py \
  --capability ask \
  --repo-root /path/to/repo \
  --query "What changed around module X?"
```

Optional structured input/output:

- `--request-json <path>`
- `--response-json <path>`

## Request Contract (v1)

Minimal fields:

- `capability` (`ask` supported)
- `repo_root`
- `query`

Optional fields:

- `dry_run`
- `tky_mode`
- `request_id`

## Response Contract (v1)

Public-safe fields:

- `surface_version`
- `public_safe`
- `kernel_disclosure`
- `capability_requested`
- `capability_used`
- `supported_capabilities`
- `status`
- `decision`
- `reason_code`
- `reason_short`
- `output.answer_text` (for successful ask)

## Honest Unsupported Behavior

When capability is outside supported scope:

- `status=blocked`
- `decision=UNSUPPORTED_CAPABILITY`
- deterministic reason fields are included.

## Boundaries

This surface does not claim:

- external review support,
- external fix support,
- full external GitHub-native runtime parity.
