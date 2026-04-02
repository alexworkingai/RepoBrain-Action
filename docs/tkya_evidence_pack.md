# Evidence Pack v1 (Public-Safe Contract)

RepoBrain writes three Evidence Pack artifacts per run:

- `artifacts/evidence_pack/repobrain_tkya_evidence_pack_internal.json`
- `artifacts/evidence_pack/repobrain_tkya_evidence_pack_public_safe.json`
- `artifacts/evidence_pack/repobrain_tkya_evidence_pack.md`

## Purpose

- `internal.json`: richer operator-facing decision truth under existing safety constraints.
- `public_safe.json`: sanitized benchmark/comparison-friendly truth.
- `.md`: compact human-readable summary derived from public-safe truth.

## Generation

Generated automatically in run flow, or manually:

```bash
python scripts/gen_tkya_evidence_pack.py \
  --audit-dir artifacts/audit \
  --output-dir artifacts/evidence_pack
```

## Public-Safe Contract Highlights

- decision category truth (route/execution/governance)
- model/provider summary truth (requested/used/final)
- control-plane profile truth (requested/used/reason/outcome)
- boundedness and coverage honesty signals
- provenance summary
- trace safety markers (hash-only policy)
- repository-scale snapshot with explicit scope limits

## Safety

Public-safe artifact excludes raw prompt text, raw candidate text, and raw diff internals.

If canonical values are unavailable, artifacts keep explicit bounded placeholders instead of synthetic values.
