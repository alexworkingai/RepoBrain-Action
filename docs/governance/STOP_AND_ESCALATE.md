# Stop and Escalate Rules

Contributors and operators must stop and file a product issue instead of improvising when any trigger below is hit.

## Mandatory Stop Triggers

1. Supported vs unsupported behavior is unclear.
2. Request implies exposing protected-kernel internals.
3. Requested scope widens beyond current sprint approval.
4. Docs and live behavior disagree.
5. Ownership/approval path is unclear for change class.
6. Legacy anomaly appears outside current sprint path.
7. Live artifact truth contradicts local results.

## Escalation Output (Minimum)

Every escalation issue should include:

- observed behavior,
- expected behavior,
- environment/surface (GitHub, external, MCP),
- artifact/log evidence,
- risk if ignored,
- recommended narrow next step.

## Non-Improvisation Rule

Do not introduce ad hoc behavior changes to "make tests pass" when stop triggers are active.

Instead:

1. preserve current accepted semantics,
2. report evidence,
3. request explicit sprint/owner decision.

## Legacy Anomaly Rule

Known legacy anomalies are not reopened by default.
Only reopen when fresh evidence appears on current production-relevant flows.
