# TopoCore Entrypoint Adapter v1

Contract name: `repobrain.topocore_entrypoint_adapter.v1`

## Purpose

Define how RepoBrain invokes TopoCore without implementing TopoCore internals.

## Required principles

- TopoCore is a separate team and system.
- Adapter sends request JSON to a configured private entrypoint.
- Adapter receives response JSON.
- Adapter validates and normalizes the response.
- Adapter hides internal fields.
- Commands remain stable.
- Future TopoCore capabilities can be accepted through capability fields without changing user commands.

## Supported private entrypoint modes

- command mode: `REPOBRAIN_TOPOCORE_ENTRYPOINT_CMD`
- module mode, optional future: `REPOBRAIN_TOPOCORE_ENTRYPOINT_MODULE`
- mock or stub mode for tests only: `REPOBRAIN_TOPOCORE_ENTRYPOINT_MODE=stub`

Do not require real TopoCore in public CI.

## Failure statuses

- `TOPOCORE_ENTRYPOINT_NOT_CONFIGURED`
- `TOPOCORE_ENTRYPOINT_TIMEOUT`
- `TOPOCORE_ENTRYPOINT_FAILED`
- `TOPOCORE_RESPONSE_INVALID`
- `TOPOCORE_RESPONSE_UNSAFE`
- `TOPOCORE_CAPABILITY_UNSUPPORTED`
