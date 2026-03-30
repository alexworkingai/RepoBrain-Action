# TKYA-Aware Evidence Pack v1

RepoBrain writes three Evidence Pack artifacts per run:

- `artifacts/evidence_pack/repobrain_tkya_evidence_pack_internal.json`
- `artifacts/evidence_pack/repobrain_tkya_evidence_pack_public_safe.json`
- `artifacts/evidence_pack/repobrain_tkya_evidence_pack.md`

## Purpose
- `internal.json`: richer operator-facing canonical TKYA truth.
- `public_safe.json`: sanitized comparison-friendly subset.
- `.md`: compact human-readable summary generated from public-safe truth.

## Generation
Issue-comment and workflow runs generate the pack automatically through `scripts/run_github.py`.

Manual regeneration from latest audit artifact:

```bash
python scripts/gen_tkya_evidence_pack.py \
  --audit-dir artifacts/audit \
  --output-dir artifacts/evidence_pack
```

## Contract highlights
- decision truth: route, execution mode, llm intent/reason, backend/engine
- canonical TKYA signals: topology, HUK, ZigZag, MorseFlow, verification gate
- boundedness and coverage: evidence budget and ultra-large mode summaries
- provenance: runtime SHA vs PR head SHA state
- trace safety: hash-only trace schema and hash references
- repository scale snapshot: file/folder/size counters

## Safety
Public-safe artifact intentionally excludes raw prompt text, raw candidate text, and raw diff internals.
