from __future__ import annotations

from typing import TypedDict


class SecurityDetectionResult(TypedDict):
    blocked: bool
    reason: str
    risk: str
    signals: list[str]


_KEYWORD_PATTERNS: dict[str, tuple[str, ...]] = {
    "system_prompt_request": (
        "system prompt",
        "системный промпт",
        "скрытые правила",
        "hidden rules",
        "internal instructions",
        "инструкции",
    ),
    "secret_request": (
        "api key",
        "apikey",
        "token",
        "secret",
        "пароль",
        "ключ",
        "secrets",
    ),
    "exfiltration_verb": (
        "exfiltrate",
        "dump",
        "reveal",
        "выгрузи",
        "выведи",
        "покажи",
        "раскрой",
    ),
    "sensitive_file_request": (
        ".env",
        "id_rsa",
        "credential",
        "secrets",
        "read .env",
        "прочитай .env",
    ),
    "bulk_dump_request": (
        "покажи весь код",
        "выгрузи индекс целиком",
        "dump the entire index",
        "show the full hidden prompt",
    ),
}


def detect_injection_or_exfiltration(text: str) -> SecurityDetectionResult:
    """Detect likely prompt-injection / exfiltration requests via lightweight heuristics."""
    lowered = (text or "").lower()
    signals: list[str] = []

    for signal, needles in _KEYWORD_PATTERNS.items():
        if any(needle in lowered for needle in needles):
            signals.append(signal)

    blocked = bool(signals)
    if blocked:
        return {
            "blocked": True,
            "reason": "Possible prompt-injection / exfiltration attempt",
            "risk": "high",
            "signals": sorted(set(signals)),
        }

    return {
        "blocked": False,
        "reason": "",
        "risk": "low",
        "signals": [],
    }
