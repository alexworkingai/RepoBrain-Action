from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_command_guide_documents_doctor_status_and_score() -> None:
    text = _read("docs/commands/REPOBRAIN_COMMANDS.md")

    assert "/repobrain doctor" in text
    assert "/repobrain status" in text
    assert "/repobrain score" in text
    assert "/repobrain fix-lite" in text
    assert "informational 100-point repository scoring MVP" in text
    assert "compact summary view of the same audit engine" in text


def test_troubleshooting_and_install_guides_reference_doctor() -> None:
    troubleshooting = _read("docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "/repobrain doctor" in troubleshooting
    assert "checks: read" in troubleshooting
    assert "pull-requests: read" in troubleshooting
    assert "do not add by default" in troubleshooting.lower()
    assert "checks: write" in troubleshooting
    assert "pull-requests: write" in troubleshooting
    assert "/repobrain doctor" in install
    assert "after setup" in install.lower() or "first setup check" in install.lower()
    assert "installed private package" in install.lower()


def test_sprint_79_sprint_83_and_sprint_84_architecture_notes_and_coverage_index_entries_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_79_AUDIT_CALIBRATION_DOCTOR_STATUS.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_83_V6_AUDIT_UX_SCORE_SUMMARY.md").exists()
    assert (ROOT / "docs/architecture/SPRINT_84_TOPOCORE_RUNTIME_DISTRIBUTION_GATE.md").exists()
    coverage = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md")

    assert "tests/test_audit_calibration.py" in coverage
    assert "tests/test_doctor_command.py" in coverage
    assert "tests/test_status_command.py" in coverage
    assert "tests/test_doctor_status_docs.py" in coverage
    assert "tests/test_score_command.py" in coverage
    assert "tests/test_topocore_runtime_distribution_mode.py" in coverage
