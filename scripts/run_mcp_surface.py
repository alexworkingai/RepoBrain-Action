from __future__ import annotations

import argparse
import json
from pathlib import Path

from repobrain.mcp_surface import handle_mcp_request, request_from_payload


def _load_payload(args: argparse.Namespace) -> dict[str, object]:
    if args.request_json:
        raw = Path(args.request_json).read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("request JSON must be an object.")
        return payload

    return {
        "capability": args.capability,
        "repo_root": args.repo_root,
        "query": args.query,
        "dry_run": args.dry_run,
        "tky_mode": args.tky_mode,
        "request_id": args.request_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request-json", default="")
    parser.add_argument("--response-json", default="")
    parser.add_argument("--capability", default="ask")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--query", default="")
    parser.add_argument("--dry-run", default="true")
    parser.add_argument("--tky-mode", default="auto")
    parser.add_argument("--request-id", default="")
    args = parser.parse_args()

    payload = _load_payload(args)
    request = request_from_payload(payload)
    response = handle_mcp_request(request)
    rendered = json.dumps(response, ensure_ascii=True, indent=2, sort_keys=True)
    print(rendered)
    if args.response_json:
        Path(args.response_json).write_text(rendered + "\n", encoding="utf-8")
    return 0 if response.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
