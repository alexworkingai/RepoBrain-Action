from __future__ import annotations

from collections import defaultdict
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


def _build_patch_messages(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    selected_snippets: list[str],
    max_input_tokens: int,
    max_hunks: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    budget_limit = max(256, int(max_input_tokens))
    blocks: list[str] = []

    sanitized_query = _trim_to_budget(str(query or "").strip(), max(48, int(budget_limit * 0.18)))
    intro = "\n".join(
        [
            "Task: produce a minimal safe patch for the requested files.",
            f"Fix instruction: {sanitized_query or 'n/a'}",
            "Response format (strict, in this exact priority):",
            "1) ```diff ...unified diff... ```",
            "2) NO_PATCH",
            "Fallback only if provider requires JSON envelope:",
            '{"result":"patch","diff":"..."} or {"result":"no_patch"}',
            "No prose before/after diff. No explanations. No secrets.",
        ]
    )
    system_content = (
        "You are RepoBrain fixer. Return ONLY one of: "
        "(A) a single ```diff fenced unified diff block, "
        "(B) exactly NO_PATCH, "
        "(C) strict JSON envelope {\"result\":\"patch\",\"diff\":\"...\"} or {\"result\":\"no_patch\"} "
        "only if diff fence cannot be returned by provider. "
        "Do not include prose."
    )

    used_tokens = estimate_tokens(system_content) + estimate_tokens(intro)
    blocks.append(intro)

    file_lines = [f"- {item}" for item in changed_files[:40]]
    dropped_target_files = max(0, len(changed_files) - len(file_lines))
    used_tokens, dropped_files_budget = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Target files:",
        items=file_lines,
        per_item_limit_tokens=24,
    )

    locator_lines = [f"- {item}" for item in changed_files[:60]]
    dropped_locator_input = max(0, len(changed_files) - len(locator_lines))
    used_tokens, dropped_locators_budget = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Locators:",
        items=locator_lines,
        per_item_limit_tokens=24,
    )

    bounded_hunks = list(diff_hunks[: max(1, int(max_hunks))])
    dropped_hunks_limit = max(0, len(diff_hunks) - len(bounded_hunks))
    used_tokens, dropped_hunks_budget = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Diff hunks:",
        items=bounded_hunks,
        per_item_limit_tokens=120,
    )

    bounded_snippets = list(selected_snippets[:24])
    dropped_snippet_limit = max(0, len(selected_snippets) - len(bounded_snippets))
    used_tokens, dropped_snippets_budget = _append_section_with_budget(
        blocks=blocks,
        used_tokens=used_tokens,
        budget_limit=budget_limit,
        header="Selected snippet IDs:",
        items=bounded_snippets,
        per_item_limit_tokens=40,
    )

    user_content = "\n".join(blocks)
    if estimate_tokens(user_content) > budget_limit:
        user_content = _trim_to_budget(user_content, budget_limit)
        used_tokens = estimate_tokens(system_content) + estimate_tokens(user_content)

    stats = {
        "input_budget_limit": budget_limit,
        "input_budget_used_est": min(used_tokens, budget_limit),
        "dropped_locators_count": int(dropped_target_files + dropped_locator_input + dropped_locators_budget + dropped_files_budget),
        "dropped_hunks_count": int(dropped_hunks_limit + dropped_hunks_budget),
        "dropped_snippets_count": int(dropped_snippet_limit + dropped_snippets_budget),
        "compacted": True,
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
    pr_changed_files: list[str] | None = None,
    max_input_tokens: int,
    selected_snippets: list[str] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    pr_lines = [f"- PR changed: {path}" for path in (pr_changed_files or []) if str(path).strip()]
    locator_lines = pr_lines[:40] + _locator_lines(locators)
    return _build_messages(
        system_content=(
            "You are RepoBrain assistant. Use only provided metadata and snippets. "
            "Do not invent file content."
        ),
        task_line="Task: answer repository question with evidence references.",
        query=query,
        locators_lines=locator_lines,
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
    max_files_context: int = 40,
    max_findings_context: int = 24,
    max_hunks_context: int = 24,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    files = [str(path).strip() for path in changed_files if str(path).strip()]
    unique_files = list(dict.fromkeys(files))
    subsystem_counts: defaultdict[str, int] = defaultdict(int)
    for path in unique_files:
        root = path.split("/", 1)[0] if "/" in path else path
        subsystem_counts[root] += 1

    max_files = max(1, int(max_files_context))
    max_findings = max(1, int(max_findings_context))
    max_hunks = max(1, int(max_hunks_context))

    grouped_summary_lines = [
        f"- subsystem `{name}`: {count} file(s)"
        for name, count in sorted(subsystem_counts.items(), key=lambda item: item[0])
    ]
    file_lines = [f"- {path}" for path in unique_files[:max_files]]
    dropped_files = max(0, len(unique_files) - len(file_lines))

    condensed_hunks = [str(item).strip() for item in diff_hunks if str(item).strip()]
    hunk_lines = [
        f"- hunk[{idx + 1}]: {_trim_to_budget(hunk, 72)}"
        for idx, hunk in enumerate(condensed_hunks[:max_hunks])
    ]
    dropped_hunks_limit = max(0, len(condensed_hunks) - len(hunk_lines))

    snippets = [str(item).strip() for item in (selected_snippets or []) if str(item).strip()]
    finding_lines = [
        f"- signal: {_trim_to_budget(item.split(':', 1)[0], 12)}"
        for item in snippets[:max_findings]
    ]
    dropped_findings = max(0, len(snippets) - len(finding_lines))

    locators_lines = [
        *grouped_summary_lines[:max_findings],
        *file_lines,
        *finding_lines,
    ]
    messages, stats = _build_messages(
        system_content=(
            "You are RepoBrain PR reviewer. Be usersafe and deterministic. "
            "Use hierarchical synthesis: (1) PR metadata summary, (2) targeted evidence, "
            "(3) concise final review. Focus on risks, impact, and practical next steps."
        ),
        task_line="Task: produce concise PR review summary.",
        query=query,
        locators_lines=locators_lines,
        diff_hunks=hunk_lines,
        selected_snippets=[],
        max_input_tokens=max_input_tokens,
    )
    stats["review_compacted"] = True
    stats["review_files_included"] = len(file_lines)
    stats["review_hunks_included"] = len(hunk_lines)
    stats["review_findings_included"] = len(finding_lines)
    stats["dropped_files_count"] = int(dropped_files)
    stats["dropped_findings_count"] = int(dropped_findings)
    stats["dropped_hunks_count"] = int(stats.get("dropped_hunks_count", 0)) + int(dropped_hunks_limit)
    return messages, stats


def build_messages_for_fix(
    *,
    query: str,
    changed_files: list[str],
    diff_hunks: list[str],
    max_input_tokens: int,
    selected_snippets: list[str] | None = None,
    max_hunks: int = 4,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    return _build_patch_messages(
        query=query,
        changed_files=[str(item) for item in changed_files if str(item).strip()],
        diff_hunks=[str(item) for item in diff_hunks if str(item).strip()],
        selected_snippets=[str(item) for item in (selected_snippets or []) if str(item).strip()],
        max_input_tokens=max_input_tokens,
        max_hunks=max_hunks,
    )
