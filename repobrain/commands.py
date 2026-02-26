from __future__ import annotations


def parse_command(text: str) -> dict[str, str]:
    """Parse `/repobrain ...` issue comment commands into `{cmd, query}`."""
    raw = (text or "").strip()
    if not raw:
        return {"cmd": "help", "query": ""}

    parts = raw.split(maxsplit=2)
    if not parts or parts[0].lower() != "/repobrain":
        return {"cmd": "help", "query": ""}

    if len(parts) == 1:
        return {"cmd": "help", "query": ""}

    cmd = parts[1].lower()
    supported = {"help", "ask", "locate", "explain", "review", "verify"}
    if cmd not in supported:
        return {"cmd": "help", "query": ""}

    if cmd in {"help", "review", "verify"}:
        return {"cmd": cmd, "query": ""}

    if len(parts) < 3 or not parts[2].strip():
        return {"cmd": "help", "query": ""}

    return {"cmd": cmd, "query": parts[2].strip()}
