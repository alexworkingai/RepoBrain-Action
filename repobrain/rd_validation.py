from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import re
from typing import Any


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _policy_hash(policy: dict[str, Any]) -> str:
    flat = "|".join(f"{k}={policy[k]}" for k in sorted(policy))
    return hashlib.blake2s(flat.encode("utf-8"), digest_size=10).hexdigest()


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
    policy_hash: str


_BLOCKED_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\beval\s*\(", "eval_call"),
    (r"\bexec\s*\(", "exec_call"),
    (r"\bos\.system\s*\(", "os_system_call"),
    (r"\bsubprocess\.", "subprocess_usage"),
)

_NETWORK_PATTERN = re.compile(r"\b(requests|httpx|urllib|socket)\b", flags=re.IGNORECASE)
_WRITE_PATTERN = re.compile(
    r"""open\s*\([^)]*,\s*["'][wa]\+?["']""",
    flags=re.IGNORECASE,
)


def validate_codegen_artifact(
    content: str,
    *,
    language: str = "python",
    sandbox_policy: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate generated code against a strict local policy."""
    policy = dict(sandbox_policy or {})
    errors: list[str] = []
    warnings: list[str] = []
    source = str(content or "")

    if not source.strip():
        errors.append("empty_content")
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings,
            policy_hash=_policy_hash(policy),
        )

    normalized_lang = str(language or "python").strip().lower()
    if normalized_lang != "python":
        warnings.append(f"language_not_verified:{normalized_lang}")
    else:
        try:
            ast.parse(source)
        except SyntaxError as exc:
            errors.append(f"python_syntax_error:{exc.lineno}")

    source_lower = source.lower()
    for pattern, code in _BLOCKED_PATTERNS:
        if re.search(pattern, source_lower, flags=re.IGNORECASE):
            errors.append(code)

    if not _to_bool(policy.get("allow_network"), default=False) and _NETWORK_PATTERN.search(source):
        errors.append("network_calls_disallowed")

    if (
        not _to_bool(policy.get("allow_filesystem_write"), default=False)
        and _WRITE_PATTERN.search(source)
    ):
        errors.append("filesystem_write_disallowed")

    if _to_bool(policy.get("require_tests"), default=False) and "def test_" not in source_lower:
        warnings.append("tests_not_found")

    return ValidationResult(
        valid=not errors,
        errors=errors,
        warnings=warnings,
        policy_hash=_policy_hash(policy),
    )
