from __future__ import annotations

import sys
from pathlib import Path

from repobrain import topocore_deprecation
from repobrain.topocore_deprecation import get_topocore_deprecation_policy


_ROOT = Path(__file__).resolve().parents[1]


def test_metadata_module_imports_without_runtime_side_effects() -> None:
    module_name = topocore_deprecation.__name__

    assert module_name == "repobrain.topocore_deprecation"
    assert sys.modules[module_name] is topocore_deprecation
    assert "topocore_v6" not in topocore_deprecation.__dict__
    assert "tkya" not in topocore_deprecation.__dict__
    assert "tky_local" not in topocore_deprecation.__dict__


def test_policy_helper_returns_expected_deprecation_state() -> None:
    policy = get_topocore_deprecation_policy()

    assert policy["topocore_v6_status"] == "active_lab_default"
    assert policy["topocore_v6_authoritative"] is True
    assert policy["topocore_v5_status"] == "deprecation_candidate"
    assert policy["topocore_v5_role"] == "fallback_only"
    assert policy["topocore_v5_disabled_by_default"] is True
    assert policy["topocore_v5_allow_deprecated_env"] == "RB_TOPOCORE_ALLOW_DEPRECATED_V5"
    assert policy["topocore_v5_deprecated_not_allowed_reason"] == "deprecated_v5_not_allowed"
    assert policy["topocore_v5_deprecated_allowed_reason"] == "v5_deprecated_emergency_allowed"
    assert policy["topocore_v5_default_disabled_reason"] == "v5_disabled_by_default"
    assert policy["topocore_v5_removal_approved"] is False
    assert policy["topocore_v5_code_deprecation_active"] is False
    assert policy["topocore_v5_fallback_required"] is True
    assert policy["topocore_v5_simulation_env"] == "RB_TOPOCORE_V5_SIMULATE_DISABLED"
    assert policy["topocore_v5_simulated_disabled_reason"] == "v5_simulated_disabled"
    assert policy["topocore_v5_off_simulation_available"] is True


def test_metadata_module_is_dependency_free_and_does_not_enable_patch_behavior() -> None:
    text = (_ROOT / "repobrain" / "topocore_deprecation.py").read_text(encoding="utf-8").lower()

    assert "topocore_v6_adapter" not in text
    assert "tkya.engine" not in text
    assert "apply_patch" not in text
    assert "autofix" not in text
    assert "removal_approved = true" not in text


def test_sprint_62_docs_reference_metadata_and_simulation_plan() -> None:
    text = (_ROOT / "docs" / "architecture" / "TOPOCORE_V6_CODE_LEVEL_V5_DEPRECATION_PREP.md").read_text(
        encoding="utf-8"
    ).lower()

    assert "repobrain/topocore_deprecation.py" in text
    assert "rb_topocore_v5_simulate_disabled=1" in text
    assert "v5-off simulation" in text
    assert "rb_topocore_allow_deprecated_v5=1" in text
