from __future__ import annotations

from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class PatchExtractResult:
    patch_text: str
    has_diff_fence: bool
    has_raw_diff: bool
    has_json_envelope: bool
    has_no_patch: bool
    extraction_path: str
    response_chars: int
    reason_code: str


def _result(
    *,
    patch_text: str,
    has_diff_fence: bool,
    has_raw_diff: bool,
    has_json_envelope: bool,
    has_no_patch: bool,
    extraction_path: str,
    response_chars: int,
    reason_code: str,
) -> PatchExtractResult:
    return PatchExtractResult(
        patch_text=patch_text,
        has_diff_fence=has_diff_fence,
        has_raw_diff=has_raw_diff,
        has_json_envelope=has_json_envelope,
        has_no_patch=has_no_patch,
        extraction_path=extraction_path,
        response_chars=response_chars,
        reason_code=reason_code,
    )


def is_unified_diff(patch_text: str) -> bool:
    text = str(patch_text or "")
    if not text.strip():
        return False
    return ("--- " in text and "+++ " in text and "@@ " in text) or text.startswith("diff --git")


def normalize_patch_output(text: str) -> str:
    payload = str(text or "")
    payload = payload.replace("\r\n", "\n").replace("\r", "\n")
    return payload.strip()


def _extract_json_envelope_patch(text: str) -> tuple[str, bool, bool]:
    candidates = [normalize_patch_output(text)]
    for match in re.finditer(r"```json\s*(.*?)```", candidates[0], flags=re.DOTALL | re.IGNORECASE):
        candidates.append(normalize_patch_output(match.group(1)))
    for raw in candidates:
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        result = str(payload.get("result", "") or "").strip().lower()
        if result in {"no_patch", "nopatch"}:
            return "", True, True
        if result == "patch":
            diff = payload.get("diff")
            if isinstance(diff, str) and diff.strip():
                return normalize_patch_output(diff), True, False
    return "", False, False


def extract_patch_candidate(text: str) -> PatchExtractResult:
    payload = normalize_patch_output(text)
    response_chars = len(payload)

    fence_matches = list(re.finditer(r"```diff\s*(.*?)```", payload, flags=re.DOTALL | re.IGNORECASE))
    has_diff_fence = bool(fence_matches)
    for match in fence_matches:
        candidate = normalize_patch_output(match.group(1))
        if is_unified_diff(candidate):
            return _result(
                patch_text=candidate,
                has_diff_fence=True,
                has_raw_diff=False,
                has_json_envelope=False,
                has_no_patch=False,
                extraction_path="diff_fence",
                response_chars=response_chars,
                reason_code="PATCH_EXTRACTED_DIFF_FENCE",
            )

    has_raw_diff = False
    idx = payload.find("diff --git")
    if idx >= 0:
        candidate = normalize_patch_output(payload[idx:])
        has_raw_diff = True
        if is_unified_diff(candidate):
            return _result(
                patch_text=candidate,
                has_diff_fence=has_diff_fence,
                has_raw_diff=True,
                has_json_envelope=False,
                has_no_patch=False,
                extraction_path="raw_diff",
                response_chars=response_chars,
                reason_code="PATCH_EXTRACTED_RAW_DIFF",
            )
    if payload.startswith("--- ") and "\n+++ " in payload:
        has_raw_diff = True
        if is_unified_diff(payload):
            return _result(
                patch_text=payload,
                has_diff_fence=has_diff_fence,
                has_raw_diff=True,
                has_json_envelope=False,
                has_no_patch=False,
                extraction_path="raw_diff",
                response_chars=response_chars,
                reason_code="PATCH_EXTRACTED_RAW_DIFF",
            )
    idx_plain = payload.find("\n--- ")
    if idx_plain >= 0:
        candidate = normalize_patch_output(payload[idx_plain + 1 :])
        if candidate.startswith("--- ") and "\n+++ " in candidate:
            has_raw_diff = True
            if is_unified_diff(candidate):
                return _result(
                    patch_text=candidate,
                    has_diff_fence=has_diff_fence,
                    has_raw_diff=True,
                    has_json_envelope=False,
                    has_no_patch=False,
                    extraction_path="raw_diff",
                    response_chars=response_chars,
                    reason_code="PATCH_EXTRACTED_RAW_DIFF",
                )

    json_diff, has_json_envelope, json_no_patch = _extract_json_envelope_patch(payload)
    if json_diff and is_unified_diff(json_diff):
        return _result(
            patch_text=json_diff,
            has_diff_fence=has_diff_fence,
            has_raw_diff=has_raw_diff,
            has_json_envelope=True,
            has_no_patch=False,
            extraction_path="json_envelope",
            response_chars=response_chars,
            reason_code="PATCH_EXTRACTED_JSON_ENVELOPE",
        )
    if json_no_patch:
        return _result(
            patch_text="",
            has_diff_fence=has_diff_fence,
            has_raw_diff=has_raw_diff,
            has_json_envelope=True,
            has_no_patch=True,
            extraction_path="no_patch",
            response_chars=response_chars,
            reason_code="NO_PATCH",
        )

    has_no_patch = payload.strip().upper() == "NO_PATCH"
    if has_no_patch:
        return _result(
            patch_text="",
            has_diff_fence=has_diff_fence,
            has_raw_diff=has_raw_diff,
            has_json_envelope=has_json_envelope,
            has_no_patch=True,
            extraction_path="no_patch",
            response_chars=response_chars,
            reason_code="NO_PATCH",
        )

    return _result(
        patch_text="",
        has_diff_fence=has_diff_fence,
        has_raw_diff=has_raw_diff,
        has_json_envelope=has_json_envelope,
        has_no_patch=False,
        extraction_path="none",
        response_chars=response_chars,
        reason_code="PATCH_MISSING",
    )
