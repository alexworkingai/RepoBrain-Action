from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_structural_maintainability_plan_and_script_exist() -> None:
    assert (ROOT / "docs/architecture/STRUCTURAL_MAINTAINABILITY_PLAN.md").exists()
    assert (ROOT / "scripts/check_module_hotspots.py").exists()


def test_structural_plan_lists_hotspots_and_safe_decomposition() -> None:
    text = _read("docs/architecture/STRUCTURAL_MAINTAINABILITY_PLAN.md").lower()

    assert "github_flow.py" in text
    assert "output_md.py" in text
    assert "audit_scoring.py" in text
    assert "safe decomposition order" in text
    assert "no behavior-change principle" in text
    assert "sprint 87/88 refactor candidates" in text


def test_hotspot_script_reports_machine_readable_status() -> None:
    text = _read("scripts/check_module_hotspots.py")

    assert "MODULE_HOTSPOT_STATUS=" in text
    assert "--strict" in text
    assert "warn" in text.lower()
