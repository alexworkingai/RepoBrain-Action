from __future__ import annotations

import os

from repobrain.topocore_v6_adapter import inspect_topocore_v6_runtime_import


def main() -> int:
    runtime_mode = str(os.environ.get("RB_TOPOCORE_V6_RUNTIME_MODE", "") or "").strip() or "auto"
    diagnostics = inspect_topocore_v6_runtime_import(
        local_path=str(os.environ.get("RB_TOPOCORE_V6_LOCAL_PATH", "") or "").strip() or None,
        runtime_mode=runtime_mode,
    )
    print(f"TOPOCORE_V6_RUNTIME_MODE_REQUESTED={diagnostics.requested_mode or runtime_mode}")
    print(f"TOPOCORE_V6_RUNTIME_MODE_USED={diagnostics.used_mode or 'not_available'}")
    print(f"TOPOCORE_V6_PACKAGE_IMPORT_AVAILABLE={'yes' if diagnostics.package_import_available else 'no'}")
    print(f"TOPOCORE_V6_LOCAL_PATH_CONFIGURED={'yes' if diagnostics.local_path_configured else 'no'}")
    print(f"TOPOCORE_V6_LOCAL_PATH_KIND={diagnostics.local_path_kind or 'not_configured'}")
    if diagnostics.ok:
        print("TOPOCORE_V6_RUNTIME_IMPORT=ok")
        print(f"TOPOCORE_V6_PYTHON={diagnostics.python_executable}")
        print(f"TOPOCORE_V6_VERSION={diagnostics.version or 'unknown'}")
        print("TOPOCORE_V6_PUBLIC_API=ok")
        print("TOPOCORE_V6_HEALTH=ok")
        print(f"TOPOCORE_V6_AUDIT_SCORE_V1_PRESENT={'yes' if diagnostics.audit_score_v1_present else 'no'}")
        if diagnostics.audit_score_contract_version:
            print(f"TOPOCORE_V6_AUDIT_SCORE_V1_CONTRACT={diagnostics.audit_score_contract_version}")
        if diagnostics.health_release_stage:
            print(f"TOPOCORE_V6_HEALTH_RELEASE_STAGE={diagnostics.health_release_stage}")
        if diagnostics.health_api_stability:
            print(f"TOPOCORE_V6_HEALTH_API_STABILITY={diagnostics.health_api_stability}")
        return 0

    if diagnostics.failure_category == "topocore_v6_runtime_disabled":
        print("TOPOCORE_V6_RUNTIME_IMPORT=skipped")
        print(f"TOPOCORE_V6_PYTHON={diagnostics.python_executable}")
        print(f"TOPOCORE_V6_FAILURE_CATEGORY={diagnostics.failure_category}")
        print(f"TOPOCORE_V6_ERROR={diagnostics.error_message_sanitized or 'TopoCore v6 runtime disabled.'}")
        return 0

    print("TOPOCORE_V6_RUNTIME_IMPORT=failed")
    print(f"TOPOCORE_V6_PYTHON={diagnostics.python_executable}")
    print(f"TOPOCORE_V6_FAILURE_CATEGORY={diagnostics.failure_category or 'topocore_v6_runtime_unknown'}")
    print(f"TOPOCORE_V6_ERROR={diagnostics.error_message_sanitized or 'TopoCore v6 runtime import failed.'}")
    if diagnostics.version:
        print(f"TOPOCORE_V6_VERSION={diagnostics.version}")
    if diagnostics.failure_category == "topocore_v6_wrong_python_context":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
