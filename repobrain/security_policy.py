from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from repobrain.security import detect_injection_or_exfiltration


_EXFIL_VERB_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(reveal|dump|exfiltrate|leak|disclose|print|show)\b", re.IGNORECASE),
    re.compile(r"\b(выведи|покажи|выгрузи|раскрой|слей|дамп)\b", re.IGNORECASE),
)

_PROTECTED_TARGET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsystem\s+prompt\b", re.IGNORECASE),
    re.compile(r"\bhidden\s+(rules|prompt|instructions)\b", re.IGNORECASE),
    re.compile(r"\binternal\s+instructions\b", re.IGNORECASE),
    re.compile(r"repobrain/tkya/vendor", re.IGNORECASE),
    re.compile(r"topocore_tcx", re.IGNORECASE),
    re.compile(r"\.env\b", re.IGNORECASE),
    re.compile(r"\bid_rsa\b", re.IGNORECASE),
    re.compile(r"begin\s+private\s+key", re.IGNORECASE),
)

_BENIGN_REPO_ANALYSIS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(review|analy[sz]e|summary|summarize|explain|locate|fix|ask)\b", re.IGNORECASE),
    re.compile(r"\b(pr|pull request|diff|changed files|files changed|risk)\b", re.IGNORECASE),
    re.compile(r"\b(security review|secret leakage|token handling|password handling)\b", re.IGNORECASE),
    re.compile(r"\b(проверь|объясни|где|риск|измен)\b", re.IGNORECASE),
)

_PROMPT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bignore\s+(all|previous)\s+instructions\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+the\s+system\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class SecurityPolicyDecision:
    blocked: bool
    security_scope: str
    security_outcome: str
    security_reason_code: str
    security_reason_short: str
    signals: list[str]
    risk: str

    def as_audit_dict(self) -> dict[str, Any]:
        return {
            "blocked": self.blocked,
            "scope": self.security_scope,
            "outcome": self.security_outcome,
            "reason_code": self.security_reason_code,
            "reason_short": self.security_reason_short,
            "signals": list(self.signals),
            "risk": self.risk,
        }


def _has_any(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def _normalize_targets(target_paths: list[str] | None) -> str:
    if not target_paths:
        return ""
    return "\n".join(path.strip() for path in target_paths if str(path).strip())


def classify_security_scope(
    request: str,
    *,
    github_context: dict[str, Any] | None = None,
    target_paths: list[str] | None = None,
    command_type: str = "",
) -> SecurityPolicyDecision:
    """Calibrated orchestration-level security classification.

    protected_zone:
      hard guard around TKYA internals, hidden prompts, secret-like protected targets.
    repo_analysis:
      normal repository/PR analysis.
    uncertain:
      ambiguous suspicious requests (kept conservative).
    """
    text = str(request or "")
    lowered = text.lower()
    target_text = _normalize_targets(target_paths).lower()
    command = str(command_type or "").strip().lower()
    legacy = detect_injection_or_exfiltration(text)
    legacy_signals = set(legacy.get("signals", []))

    exfil_verbs = _has_any(_EXFIL_VERB_PATTERNS, lowered)
    protected_target = _has_any(_PROTECTED_TARGET_PATTERNS, lowered) or _has_any(
        _PROTECTED_TARGET_PATTERNS,
        target_text,
    )
    benign_analysis = _has_any(_BENIGN_REPO_ANALYSIS_PATTERNS, lowered) or command in {
        "ask",
        "review",
        "fix",
        "locate",
        "explain",
        "verify",
    }
    prompt_injection = _has_any(_PROMPT_INJECTION_PATTERNS, lowered)
    strong_legacy = bool(legacy_signals & {"system_prompt_request", "sensitive_file_request", "bulk_dump_request"})

    if strong_legacy or (protected_target and exfil_verbs):
        return SecurityPolicyDecision(
            blocked=True,
            security_scope="protected_zone",
            security_outcome="block",
            security_reason_code="PROTECTED_ZONE_EXFIL_ATTEMPT",
            security_reason_short="Request blocked: protected internals or secret-like targets cannot be exposed.",
            signals=sorted(legacy_signals) or ["protected_target_exfiltration"],
            risk="high",
        )

    if prompt_injection and not benign_analysis:
        return SecurityPolicyDecision(
            blocked=True,
            security_scope="uncertain",
            security_outcome="block",
            security_reason_code="PROMPT_INJECTION_PATTERN",
            security_reason_short="Request blocked: suspicious prompt-injection pattern detected.",
            signals=sorted(legacy_signals) or ["prompt_injection_pattern"],
            risk="high",
        )

    if legacy.get("blocked", False) and not benign_analysis and exfil_verbs:
        return SecurityPolicyDecision(
            blocked=True,
            security_scope="uncertain",
            security_outcome="block",
            security_reason_code="SUSPICIOUS_EXFIL_REQUEST",
            security_reason_short="Request blocked: potential exfiltration request detected.",
            signals=sorted(legacy_signals) or ["suspicious_exfiltration"],
            risk="high",
        )

    reason_code = "REPO_ANALYSIS_ALLOWED"
    reason_short = "Request allowed: repository analysis in current context."
    if legacy.get("blocked", False):
        reason_code = "REPO_ANALYSIS_ALLOWED_AFTER_CALIBRATION"
        reason_short = "Request allowed: security wording detected, but target is standard repo/PR analysis."
    if github_context and bool(github_context.get("is_pr", False)):
        reason_short = "Request allowed: PR-context repository analysis."

    return SecurityPolicyDecision(
        blocked=False,
        security_scope="repo_analysis",
        security_outcome="allow",
        security_reason_code=reason_code,
        security_reason_short=reason_short,
        signals=sorted(legacy_signals),
        risk="low",
    )

