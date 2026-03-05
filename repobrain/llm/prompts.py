from __future__ import annotations

from typing import Any

from repobrain.evidence import EvidenceItem


def estimate_tokens(text: str) -> int:
    """Heuristic token estimate used for prompt budgeting."""
    return max(1, int(len(text) / 4))


def _trim_to_budget(text: str, max_tokens: int) -> str:
    if estimate_tokens(text) <= max_tokens:
        return text
    return text[: max(1, int(max_tokens * 4))]


def _locator_lines(locators: list[EvidenceItem], limit: int = 50) -> list[str]:
    lines: list[str] = []
    for item in locators[:limit]:
        lines.append(f"- {item.file_path}:L{item.line_start}-L{item.line_end} score={item.score:.4f}")
    if len(locators) > limit:
        lines.append(f"- +{len(locators) - limit} more locators")
    return lines


def _sanitize_item(text: str, *, per_item_limit_tokens: int) -> str:
    cleaned = str(text or "").strip()
    if not cleaned:
        return ""
    return _trim_to_budget(cleaned, per_item_limit_tokens)


def _append_section_with_budget(
    *,
    blocks: list[str],
    used_tokens: int,
    budget_limit: int,
    header: str,
    items: list[str],
    per_item_limit_tokens: int,
) -> tuple[int, int]:
    dropped = 0
    if not items:
        return used_tokens, dropped

    header_block = f"\n{header}\n"
    header_tokens = estimate_tokens(header_block)
    if used_tokens + header_tokens > budget_limit:
        return used_tokens, len(items)
    blocks.append(header_block.rstrip("\n"))
    used_tokens += header_tokens

    for raw in items:
        item = _sanitize_item(raw, per_item_limit_tokens=per_item_limit_tokens)
        if not item:
            continue
        line_block = f"{item}\n"
        line_tokens = estimate_tokens(line_block)
        if used_tokens + line_tokens > budget_limit:
            dropped += 1
            continue
        blocks.append(item)
        used_tokens += line_tokens
    return used_tokens, dropped


def _build_messages(
    *,
    system_content: str,
    task_line: str,
    query: str,
    locators_lines: list[str],
    diff_hunks: list[str],
    selected_snippets: list[str],
    max_input_tokens: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    budget_limit = max(400, int(max_input_tokens))
    blocks: list[str] = []

    sanitized_query = _trim_to_budget(str(query or "").strip(), max(80, int(budget_limit * 0.25)))
    intro = "\n".join(
        [
            task_line,
            f"Query: {sanitized_query or 'n/a'}",
            "Output: usersafe, concise, no raw secrets.",
        ]
    )

    used_tokens = estimate_tokens(system_content) + estimate_tokens(intro)
    blocks.append(intro)

    used_tokens, dropped_locators = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Locators:",
        items=locators_lines,
        per_item_limit_tokens=32,
    )
    used_tokens, dropped_hunks = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Diff hunks:",
        items=diff_hunks,
        per_item_limit_tokens=180,
    )
    used_tokens, dropped_snippets = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Selected snippets:",
        items=selected_snippets,
        per_item_limit_tokens=220,
    )

    user_content = "\n".join(blocks)
    if estimate_tokens(user_content) > budget_limit:
        user_content = _trim_to_budget(user_content, budget_limit)
        used_tokens = estimate_tokens(system_content) + estimate_tokens(user_content)

    stats = {
        "input_budget_limit": budget_limit,
        "input_budget_used_est": min(used_tokens, budget_limit),
        "dropped_locators_count": int(dropped_locators),
        "dropped_hunks_count": int(dropped_hunks),
        "dropped_snippets_count": int(dropped_snippets),
    }
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
    return messages, stats


def build_messages_for_ask(
    *,
    query: str,
    locators: list[EvidenceItem],
    max_input_tokens: int,
    selected_snippets: list[str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    return _build_messages(
        system_content=(
            "You are RepoBrain assistant. Use only provided metadata and snippets. "
            "Do not invent file content."
        ),
        task_line="Task: answer repository question with evidence references.",
        query=query,
        locators_lines=_locator_lines(locators),
        diff_hunks=[],
        selected_snippets=[str(item) for item in (selected_snippets or [])],
        max_input_tokens=max_input_tokens,
    )


def build_messages_for_review(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    max_input_tokens: int,
    selected_snippets: list[str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    locators_lines = [f"- {path}" for path in changed_files[:80]]
    return _build_messages(
        system_content=(
            "You are RepoBrain PR reviewer. Be usersafe and deterministic. "
            "Focus on risks, impact, and practical next steps."
        ),
        task_line="Task: produce concise PR review summary.",
        query=query,
        locators_lines=locators_lines,
        diff_hunks=[str(item) for item in diff_hunks],
        selected_snippets=[str(item) for item in (selected_snippets or [])],
        max_input_tokens=max_input_tokens,
    )


def build_messages_for_fix(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    max_input_tokens: int,
    selected_snippets: list[str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    locators_lines = [f"- {path}" for path in changed_files[:80]]
    return _build_messages(
        system_content=(
            "You are RepoBrain fixer. Return concise patch guidance and validation steps. "
            "Do not expose secrets."
        ),
        task_line="Task: propose minimal safe patch strategy.",
        query=query,
        locators_lines=locators_lines,
        diff_hunks=[str(item) for item in diff_hunks],
        selected_snippets=[str(item) for item in (selected_snippets or [])],
        max_input_tokens=max_input_tokens,
    )
