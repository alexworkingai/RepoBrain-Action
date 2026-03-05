from __future__ import annotations

import time
from typing import Any

import requests


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _post_with_retry(
    *,
    url: str,
    token: str,
    payload: dict[str, Any],
    timeout_s: float = 15.0,
    retries: int = 1,
) -> tuple[bool, int | None, dict[str, Any]]:
    last_status: int | None = None
    last_json: dict[str, Any] = {}
    for attempt in range(max(0, retries) + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=_headers(token),
                timeout=timeout_s,
            )
        except requests.RequestException:
            if attempt < retries:
                time.sleep(0.5)
                continue
            return False, None, {"error": "network"}

        last_status = int(getattr(response, "status_code", 0) or 0)
        try:
            data = response.json()
        except ValueError:
            data = {}
        last_json = data if isinstance(data, dict) else {}

        if 200 <= last_status < 300:
            return True, last_status, last_json
        if last_status in {403, 404}:
            return False, last_status, {"error": "forbidden_or_not_found"}
        if last_status == 429 or last_status >= 500:
            if attempt < retries:
                time.sleep(0.5)
                continue
        return False, last_status, {"error": f"http_{last_status}"}

    return False, last_status, last_json


def publish_comment(
    *,
    repo: str,
    token: str,
    issue_or_pr: int,
    markdown: str,
) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/issues/{issue_or_pr}/comments"
    ok, status, data = _post_with_retry(url=url, token=token, payload={"body": markdown}, retries=1)
    return {"ok": ok, "status_code": status, "data": data}


def build_check_annotations(
    locators: list[dict[str, Any]],
    *,
    max_annotations: int = 50,
) -> tuple[list[dict[str, Any]], int]:
    annotations: list[dict[str, Any]] = []
    for item in locators:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "") or "").strip()
        if not path:
            continue
        start_line = int(item.get("start_line", 1) or 1)
        end_line = int(item.get("end_line", start_line) or start_line)
        level = str(item.get("annotation_level", "notice") or "notice").strip().lower()
        if level not in {"failure", "warning", "notice"}:
            level = "notice"
        message = str(item.get("message", "RepoBrain locator")).strip() or "RepoBrain locator"
        title = str(item.get("title", "RepoBrain")).strip() or "RepoBrain"
        annotations.append(
            {
                "path": path,
                "start_line": max(1, start_line),
                "end_line": max(max(1, start_line), end_line),
                "annotation_level": level,
                "message": message,
                "title": title,
            }
        )
    if len(annotations) <= max_annotations:
        return annotations, 0
    return annotations[:max_annotations], len(annotations) - max_annotations


def build_check_run_payload(
    *,
    name: str,
    head_sha: str,
    conclusion: str,
    summary_md: str,
    text_md: str,
    annotations: list[dict[str, Any]],
) -> dict[str, Any]:
    safe_conclusion = str(conclusion or "neutral").strip().lower()
    if safe_conclusion not in {"success", "neutral", "failure", "cancelled"}:
        safe_conclusion = "neutral"

    trimmed_annotations, hidden = build_check_annotations(annotations)
    summary = summary_md.strip() or "RepoBrain check summary."
    if hidden > 0:
        summary = f"{summary}\n\n+{hidden} more annotations omitted."

    return {
        "name": str(name or "RepoBrain"),
        "head_sha": str(head_sha),
        "status": "completed",
        "conclusion": safe_conclusion,
        "output": {
            "title": str(name or "RepoBrain"),
            "summary": summary[:65000],
            "text": (text_md or "")[:65000],
            "annotations": trimmed_annotations,
        },
    }


def publish_check_run(
    *,
    repo: str,
    token: str,
    name: str,
    head_sha: str,
    conclusion: str,
    summary_md: str,
    text_md: str,
    annotations: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = build_check_run_payload(
        name=name,
        head_sha=head_sha,
        conclusion=conclusion,
        summary_md=summary_md,
        text_md=text_md,
        annotations=annotations,
    )
    url = f"https://api.github.com/repos/{repo}/check-runs"
    ok, status, data = _post_with_retry(url=url, token=token, payload=payload, retries=2)
    return {"ok": ok, "status_code": status, "data": data, "payload": payload}


def create_pull_request(
    *,
    repo: str,
    token: str,
    head_branch: str,
    base_branch: str,
    title: str,
    body_md: str,
) -> dict[str, Any]:
    payload = {
        "title": str(title or "RepoBrain: suggested patch"),
        "head": str(head_branch),
        "base": str(base_branch),
        "body": str(body_md or ""),
        "maintainer_can_modify": True,
    }
    url = f"https://api.github.com/repos/{repo}/pulls"
    ok, status, data = _post_with_retry(url=url, token=token, payload=payload, retries=1)
    return {"ok": ok, "status_code": status, "data": data, "payload": payload}
