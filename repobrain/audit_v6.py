from __future__ import annotations

import copy
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from repobrain.audit_contract import (
    AuditContractError,
    append_contract_rejection_limitation,
    append_static_contract_limitation,
    build_audit_score_request_v1,
    merge_audit_report_with_v6,
    validate_audit_score_response_v1,
)
from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterRuntimeError,
)


def enrich_audit_report_with_optional_v6(
    *,
    repo_root: Path,
    report: Mapping[str, Any],
    github_context: Mapping[str, Any] | None,
    query: str,
    tky_mode: str,
    requested_backend: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    static_report = copy.deepcopy(dict(report))
    adapter = RepoBrainTopoCoreV6Adapter()
    local_path = str(os.environ.get("RB_TOPOCORE_V6_LOCAL_PATH", "") or "").strip() or None
    runtime_mode = str(os.environ.get("RB_TOPOCORE_V6_RUNTIME_MODE", "") or "").strip() or "auto"
    capability = adapter.audit_score_v1_capability_local(
        local_path=local_path,
        runtime_mode=runtime_mode,
    )

    base_summary = {
        "tky_mode_requested": tky_mode,
        "tky_mode_used": tky_mode,
        "tkya_mode": "audit_mvp_static",
        "tkya_backend": "audit_mvp_static",
        "requested_backend": requested_backend,
        "resolved_backend": "not_applicable",
        "backend_mode": "audit_mvp_static_scoring",
        "fallback_used": "not_applicable",
        "fallback_reason": "audit_static_scoring",
        "scope_status": "repository_audit",
        "llm_used": False,
        "llm_skip_reason": "audit_mvp_static_scoring",
        "audit_mode": "static_mvp",
        "audit_contract_status": "not_requested",
        "audit_contract_warning": "",
        "audit_contract_capability": capability.get("status", "unknown"),
    }

    try:
        request = build_audit_score_request_v1(
            repo_root=repo_root,
            report=static_report,
            github_context=github_context,
            query=query,
        )
    except AuditContractError as exc:
        degraded = append_contract_rejection_limitation(
            static_report,
            f"v6 audit contract request failed safety validation: {exc}",
        )
        summary = dict(base_summary)
        summary.update(
            {
                "audit_mode": "static_contract_rejected",
                "audit_contract_status": "request_rejected",
                "audit_contract_warning": "v6 audit request rejected by contract guard",
                "backend_mode": "audit_v6_contract_rejected_static",
                "fallback_reason": "audit_v6_contract_request_rejected_static_scoring",
            }
        )
        return degraded, summary

    try:
        raw_response = adapter.run_audit_score_v1_local(
            request,
            local_path=local_path,
            runtime_mode=runtime_mode,
        )
    except RepoBrainV6AdapterRuntimeError:
        degraded = append_static_contract_limitation(
            static_report,
            "TopoCore v6 deep scoring capability was not available in this runtime; the static scoring baseline was retained with the Sprint 81 contract guard.",
        )
        summary = dict(base_summary)
        summary.update(
            {
                "audit_mode": "static_contract_ready",
                "audit_contract_status": capability.get("status", "capability_unavailable"),
                "audit_contract_warning": "",
                "tkya_mode": "audit_v6_contract_ready_static",
                "tkya_backend": "audit_v6_contract_ready_static",
                "backend_mode": "audit_v6_contract_ready_static",
                "fallback_reason": "audit_v6_capability_unavailable_static_scoring",
                "llm_skip_reason": "audit_v6_capability_unavailable_static_scoring",
            }
        )
        return degraded, summary

    try:
        validated = validate_audit_score_response_v1(raw_response)
    except AuditContractError:
        degraded = append_contract_rejection_limitation(
            static_report,
            "TopoCore v6 audit response was rejected by the contract guard; the static scoring baseline was retained.",
        )
        summary = dict(base_summary)
        summary.update(
            {
                "audit_mode": "static_contract_rejected",
                "audit_contract_status": "response_rejected",
                "audit_contract_warning": "v6 audit response rejected by contract guard",
                "resolved_backend": "v6_rejected",
                "tkya_mode": "audit_v6_contract_rejected_static",
                "tkya_backend": "audit_v6_contract_rejected_static",
                "backend_mode": "audit_v6_contract_rejected_static",
                "fallback_reason": "audit_v6_contract_rejected_static_scoring",
                "llm_skip_reason": "audit_v6_contract_rejected_static_scoring",
            }
        )
        return degraded, summary

    merged = merge_audit_report_with_v6(static_report=static_report, validated_response=validated)
    diagnostics = validated.get("diagnostics", {}) if isinstance(validated.get("diagnostics", {}), Mapping) else {}
    summary = dict(base_summary)
    summary.update(
        {
            "audit_mode": "v6_enriched",
            "audit_contract_status": str(validated.get("status", "ok") or "ok"),
            "audit_contract_warning": "",
            "tkya_mode": "audit_v6_enriched",
            "tkya_backend": "audit_v6_enriched",
            "resolved_backend": "v6",
            "backend_mode": "audit_v6_enriched",
            "fallback_used": "no",
            "fallback_reason": "none",
            "llm_skip_reason": "audit_v6_enriched",
            "topocore_capability_version": str(diagnostics.get("capability_version", "") or ""),
        }
    )
    return merged, summary
