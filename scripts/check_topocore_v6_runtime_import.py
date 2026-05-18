from __future__ import annotations

import os

from repobrain.topocore_v6_adapter import inspect_topocore_v6_runtime_import


def main() -> int:
    diagnostics = inspect_topocore_v6_runtime_import(
        local_path=str(os.environ.get("RB_TOPOCORE_V6_LOCAL_PATH", "") or "").strip() or None
    )
    if diagnostics.ok:
        print("TOPOCORE_V6_RUNTIME_IMPORT=ok")
        print(f"TOPOCORE_V6_PYTHON={diagnostics.python_executable}")
        print(f"TOPOCORE_V6_VERSION={diagnostics.version or 'unknown'}")
        print("TOPOCORE_V6_PUBLIC_API=ok")
        print("TOPOCORE_V6_HEALTH=ok")
        if diagnostics.health_release_stage:
            print(f"TOPOCORE_V6_HEALTH_RELEASE_STAGE={diagnostics.health_release_stage}")
        if diagnostics.health_api_stability:
            print(f"TOPOCORE_V6_HEALTH_API_STABILITY={diagnostics.health_api_stability}")
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
