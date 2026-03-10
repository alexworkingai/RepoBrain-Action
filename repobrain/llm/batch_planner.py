from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any


_PATH_IN_HUNK_RE = re.compile(r"(?:^|\s)(?:a/|b/)([A-Za-z0-9._/\-]+)")


@dataclass(frozen=True)
class Batch:
    batch_id: str
    paths: list[str]
    diff_hunks: list[str]
    snippet_ids: list[str]
    estimated_input_tokens: int


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def _stable_batch_id(*, paths: list[str], snippet_ids: list[str], diff_hunks: list[str]) -> str:
    hunk_hashes = [
        hashlib.blake2s(hunk.encode("utf-8"), digest_size=8).hexdigest()
        for hunk in diff_hunks
    ]
    payload = "|".join(
        [
            "paths:" + ",".join(paths),
            "snippets:" + ",".join(snippet_ids),
            "hunks:" + ",".join(hunk_hashes),
        ]
    )
    return hashlib.blake2s(payload.encode("utf-8"), digest_size=8).hexdigest()


def _extract_hunk_paths(hunk: str) -> list[str]:
    out: list[str] = []
    for match in _PATH_IN_HUNK_RE.finditer(hunk):
        candidate = match.group(1).strip()
        if candidate:
            out.append(candidate)
    return list(dict.fromkeys(out))


def _dedupe(items: list[str]) -> list[str]:
    return [item for item in dict.fromkeys(items) if item]


def _chunk_file_units(
    *,
    path: str,
    snippet_ids: list[str],
    hunks: list[str],
    max_tokens: int,
) -> list[dict[str, Any]]:
    if not hunks:
        estimate = _estimate_tokens(path) + sum(_estimate_tokens(x) for x in snippet_ids)
        return [
            {
                "path": path,
                "snippet_ids": snippet_ids,
                "diff_hunks": [],
                "estimated_input_tokens": estimate,
                "part_index": 0,
            }
        ]

    units: list[dict[str, Any]] = []
    current: list[str] = []
    current_tokens = _estimate_tokens(path) + sum(_estimate_tokens(x) for x in snippet_ids)
    part_index = 0
    for hunk in hunks:
        hunk_tokens = _estimate_tokens(hunk)
        if current and current_tokens + hunk_tokens > max_tokens:
            units.append(
                {
                    "path": path,
                    "snippet_ids": snippet_ids,
                    "diff_hunks": list(current),
                    "estimated_input_tokens": current_tokens,
                    "part_index": part_index,
                }
            )
            part_index += 1
            current = []
            current_tokens = _estimate_tokens(path) + sum(_estimate_tokens(x) for x in snippet_ids)
        current.append(hunk)
        current_tokens += hunk_tokens
    if current:
        units.append(
            {
                "path": path,
                "snippet_ids": snippet_ids,
                "diff_hunks": list(current),
                "estimated_input_tokens": current_tokens,
                "part_index": part_index,
            }
        )
    return units


def plan_batches(
    task_type: str,
    intent: str,
    github_context: dict[str, Any],
    selected_chunks: list[Any],
    limits: dict[str, Any],
    budgets: dict[str, Any],
) -> list[Batch]:
    """Build deterministic file/hunk batches for LLM map stage."""
    _ = task_type
    _ = intent
    max_input_tokens = int(
        budgets.get(
            "max_input_tokens",
            limits.get("max_input_tokens", 7600),
        )
        or 7600
    )
    reserve_tokens = int(budgets.get("reserve_tokens", 800) or 800)
    per_batch_budget = max(400, max_input_tokens - reserve_tokens)

    changed_files_raw = github_context.get("changed_files", [])
    changed_files = sorted(
        _dedupe([str(item).strip() for item in changed_files_raw if str(item).strip()])
    )
    snippets_by_path: dict[str, list[str]] = {path: [] for path in changed_files}
    for chunk in selected_chunks:
        path = str(getattr(chunk, "file_path", "") or "").strip()
        chunk_id = str(getattr(chunk, "chunk_id", "") or "").strip()
        if not path:
            continue
        snippets_by_path.setdefault(path, [])
        if chunk_id:
            snippets_by_path[path].append(chunk_id)

    for path, ids in list(snippets_by_path.items()):
        snippets_by_path[path] = _dedupe(ids)

    hunks_raw = github_context.get("diff_hunks", [])
    hunks = [str(item) for item in hunks_raw if str(item).strip()] if isinstance(hunks_raw, list) else []
    hunks_by_path: dict[str, list[str]] = {path: [] for path in snippets_by_path}
    unassigned_hunks: list[str] = []
    known_paths = sorted(snippets_by_path) or changed_files
    for hunk in hunks:
        matched = False
        referenced_paths = _extract_hunk_paths(hunk)
        for path in referenced_paths:
            if path in hunks_by_path:
                hunks_by_path[path].append(hunk)
                matched = True
                break
        if not matched:
            unassigned_hunks.append(hunk)

    if known_paths:
        for idx, hunk in enumerate(unassigned_hunks):
            target = known_paths[idx % len(known_paths)]
            hunks_by_path.setdefault(target, []).append(hunk)

    if not snippets_by_path and hunks:
        snippets_by_path["(diff-only)"] = []
        hunks_by_path["(diff-only)"] = list(hunks)

    file_units: list[dict[str, Any]] = []
    for path in sorted(snippets_by_path):
        snippet_ids = snippets_by_path.get(path, [])
        path_hunks = hunks_by_path.get(path, [])
        units = _chunk_file_units(
            path=path,
            snippet_ids=snippet_ids,
            hunks=path_hunks,
            max_tokens=per_batch_budget,
        )
        file_units.extend(units)

    file_units.sort(key=lambda item: (str(item.get("path", "")), int(item.get("part_index", 0))))
    batches: list[Batch] = []
    current_paths: list[str] = []
    current_hunks: list[str] = []
    current_snippets: list[str] = []
    current_tokens = 0

    for unit in file_units:
        path = str(unit.get("path", "") or "")
        unit_hunks = [str(item) for item in unit.get("diff_hunks", []) if str(item).strip()]
        unit_snippets = [str(item) for item in unit.get("snippet_ids", []) if str(item).strip()]
        unit_tokens = int(unit.get("estimated_input_tokens", 0) or 0)
        if current_paths and current_tokens + unit_tokens > per_batch_budget:
            paths = _dedupe(current_paths)
            snippet_ids = _dedupe(current_snippets)
            diff_hunks = list(current_hunks)
            batches.append(
                Batch(
                    batch_id=_stable_batch_id(paths=paths, snippet_ids=snippet_ids, diff_hunks=diff_hunks),
                    paths=paths,
                    diff_hunks=diff_hunks,
                    snippet_ids=snippet_ids,
                    estimated_input_tokens=current_tokens,
                )
            )
            current_paths = []
            current_hunks = []
            current_snippets = []
            current_tokens = 0

        current_paths.append(path)
        current_hunks.extend(unit_hunks)
        current_snippets.extend(unit_snippets)
        current_tokens += max(1, unit_tokens)

    if current_paths:
        paths = _dedupe(current_paths)
        snippet_ids = _dedupe(current_snippets)
        diff_hunks = list(current_hunks)
        batches.append(
            Batch(
                batch_id=_stable_batch_id(paths=paths, snippet_ids=snippet_ids, diff_hunks=diff_hunks),
                paths=paths,
                diff_hunks=diff_hunks,
                snippet_ids=snippet_ids,
                estimated_input_tokens=current_tokens,
            )
        )

    return batches
