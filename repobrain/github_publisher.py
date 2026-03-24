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


def _header_value(headers: Any, key: str) -> str:
    if headers is None:
        return ""
    try:
        value = headers.get(key) or headers.get(key.lower())
    except AttributeError:
        value = ""
    return str(value or "").strip()


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
    pr_number: int | None = None,
    command: str | None = None,
) -> dict[str, Any]:
    safe_conclusion = str(conclusion or "neutral").strip().lower()
    if safe_conclusion not in {"success", "neutral", "failure", "cancelled"}:
        safe_conclusion = "neutral"

    trimmed_annotations, hidden = build_check_annotations(annotations)
    summary = summary_md.strip() or "RepoBrain check summary."
    if hidden > 0:
        summary = f"{summary}\n\n+{hidden} more annotations omitted."

    payload: dict[str, Any] = {
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
    if isinstance(pr_number, int) and pr_number > 0:
        payload["pr_number"] = pr_number
    safe_command = str(command or "").strip().lower()
    if safe_command:
        payload["command"] = safe_command
    return payload


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
    required_permissions_header = "n/a"
    ok = False
    status: int | None = None
    data: dict[str, Any] = {}
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=_headers(token),
                timeout=15,
            )
        except requests.RequestException:
            if attempt < 2:
                time.sleep(0.5)
                continue
            status = None
            data = {"error": "network"}
            break

        status = int(getattr(response, "status_code", 0) or 0)
        try:
            raw_data = response.json()
            data = raw_data if isinstance(raw_data, dict) else {}
        except ValueError:
            data = {}
        response_headers = getattr(response, "headers", {})
        required_permissions = _header_value(response_headers, "X-Accepted-GitHub-Permissions")
        if required_permissions:
            required_permissions_header = required_permissions
        if 200 <= status < 300:
            ok = True
            break
        if status in {429, 500, 502, 503, 504} and attempt < 2:
            time.sleep(0.5)
            continue
        break
    return {
        "ok": ok,
        "status_code": status,
        "data": data,
        "payload": payload,
        "required_permissions_header": required_permissions_header,
    }


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
