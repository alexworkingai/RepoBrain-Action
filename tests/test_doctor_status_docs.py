from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_command_guide_documents_doctor_and_status() -> None:
    text = _read("docs/commands/REPOBRAIN_COMMANDS.md")

    assert "/repobrain doctor" in text
    assert "/repobrain status" in text
    assert "/repobrain score" in text
    assert "/repobrain fix-lite" in text
    assert "informational 100-point repository scoring MVP" in text


def test_troubleshooting_and_install_guides_reference_doctor() -> None:
    troubleshooting = _read("docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md")
    install = _read("docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md")

    assert "/repobrain doctor" in troubleshooting
    assert "checks: write" in troubleshooting
    assert "pull-requests: write" in troubleshooting
    assert "/repobrain doctor" in install
    assert "after setup" in install.lower() or "first setup check" in install.lower()


def test_sprint_79_architecture_note_and_coverage_index_entries_exist() -> None:
    assert (ROOT / "docs/architecture/SPRINT_79_AUDIT_CALIBRATION_DOCTOR_STATUS.md").exists()
    coverage = _read("docs/architecture/TOPOCORE_V6_TEST_COVERAGE_INDEX.md")

    assert "tests/test_audit_calibration.py" in coverage
    assert "tests/test_doctor_command.py" in coverage
    assert "tests/test_status_command.py" in coverage
    assert "tests/test_doctor_status_docs.py" in coverage
