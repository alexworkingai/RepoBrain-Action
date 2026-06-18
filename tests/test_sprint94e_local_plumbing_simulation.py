from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "simulate_sprint94e_trusted_partner_plumbing.py"


def test_local_simulation_script_exits_zero_and_prints_local_only_notice() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "This is local plumbing simulation only and does not prove TRUSTED_PARTNER_BETA_READY." in result.stdout


def test_local_simulation_output_covers_both_repos_and_all_commands() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout.splitlines()[-1])
    assert "alexworkingai/Elen-MCP-v.2.2.0" in payload["repos_simulated"]
    assert "alexworkingai/repobrain-community" in payload["repos_simulated"]
    assert "/repobrain score" in payload["commands_simulated"]
    assert "/repobrain audit" in payload["commands_simulated"]
    assert "/repobrain audit --profile premium" in payload["commands_simulated"]


def test_local_simulation_output_keeps_transport_status_and_no_hosted_api() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout.splitlines()[-1])
    assert payload["transport_mode"] == "github_app_queue"
    assert payload["hosted_api_used"] is False
    assert payload["api_url_used"] is False
    assert payload["status"] == "SPRINT_94E_LOCAL_PLUMBING_SIMULATION_PASS"


def test_local_simulation_output_has_processed_and_duplicate_counts_and_no_leakage() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout.splitlines()[-1])
    assert payload["processed_count"] == 6
    assert payload["skipped_duplicate_count"] >= 6
    assert payload["leakage_scan_pass"] is True
    lowered = result.stdout.lower()
    assert "authorization" not in lowered
    assert "bearer " not in lowered
    assert "ghp_" not in lowered
    assert "github_pat_" not in lowered
    assert ".topocore-v6" not in lowered
