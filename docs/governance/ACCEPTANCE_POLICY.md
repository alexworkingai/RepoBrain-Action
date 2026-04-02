# Acceptance Policy

## Core Rule

Acceptance has three distinct states:

1. Local validated: mandatory local gate is green.
2. Live validated: behavior/artifacts verified in the relevant live surface.
3. Accepted: human-reviewed decision that documentation, behavior, and evidence are aligned.

Local validated is necessary but not sufficient.

## Required Evidence by Surface

### GitHub mode changes

Must verify in live PR context:

- command behavior,
- visible output behavior,
- artifact truth,
- honest unsupported behavior where applicable.

### External mode changes

Must verify in external CLI execution on real target repo path:

- supported command result,
- unsupported command block behavior,
- artifact/log consistency.

### MCP surface changes

Must verify live adapter path:

- request/response contract,
- supported capability behavior,
- unsupported capability block behavior,
- public-safe output discipline.

### Docs-only productization changes

Must verify docs against accepted live reality:

- no capability over-claim,
- no mismatch between docs and behavior,
- no protected-kernel disclosure regression.

## Acceptance Prohibitions

Do not mark accepted when any of the following is true:

1. Only local tests were run.
2. Live behavior contradicts docs or claims.
3. Supported/unsupported boundary is ambiguous.
4. Protected-kernel policy is violated.

## Evidence Source Priority

When sources conflict:

1. live behavior/artifacts,
2. canonical audit/evidence outputs,
3. local assumptions.

Live evidence wins.
