from __future__ import annotations

import argparse
from pathlib import Path

import orjson

from repobrain.tkya_evidence_pack import write_tkya_evidence_pack_artifacts


def _latest_audit_path(audit_dir: Path) -> Path | None:
    candidates = sorted(audit_dir.glob("audit_*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0.0)
    return candidates[-1] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", default="artifacts/audit")
    parser.add_argument("--output-dir", default="artifacts/evidence_pack")
    args = parser.parse_args()

    audit_dir = Path(args.audit_dir)
    output_dir = Path(args.output_dir)
    latest = _latest_audit_path(audit_dir)
    if latest is None:
        print("EVIDENCE_PACK_STATUS=no_audit_found")
        return 0

    payload_raw = orjson.loads(latest.read_bytes())
    audit = payload_raw if isinstance(payload_raw, dict) else {}
    result = write_tkya_evidence_pack_artifacts(
        repo_root=Path.cwd(),
        audit=audit,
        output_dir=output_dir,
    )
    print(f"EVIDENCE_PACK_AUDIT_SOURCE={latest.as_posix()}")
    print(f"EVIDENCE_PACK_INTERNAL_PATH={str(result.get('internal_path', 'n/a'))}")
    print(f"EVIDENCE_PACK_PUBLIC_SAFE_PATH={str(result.get('public_safe_path', 'n/a'))}")
    print(f"EVIDENCE_PACK_SUMMARY_PATH={str(result.get('summary_path', 'n/a'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
