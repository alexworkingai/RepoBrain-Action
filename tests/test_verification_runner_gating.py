from __future__ import annotations

from pathlib import Path
import subprocess

from repobrain.verification_runner import (
    VerificationBudgets,
    VerificationCapabilities,
    run_verification,
)


def _caps() -> VerificationCapabilities:
    return VerificationCapabilities(
        ruff_available=True,
        pytest_available=True,
        has_ruff_config=True,
        has_pytest_targets=True,
    )


def test_untrusted_context_skips_pytest(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr("repobrain.verification_runner.subprocess.run", fake_run)

    report = run_verification(
        plan=["ruff", "pytest"],
        caps=_caps(),
        budgets=VerificationBudgets(time_budget_s=30, output_tail_lines=10),
        repo_root=tmp_path,
        trusted=False,
        allow_dynamic=True,
    )
    assert calls == [["ruff", "check", "."]]
    statuses = {item.name: item.status for item in report.checks}
    reasons = {item.name: item.reason for item in report.checks}
    assert statuses["pytest"] == "NOT_RUN"
    assert reasons["pytest"] == "untrusted_context"


def test_trusted_dynamic_context_runs_pytest(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr("repobrain.verification_runner.subprocess.run", fake_run)

    report = run_verification(
        plan=["ruff", "pytest"],
        caps=_caps(),
        budgets=VerificationBudgets(time_budget_s=30, output_tail_lines=10),
        repo_root=tmp_path,
        trusted=True,
        allow_dynamic=True,
    )
    assert ["ruff", "check", "."] in calls
    assert ["pytest", "-q"] in calls
    statuses = {item.name: item.status for item in report.checks}
    assert statuses["pytest"] == "PASS"
