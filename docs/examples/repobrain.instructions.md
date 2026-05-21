# .github/repobrain.instructions.md

Review priorities:

- Treat auth, secrets, deployment, and schema-migration changes as high attention.
- Prefer small PRs and explicit operator intent.
- Generated files and build artifacts should not drive review focus by themselves.

Build and validation hints:

- Run the repository's normal lint/test commands when they are lightweight and deterministic.
- Prefer bounded evidence over broad speculation.
- Escalate missing private TopoCore v6 access as setup failure, not product success.

Rules:

- Keep review bounded and read-only unless a product surface explicitly says otherwise.
- Treat `/repobrain fix` output as manual-only guidance, not patch application.
- Do not assume v5, `lite`, or `repobrain-community` are available.
