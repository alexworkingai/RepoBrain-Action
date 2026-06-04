from __future__ import annotations

from typing import Any


def parse_command(text: str) -> dict[str, Any]:
    """Parse `/repobrain ...` issue comment commands into command fields."""
    raw = (text or "").strip()
    if not raw:
        return {"cmd": "help", "query": ""}

    parts = raw.split(maxsplit=2)
    if not parts or parts[0].lower() != "/repobrain":
        return {"cmd": "help", "query": ""}

    if len(parts) == 1:
        return {"cmd": "help", "query": ""}

    cmd = parts[1].lower()
    supported = {
        "help",
        "ask",
        "locate",
        "explain",
        "review",
        "verify",
        "fix",
        "audit",
        "doctor",
        "status",
        "score",
    }
    if cmd not in supported:
        return {"cmd": "unsupported", "query": ""}

    if cmd in {"help", "review", "verify"}:
        base: dict[str, Any] = {"cmd": cmd, "query": ""}
    elif cmd in {"fix", "audit", "doctor", "status", "score"}:
        if len(parts) >= 3:
            base = {"cmd": cmd, "query": parts[2].strip()}
        else:
            base = {"cmd": cmd, "query": ""}
    else:
        if len(parts) < 3 or not parts[2].strip():
            return {"cmd": "help", "query": ""}
        base = {"cmd": cmd, "query": parts[2].strip()}

    if cmd not in {"ask", "explain", "review", "fix", "audit"}:
        return base

    query = base.get("query", "")
    if not query and cmd in {"review", "fix", "audit"} and len(parts) >= 3:
        query = parts[2].strip()

    tokens = query.split() if query else []
    out_tokens: list[str] = []
    profile_override = ""
    audit_narrative = False
    audit_executive = False
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        lower = token.lower()
        if lower == "--profile":
            if idx + 1 >= len(tokens):
                base["error_code"] = "missing_profile_value"
                base["error_message"] = (
                    "Invalid command: `--profile` requires one value from `cheap | balanced | premium`."
                )
                return base
            profile_value = tokens[idx + 1].strip().lower()
            if profile_value not in {"cheap", "balanced", "premium"}:
                base["error_code"] = "invalid_profile_value"
                base["error_message"] = (
                    f"Invalid profile `{tokens[idx + 1]}`. Allowed values: `cheap | balanced | premium`."
                )
                return base
            if profile_override:
                base["error_code"] = "duplicate_profile_value"
                base["error_message"] = (
                    "Invalid command: `--profile` can be set only once per command."
                )
                return base
            profile_override = profile_value
            idx += 2
            continue
        if lower.startswith("--profile="):
            profile_value = token.split("=", 1)[1].strip().lower()
            if profile_value not in {"cheap", "balanced", "premium"}:
                base["error_code"] = "invalid_profile_value"
                base["error_message"] = (
                    f"Invalid profile `{profile_value}`. Allowed values: `cheap | balanced | premium`."
                )
                return base
            if profile_override:
                base["error_code"] = "duplicate_profile_value"
                base["error_message"] = (
                    "Invalid command: `--profile` can be set only once per command."
                )
                return base
            profile_override = profile_value
            idx += 1
            continue
        if cmd == "audit" and lower in {"--narrative", "--executive"}:
            if lower == "--narrative":
                audit_narrative = True
            if lower == "--executive":
                audit_executive = True
            idx += 1
            continue
        out_tokens.append(token)
        idx += 1

    if cmd in {"ask", "explain"} and not out_tokens:
        return {"cmd": "help", "query": ""}

    if cmd == "fix":
        base["query"] = " ".join(out_tokens).strip()
    elif cmd == "review":
        # Keep existing command contract: review query remains empty.
        base["query"] = ""
    else:
        base["query"] = " ".join(out_tokens).strip()

    if profile_override:
        base["profile"] = profile_override
    if cmd == "audit":
        if profile_override == "premium" and not audit_narrative and not audit_executive:
            audit_narrative = True
        if audit_narrative:
            base["narrative"] = "1"
        if audit_executive:
            base["executive"] = "1"

    return base
