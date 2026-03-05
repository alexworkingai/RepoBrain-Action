from __future__ import annotations

import argparse
from hashlib import sha256
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from typing import Any

import orjson

from .tkya.engine import get_engine
from .tky_engine import EngineCandidate, EngineQuery, EngineRequest

PRIVACY_FORBIDDEN_KEYS = {"text", "snippet", "content"}


def validate_payload_privacy(payload: dict[str, Any]) -> bool:
    """Return False if payload contains raw content fields inside candidates."""
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        return False
    for item in candidates:
        if not isinstance(item, dict):
            return False
        lowered_keys = {str(key).lower() for key in item}
        if lowered_keys & PRIVACY_FORBIDDEN_KEYS:
            return False
    return True


def verify_signature(
    secret: str,
    body_bytes: bytes,
    ts: str,
    nonce: str,
    signature_hex: str,
) -> bool:
    """Verify stub HMAC signature: HMAC(secret, sha256(body)+'.'+ts+'.'+nonce)."""
    body_hash_hex = sha256(body_bytes).hexdigest()
    message = f"{body_hash_hex}.{ts}.{nonce}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex)


def build_response_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build stub response via selected TKYA engine from a privacy-safe payload."""
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []

    limits = payload.get("limits", {})
    max_sources = 8
    if isinstance(limits, dict):
        try:
            max_sources = int(limits.get("max_sources", 8))
        except (TypeError, ValueError):
            max_sources = 8

    engine_candidates: list[EngineCandidate] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        try:
            score_local = float(item.get("score_local", 0) or 0)
        except (TypeError, ValueError):
            score_local = 0.0
        signature = item.get("signature", [])
        if not isinstance(signature, list):
            signature = []
        engine_candidates.append(
            EngineCandidate(
                chunk_id=str(item.get("chunk_id", "")),
                score_local=score_local,
                signature=[int(x) for x in signature],
                file_path=str(item.get("file_path", "")) or None,
                line_start=int(item["line_start"]) if item.get("line_start") is not None else None,
                line_end=int(item["line_end"]) if item.get("line_end") is not None else None,
            )
        )

    task_type = str(payload.get("task_type", "ask")).lower()
    if task_type not in {"ask", "locate", "explain", "review"}:
        task_type = "ask"
    query = payload.get("query", {})
    if not isinstance(query, dict):
        query = {}
    query_signature = query.get("signature", [])
    if not isinstance(query_signature, list):
        query_signature = []
    github_context = payload.get("github_context", {})
    if not isinstance(github_context, dict):
        github_context = {}
    verification_context = payload.get("verification_context", {})
    if not isinstance(verification_context, dict):
        verification_context = {}

    req = EngineRequest(
        task_type=task_type,  # type: ignore[arg-type]
        query=EngineQuery(
            text=str(query.get("text", "")),
            signature=[int(x) for x in query_signature],
        ),
        candidates=engine_candidates,
        limits={**(limits if isinstance(limits, dict) else {}), "max_sources": max_sources},
        policy={
            "corelocked": True,
            "github_context": github_context,
            "verification_context": verification_context,
            "runtime": {
                "mode": "stub",
                "network_allowed": os.environ.get("RB_TKYA_ALLOW_REMOTE", "").strip() == "1",
            },
        },
    )
    decision = get_engine().decide(req)

    return {
        "schema_version": "1.0",
        "decision": {"route": decision.route, "reason": decision.rationale},
        "selection": {"selected_chunk_ids": decision.selected_chunk_ids},
        "compression_stats": dict(decision.compression_stats),
        "security": {
            "blocked": decision.security.blocked,
            "injection_risk": decision.security.injection_risk,
            "exfiltration_risk": decision.security.exfiltration_risk,
            "signals": decision.security.signals,
        },
        "stable_tokens": decision.stable_tokens,
        "rationale": "Stub response",
    }


class _TKYStubHandler(BaseHTTPRequestHandler):
    server_version = "RepoBrainTKYStub/1.0"

    def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
        body_bytes = orjson.dumps(body)
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/tky/decide":
            self._send_json(404, {"error": "not_found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        body_bytes = self.rfile.read(max(content_length, 0))

        hmac_secret = os.environ.get("TKY_STUB_HMAC_SECRET", "").strip()
        if hmac_secret:
            ts = self.headers.get("x-ts", "")
            nonce = self.headers.get("x-nonce", "")
            signature = self.headers.get("x-signature", "")
            if not ts or not nonce or not signature:
                self._send_json(401, {"error": "missing_hmac_headers"})
                return
            if not verify_signature(hmac_secret, body_bytes, ts, nonce, signature):
                self._send_json(401, {"error": "invalid_signature"})
                return

        try:
            payload = orjson.loads(body_bytes)
        except orjson.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        if not isinstance(payload, dict):
            self._send_json(400, {"error": "invalid_payload"})
            return

        if not validate_payload_privacy(payload):
            self._send_json(422, {"error": "policy_violation", "reason": "raw_content_forbidden"})
            return

        self._send_json(200, build_response_from_payload(payload))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        # Keep CI logs compact.
        return


def run_server(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), _TKYStubHandler)
    print(f"RepoBrain TKY stub listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    run_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
