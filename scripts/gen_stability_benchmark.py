from __future__ import annotations

import argparse
from pathlib import Path

from repobrain.stability_benchmark import write_stability_benchmark_artifacts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", default="artifacts/audit")
    parser.add_argument(
        "--history-path",
        default="artifacts/.repobrain_cache/stability_benchmark_history.json",
    )
    parser.add_argument(
        "--output-json",
        default="artifacts/benchmarks/repobrain_stability_benchmark.json",
    )
    parser.add_argument(
        "--output-md",
        default="artifacts/benchmarks/repobrain_stability_benchmark.md",
    )
    args = parser.parse_args()

    audit_dir = Path(args.audit_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    history_path = Path(args.history_path)
    payload = write_stability_benchmark_artifacts(
        audit_dir=audit_dir,
        output_json_path=output_json,
        output_markdown_path=output_md,
        history_path=history_path,
    )
    print(f"BENCHMARK_JSON_PATH={output_json.as_posix()}")
    print(f"BENCHMARK_MD_PATH={output_md.as_posix()}")
    print(f"BENCHMARK_STATUS={str(payload.get('overall_status', 'not_enough_data'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
