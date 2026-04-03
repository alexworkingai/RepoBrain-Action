# Capability Surfaces (Current)

## Surface Matrix

| Surface | Entry Point | Supported | Unsupported | Notes |
|---|---|---|---|---|
| GitHub mode | `/repobrain` commands in GitHub comments | `help`, `ask`, `review`, `fix` | out-of-contract commands | Primary runtime path. |
| External GitHub mode foundation | third-party caller workflow -> `repobrain_external_foundation.yml` | `help`, `ask` | `review`, `fix`, out-of-contract commands | Product-shaped third-party GitHub-native foundation path. |
| External mode | `scripts/run_github.py --mode external` | `ask` | `review`, `fix`, non-ask commands | Explicit unsupported block expected. |
| MCP surface | `scripts/run_mcp_surface.py` | `ask` capability | non-ask capabilities | Structured public-safe response contract. |

## Execution Profile Contract

For GitHub command surface:

- command-level `--profile cheap|balanced|premium` is supported,
- default remains `balanced`,
- review/fix `cheap` requests are normalized to governed `balanced`.

External and MCP ask-first surfaces do not broaden this capability scope.

## Artifact Expectations by Surface

### GitHub mode

- readiness, audit, diagnostic summary, evidence pack, benchmark path artifacts (as applicable).

### External GitHub mode foundation

- readiness, audit, diagnostic summary, evidence pack (bounded ask/help path).

### External mode

- command status/decision output and local external-flow artifacts.

### MCP surface

- structured response payload with explicit status/decision and public-safe output.

## Boundaries Reminder

Capability exposure is allowed.
Protected-kernel implementation disclosure is not.
