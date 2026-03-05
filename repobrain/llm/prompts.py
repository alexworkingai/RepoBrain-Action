from __future__ import annotations

from repobrain.evidence import EvidenceItem


def _token_estimate(text: str) -> int:
    return max(1, int(len(text) / 4))


def _trim_by_tokens(text: str, max_tokens: int) -> str:
    if _token_estimate(text) <= max_tokens:
        return text
    max_chars = max(1, int(max_tokens * 4))
    return text[:max_chars]


def _locator_lines(locators: list[EvidenceItem], limit: int = 20) -> list[str]:
    lines: list[str] = []
    for item in locators[:limit]:
        lines.append(f"- {item.file_path}:L{item.line_start}-L{item.line_end} score={item.score:.4f}")
    if len(locators) > limit:
        lines.append(f"- +{len(locators) - limit} more locators")
    return lines


def build_messages_for_ask(
    *,
    query: str,
    locators: list[EvidenceItem],
    max_input_tokens: int,
) -> list[dict[str, str]]:
    locator_block = "\n".join(_locator_lines(locators))
    user = (
        "Task: answer repository question using locator references only.\n"
        f"Question: {query.strip()}\n"
        "Locators:\n"
        f"{locator_block or '- none'}\n"
        "Output requirements: concise, usersafe, no raw secrets."
    )
    user = _trim_by_tokens(user, max_input_tokens)
    return [
        {
            "role": "system",
            "content": (
                "You are RepoBrain assistant. Use only provided locator metadata. "
                "Do not invent file content."
            ),
        },
        {"role": "user", "content": user},
    ]


def build_messages_for_review(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    max_input_tokens: int,
) -> list[dict[str, str]]:
    files_block = "\n".join(f"- {path}" for path in changed_files[:30]) or "- none"
    hunks_block = "\n".join(diff_hunks[:12]) or "no hunks available"
    user = (
        "Task: produce concise PR review summary with risks and next steps.\n"
        f"Instruction: {query.strip() or 'review changes'}\n"
        "Changed files:\n"
        f"{files_block}\n"
        "Diff hints:\n"
        f"{hunks_block}"
    )
    user = _trim_by_tokens(user, max_input_tokens)
    return [
        {
            "role": "system",
            "content": (
                "You are RepoBrain PR reviewer. Be usersafe, deterministic, and avoid exposing secrets."
            ),
        },
        {"role": "user", "content": user},
    ]


def build_messages_for_fix(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    max_input_tokens: int,
) -> list[dict[str, str]]:
    files_block = "\n".join(f"- {path}" for path in changed_files[:30]) or "- none"
    hunks_block = "\n".join(diff_hunks[:12]) or "no hunks available"
    user = (
        "Task: suggest minimal patch strategy and fix summary.\n"
        f"Instruction: {query.strip() or 'fix issues in changed files'}\n"
        "Changed files:\n"
        f"{files_block}\n"
        "Diff hints:\n"
        f"{hunks_block}\n"
        "Do not include secrets."
    )
    user = _trim_by_tokens(user, max_input_tokens)
    return [
        {
            "role": "system",
            "content": (
                "You are RepoBrain fixer. Return concise patch guidance and validation steps."
            ),
        },
        {"role": "user", "content": user},
    ]
