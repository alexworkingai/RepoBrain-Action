from __future__ import annotations

from dataclasses import dataclass
import re

_PLACEHOLDER_RE = re.compile(
    r"(?i)(path/to/file|your_file|placeholder|insert diff here|example diff|todo(?:\s*:)?.*patch|fixme.*patch)"
)
_GENERIC_TEXT_RE = re.compile(
    r"(?i)(here is (the )?patch|apply this patch|run this command|you can fix by)"
)


@dataclass(frozen=True)
class PatchGuardDecision:
    triggered: bool
    reason_code: str
    reason_short: str


def evaluate_patch_payload(text: str) -> PatchGuardDecision:
    payload = str(text or "").strip()
    if not payload:
        return PatchGuardDecision(False, "EMPTY_OUTPUT", "No patch output provided.")

    lowered = payload.lower()
    has_diff_markers = ("diff --git" in lowered) or ("--- " in payload and "\n+++ " in payload)
    if _PLACEHOLDER_RE.search(payload):
        return PatchGuardDecision(
            True,
            "PATCH_PLACEHOLDER_DETECTED",
            "Patch output rejected: placeholder or template-style content detected.",
        )
    if _GENERIC_TEXT_RE.search(payload) and not has_diff_markers:
        return PatchGuardDecision(
            True,
            "PATCH_GENERIC_TEXT",
            "Patch output rejected: generic prose without concrete unified diff.",
        )
    return PatchGuardDecision(False, "PATCH_GUARD_CLEAR", "Patch guard did not detect placeholder patterns.")
