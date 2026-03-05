from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any


@dataclass(frozen=True)
class VerificationCapabilities:
    ruff_available: bool
    pytest_available: bool
    has_ruff_config: bool
    has_pytest_targets: bool


@dataclass(frozen=True)
class VerificationCheckResult:
    name: str
    status: str  # PASS | FAIL | NOT_RUN
    reason: str
    duration_ms: float
    output_tail: str
    exit_code: int | None


@dataclass(frozen=True)
class VerificationReport:
    overall: str  # PASS | WARN | NOT_RUN
    summary: str
    checks: list[VerificationCheckResult]
    trusted_context: bool
    dynamic_allowed: bool
    time_budget_s: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": self.overall,
            "summary": self.summary,
            "trusted_context": self.trusted_context,
            "dynamic_allowed": self.dynamic_allowed,
            "time_budget_s": self.time_budget_s,
            "checks": [
                {
                    "name": item.name,
                    "status": item.status,
                    "reason": item.reason,
                    "duration_ms": round(item.duration_ms, 3),
                    "output_tail": item.output_tail,
                    "exit_code": item.exit_code,
                }
                for item in self.checks
            ],
        }


@dataclass(frozen=True)
class VerificationBudgets:
    time_budget_s: int = 120
    output_tail_lines: int = 30


def detect_capabilities(repo_root: Path) -> VerificationCapabilities:
    """Detect locally available verification tools and repo targets."""
    root = repo_root.resolve()
    has_ruff_config = (root / "pyproject.toml").exists() or (root / "ruff.toml").exists()
    has_pytest_targets = (
        (root / "tests").exists()
        or (root / "pyproject.toml").exists()
        or (root / "pytest.ini").exists()
    )
    return VerificationCapabilities(
        ruff_available=shutil.which("ruff") is not None,
        pytest_available=shutil.which("pytest") is not None,
        has_ruff_config=has_ruff_config,
        has_pytest_targets=has_pytest_targets,
    )


def _sanitize_output(output: str, repo_root: Path, *, max_lines: int) -> str:
    value = output.replace(str(repo_root.resolve()), "<repo>")
    lines = [line for line in value.splitlines() if line.strip()]
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines)


def _run_check(
    *,
    name: str,
    cmd: list[str],
    repo_root: Path,
    timeout_s: int,
    output_tail_lines: int,
) -> VerificationCheckResult:
    t0 = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_s)),
            check=False,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        merged = f"{completed.stdout}\n{completed.stderr}".strip()
        tail = _sanitize_output(merged, repo_root, max_lines=output_tail_lines)
        if completed.returncode == 0:
            return VerificationCheckResult(
                name=name,
                status="PASS",
                reason="completed",
                duration_ms=elapsed_ms,
                output_tail=tail,
                exit_code=0,
            )
        return VerificationCheckResult(
            name=name,
            status="FAIL",
            reason="non_zero_exit",
            duration_ms=elapsed_ms,
            output_tail=tail,
            exit_code=int(completed.returncode),
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        merged = f"{exc.stdout or ''}\n{exc.stderr or ''}".strip()
        tail = _sanitize_output(merged, repo_root, max_lines=output_tail_lines)
        return VerificationCheckResult(
            name=name,
            status="NOT_RUN",
            reason="timeout",
            duration_ms=elapsed_ms,
            output_tail=tail,
            exit_code=None,
        )
    except OSError:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return VerificationCheckResult(
            name=name,
            status="NOT_RUN",
            reason="spawn_error",
            duration_ms=elapsed_ms,
            output_tail="",
            exit_code=None,
        )


def _not_run(name: str, reason: str) -> VerificationCheckResult:
    return VerificationCheckResult(
        name=name,
        status="NOT_RUN",
        reason=reason,
        duration_ms=0.0,
        output_tail="",
        exit_code=None,
    )


def _overall_status(checks: list[VerificationCheckResult]) -> str:
    if not checks:
        return "NOT_RUN"
    if any(item.status == "FAIL" for item in checks):
        return "WARN"
    if all(item.status == "PASS" for item in checks):
        return "PASS"
    if any(item.status == "PASS" for item in checks):
        return "WARN"
    return "NOT_RUN"


def run_verification(
    plan: list[str],
    caps: VerificationCapabilities,
    budgets: VerificationBudgets,
    *,
    repo_root: Path,
    trusted: bool,
    allow_dynamic: bool,
) -> VerificationReport:
    """Run verification checks using trust-aware gating."""
    checks: list[VerificationCheckResult] = []
    remaining_s = max(1, int(budgets.time_budget_s))
    dynamic_allowed = bool(trusted and allow_dynamic)

    for check_name in plan:
        normalized = str(check_name).strip().lower()
        if normalized == "ruff":
            if not caps.ruff_available:
                checks.append(_not_run("ruff", "tool_unavailable"))
                continue
            if not caps.has_ruff_config:
                checks.append(_not_run("ruff", "config_missing"))
                continue
            result = _run_check(
                name="ruff",
                cmd=["ruff", "check", "."],
                repo_root=repo_root,
                timeout_s=remaining_s,
                output_tail_lines=budgets.output_tail_lines,
            )
            checks.append(result)
            remaining_s = max(1, remaining_s - int(result.duration_ms / 1000))
            continue

        if normalized == "pytest":
            if not caps.pytest_available:
                checks.append(_not_run("pytest", "tool_unavailable"))
                continue
            if not caps.has_pytest_targets:
                checks.append(_not_run("pytest", "targets_missing"))
                continue
            if not trusted:
                checks.append(_not_run("pytest", "untrusted_context"))
                continue
            if not dynamic_allowed:
                checks.append(_not_run("pytest", "dynamic_verify_disabled"))
                continue
            result = _run_check(
                name="pytest",
                cmd=["pytest", "-q"],
                repo_root=repo_root,
                timeout_s=remaining_s,
                output_tail_lines=budgets.output_tail_lines,
            )
            checks.append(result)
            remaining_s = max(1, remaining_s - int(result.duration_ms / 1000))
            continue

        checks.append(_not_run(normalized, "unknown_check"))

    overall = _overall_status(checks)
    pass_count = sum(1 for item in checks if item.status == "PASS")
    fail_count = sum(1 for item in checks if item.status == "FAIL")
    not_run_count = sum(1 for item in checks if item.status == "NOT_RUN")
    summary = (
        f"Verification {overall}: PASS={pass_count}, FAIL={fail_count}, NOT_RUN={not_run_count} "
        f"(trusted={int(bool(trusted))}, dynamic={int(bool(dynamic_allowed))})"
    )
    return VerificationReport(
        overall=overall,
        summary=summary,
        checks=checks,
        trusted_context=bool(trusted),
        dynamic_allowed=bool(dynamic_allowed),
        time_budget_s=int(budgets.time_budget_s),
    )
