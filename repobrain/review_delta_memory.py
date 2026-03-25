from __future__ import annotations

import hashlib
from pathlib import Path
import time
from typing import Any

import orjson

_CACHE_FORMAT_VERSION = "1.0"
_MAX_STATES = 512


def _cache_path(repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    return repo_root / "artifacts" / ".repobrain_cache" / "review_delta_memory.json"


def _normalize_pr_number(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(text))
    except (TypeError, ValueError):
        return ""


def _normalize_spaces(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _summary_from_labels(labels: list[str], *, max_items: int = 3) -> str:
    cleaned = [str(item).strip() for item in labels if str(item).strip()]
    if not cleaned:
        return "none"
    preview = cleaned[:max_items]
    if len(cleaned) <= max_items:
        return "; ".join(preview)
    return f"{'; '.join(preview)} (+{len(cleaned) - max_items} more)"


def _load_cache(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"format_version": _CACHE_FORMAT_VERSION, "states": {}}
    try:
        payload = orjson.loads(path.read_bytes())
    except (OSError, ValueError):
        return {"format_version": _CACHE_FORMAT_VERSION, "states": {}}
    if not isinstance(payload, dict):
        return {"format_version": _CACHE_FORMAT_VERSION, "states": {}}
    states = payload.get("states", {})
    if not isinstance(states, dict):
        states = {}
    return {
        "format_version": str(payload.get("format_version", _CACHE_FORMAT_VERSION) or _CACHE_FORMAT_VERSION),
        "states": states,
    }


def _save_cache(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    except OSError:
        return


def _finding_rows_from_verdicts(verdicts: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for item in verdicts:
        if not isinstance(item, dict):
            continue
        claim = _normalize_spaces(str(item.get("claim", "") or ""))
        if not claim:
            continue
        anchors_raw = item.get("evidence_anchors", [])
        anchors = (
            sorted({str(anchor).strip() for anchor in anchors_raw if str(anchor).strip()})
            if isinstance(anchors_raw, list)
            else []
        )
        anchor_key = "|".join(anchor.lower() for anchor in anchors)
        identity_source = f"{claim.lower()}::{anchor_key}"
        finding_id = f"va_{_sha256_text(identity_source)}"
        confidence = str(item.get("confidence", "n/a") or "n/a").strip().lower() or "n/a"
        impact = str(item.get("impact", "n/a") or "n/a").strip().lower() or "n/a"
        patchability = str(item.get("patchability", "n/a") or "n/a").strip().lower() or "n/a"
        classification = f"{confidence}|{impact}|{patchability}"
        label = claim
        rows[finding_id] = {
            "finding_id": finding_id,
            "label": label,
            "classification": classification,
        }
    return [rows[key] for key in sorted(rows)]


def _finding_rows_from_confirmed_findings(confirmed_findings: list[str]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for raw in confirmed_findings:
        label = _normalize_spaces(str(raw or ""))
        if not label:
            continue
        finding_id = f"cf_{_sha256_text(label.lower())}"
        rows[finding_id] = {
            "finding_id": finding_id,
            "label": label,
            "classification": "not_tracked",
        }
    return [rows[key] for key in sorted(rows)]


def _extract_current_rows(review: dict[str, Any]) -> tuple[list[dict[str, str]], str, str]:
    verdicts_raw = review.get("evidence_verdicts", [])
    verdicts = [item for item in verdicts_raw if isinstance(item, dict)] if isinstance(verdicts_raw, list) else []
    verdict_rows = _finding_rows_from_verdicts(verdicts)
    if verdict_rows:
        return verdict_rows, "verdict_anchor_identity", "low"

    confirmed_raw = review.get("confirmed_findings", [])
    confirmed = (
        [str(item).strip() for item in confirmed_raw if str(item).strip()]
        if isinstance(confirmed_raw, list)
        else []
    )
    return _finding_rows_from_confirmed_findings(confirmed), "confirmed_finding_text", "elevated"


def _review_state_key(*, pr_number: str, command: str) -> str:
    return f"{command}:{pr_number}"


def review_delta_defaults() -> dict[str, Any]:
    return {
        "review_delta_memory_active": False,
        "review_delta_prior_state_available": False,
        "review_delta_status": "inactive",
        "review_delta_matching_mode": "not_applicable",
        "review_delta_current_vs_prior_summary": "not_applicable",
        "review_delta_new_count": 0,
        "review_delta_persisted_count": 0,
        "review_delta_resolved_count": 0,
        "review_delta_reclassified_count": 0,
        "review_delta_prior_run_id": "not_applicable",
        "review_delta_prior_head_sha": "not_applicable",
        "review_delta_new_summary": "none",
        "review_delta_persisted_summary": "none",
        "review_delta_resolved_summary": "none",
        "review_delta_reclassified_summary": "none",
        "review_delta_uncertainty_level": "not_applicable",
    }


def compute_review_delta_and_store(
    *,
    repo_root: Path | None,
    pr_number: int | str | None,
    command: str,
    review: dict[str, Any],
    head_sha: str,
    run_id: str | None = None,
    persist_state: bool = True,
) -> dict[str, Any]:
    result = review_delta_defaults()
    command_norm = str(command or "").strip().lower()
    if command_norm != "review":
        return result

    pr_number_norm = _normalize_pr_number(pr_number)
    if not pr_number_norm:
        result.update(
            {
                "review_delta_memory_active": False,
                "review_delta_status": "inactive_missing_pr_identity",
                "review_delta_current_vs_prior_summary": "inactive_missing_pr_identity",
            }
        )
        return result

    current_rows, matching_mode, uncertainty_level = _extract_current_rows(review)
    current_by_id = {str(row.get("finding_id", "")): row for row in current_rows if str(row.get("finding_id", ""))}
    current_ids = sorted(current_by_id)

    path = _cache_path(repo_root)
    cache = _load_cache(path)
    states = cache.get("states", {})
    if not isinstance(states, dict):
        states = {}

    state_key = _review_state_key(pr_number=pr_number_norm, command=command_norm)
    prior_entry = states.get(state_key, {})
    prior_rows_raw = prior_entry.get("finding_rows", []) if isinstance(prior_entry, dict) else []
    prior_rows = [item for item in prior_rows_raw if isinstance(item, dict)] if isinstance(prior_rows_raw, list) else []
    prior_by_id = {
        str(item.get("finding_id", "")): item
        for item in prior_rows
        if str(item.get("finding_id", ""))
    }
    prior_ids = sorted(prior_by_id)

    prior_available = bool(prior_ids or (isinstance(prior_entry, dict) and bool(prior_entry)))
    intersection = [finding_id for finding_id in current_ids if finding_id in prior_by_id]
    reclassified = [
        finding_id
        for finding_id in intersection
        if str(current_by_id.get(finding_id, {}).get("classification", "n/a"))
        != str(prior_by_id.get(finding_id, {}).get("classification", "n/a"))
        and str(current_by_id.get(finding_id, {}).get("classification", "n/a")) != "not_tracked"
        and str(prior_by_id.get(finding_id, {}).get("classification", "n/a")) != "not_tracked"
    ]
    persisted = [finding_id for finding_id in intersection if finding_id not in set(reclassified)]
    new_ids = [finding_id for finding_id in current_ids if finding_id not in prior_by_id]
    resolved = [finding_id for finding_id in prior_ids if finding_id not in current_by_id]

    result.update(
        {
            "review_delta_memory_active": True,
            "review_delta_prior_state_available": prior_available,
            "review_delta_status": "prior_state_present" if prior_available else "first_run",
            "review_delta_matching_mode": matching_mode,
            "review_delta_current_vs_prior_summary": (
                "first_run_no_prior_state"
                if not prior_available
                else (
                    "new={new}; persisted={persisted}; resolved={resolved}; reclassified={reclassified}".format(
                        new=len(new_ids),
                        persisted=len(persisted),
                        resolved=len(resolved),
                        reclassified=len(reclassified),
                    )
                )
            ),
            "review_delta_new_count": len(new_ids),
            "review_delta_persisted_count": len(persisted),
            "review_delta_resolved_count": len(resolved),
            "review_delta_reclassified_count": len(reclassified),
            "review_delta_prior_run_id": str(
                prior_entry.get("run_id", "not_applicable") if isinstance(prior_entry, dict) else "not_applicable"
            )
            or "not_applicable",
            "review_delta_prior_head_sha": str(
                prior_entry.get("head_sha", "not_applicable")
                if isinstance(prior_entry, dict)
                else "not_applicable"
            )
            or "not_applicable",
            "review_delta_new_summary": _summary_from_labels(
                [str(current_by_id[item].get("label", "")) for item in new_ids]
            ),
            "review_delta_persisted_summary": _summary_from_labels(
                [str(current_by_id[item].get("label", "")) for item in persisted]
            ),
            "review_delta_resolved_summary": _summary_from_labels(
                [str(prior_by_id[item].get("label", "")) for item in resolved]
            ),
            "review_delta_reclassified_summary": _summary_from_labels(
                [str(current_by_id[item].get("label", "")) for item in reclassified]
            ),
            "review_delta_uncertainty_level": uncertainty_level,
        }
    )

    if persist_state:
        states[state_key] = {
            "pr_number": pr_number_norm,
            "command": command_norm,
            "head_sha": str(head_sha or "").strip() or "not_available",
            "run_id": str(run_id or "").strip() or "not_available",
            "stored_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "stored_at_epoch_s": int(time.time()),
            "finding_rows": current_rows,
            "matching_mode": matching_mode,
        }
        if len(states) > _MAX_STATES:
            ordered = sorted(
                [
                    (
                        key,
                        int(value.get("stored_at_epoch_s", 0) or 0),
                    )
                    for key, value in states.items()
                    if isinstance(value, dict)
                ],
                key=lambda item: item[1],
                reverse=True,
            )
            keep_keys = {item[0] for item in ordered[:_MAX_STATES]}
            states = {key: value for key, value in states.items() if key in keep_keys}
        cache["states"] = states
        _save_cache(path, cache)

    return result
