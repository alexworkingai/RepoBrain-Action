from __future__ import annotations

from repobrain.output_md import _compact_backend_label, _compact_fallback_label


def test_partner_default_runtime_wording_is_not_raw_backend_arrow() -> None:
    audit_summary = {
        "requested_backend": "auto",
        "resolved_backend": "v6",
        "fallback_used": "no",
        "fallback_reason": "none",
    }

    assert _compact_backend_label(audit_summary) == "private runtime resolved successfully"
    assert _compact_fallback_label(audit_summary) == "no fallback used"

