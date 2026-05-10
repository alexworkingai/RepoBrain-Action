from __future__ import annotations

from typing import Any


def _result(
    *,
    status: str,
    reason_code: str,
    reason_short: str,
    valid: bool,
    touched_files: list[str],
    placeholder_detected: bool,
    grounded: bool,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": status,
        "reason_code": reason_code,
        "reason_short": reason_short,
        "valid": valid,
        "touched_files": touched_files,
        "placeholder_detected": placeholder_detected,
        "grounded": grounded,
    }
    if extras:
        payload.update(extras)
    return payload


def _normalize_changed_files(pr_changed_files: list[str] | None) -> list[str]:
    return sorted(
        {
            str(item).strip()
            for item in (pr_changed_files or [])
            if str(item).strip()
        }
    )


def _parse_touched_files(patch_text: str) -> list[str]:
    touched: list[str] = []
    for raw in str(patch_text or "").splitlines():
        line = raw.strip()
        if line.startswith("+++ "):
            path = line[4:].strip()
            if path.startswith("b/"):
                path = path[2:]
            if path and path != "/dev/null":
                touched.append(path)
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                b_path = parts[3].strip()
                if b_path.startswith("b/"):
                    b_path = b_path[2:]
                if b_path:
                    touched.append(b_path)
    return sorted(set(item for item in touched if item))


def _is_unified_diff(patch_text: str) -> bool:
    text = str(patch_text or "")
    if not text.strip():
        return False
    return ("--- " in text and "+++ " in text and "@@ " in text) or text.startswith("diff --git")


def _has_placeholder_markers(patch_text: str) -> bool:
    lowered = str(patch_text or "").lower()
    placeholder_tokens = (
        "path/to/file",
        "your_file",
        "example.py",
        "todo.diff",
        "placeholder",
    )
    return any(token in lowered for token in placeholder_tokens)


def validate_patch_grounding(
    *,
    patch_text: str,
    pr_changed_files: list[str] | None,
    command_type: str,
) -> dict[str, Any]:
    text = str(patch_text or "")
    changed_files = _normalize_changed_files(pr_changed_files)
    if not text.strip():
        return _result(
            status="no_patch",
            reason_code="NO_PATCH",
            reason_short="No patch returned by model/engine.",
            valid=False,
            touched_files=[],
            placeholder_detected=False,
            grounded=False,
        )

    if not _is_unified_diff(text):
        return _result(
            status="patch_validation_failed",
            reason_code="INVALID_PATCH_FORMAT",
            reason_short="Patch validation failed: output is not a unified diff.",
            valid=False,
            touched_files=[],
            placeholder_detected=_has_placeholder_markers(text),
            grounded=False,
        )

    touched_files = _parse_touched_files(text)
    if not touched_files:
        return _result(
            status="patch_validation_failed",
            reason_code="PATCH_WITHOUT_TOUCHED_FILES",
            reason_short="Patch validation failed: no touched files found in diff headers.",
            valid=False,
            touched_files=[],
            placeholder_detected=_has_placeholder_markers(text),
            grounded=False,
        )

    placeholder_detected = _has_placeholder_markers(text)
    if placeholder_detected:
        return _result(
            status="patch_validation_failed",
            reason_code="PLACEHOLDER_PATCH",
            reason_short="Patch validation failed: placeholder or generic patch content detected.",
            valid=False,
            touched_files=touched_files,
            placeholder_detected=True,
            grounded=False,
        )

    if changed_files:
        changed_files_set = set(changed_files)
        unrelated = [path for path in touched_files if path not in changed_files_set]
        if unrelated:
            return _result(
                status="patch_validation_failed",
                reason_code="PATCH_NOT_GROUNDED_IN_PR_FILES",
                reason_short="Patch validation failed: patch touched files outside PR context.",
                valid=False,
                touched_files=touched_files,
                placeholder_detected=False,
                grounded=False,
                extras={"unrelated_files": unrelated},
            )

    return _result(
        status="valid_patch",
        reason_code="PATCH_GROUNDED",
        reason_short="Patch validated against PR grounding context.",
        valid=True,
        touched_files=touched_files,
        placeholder_detected=False,
        grounded=bool(changed_files) if command_type == "fix" else True,
    )
