from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from repobrain.topocore_entrypoint import (
    TopoCoreEntrypointAdapter,
    TopoCoreEntrypointConfig,
    TopoCoreEntrypointError,
)


def test_topocore_entrypoint_not_configured_raises_stable_error() -> None:
    adapter = TopoCoreEntrypointAdapter(TopoCoreEntrypointConfig())

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_ENTRYPOINT_NOT_CONFIGURED"


def test_topocore_stub_mode_returns_deterministic_safe_result() -> None:
    adapter = TopoCoreEntrypointAdapter(TopoCoreEntrypointConfig(mode="stub"))

    result = adapter.invoke({"command": "audit", "profile": "premium"})

    assert result.backend == "private_topocore_stub"
    assert result.score == 86
    assert result.verdict == "GOOD"
    assert "stub" in result.capability_markers[0]


def test_topocore_command_mode_can_execute_local_fixture_script(tmp_path: Path) -> None:
    script = tmp_path / "topocore_fixture.py"
    script.write_text(
        "\n".join(
            [
                "import json, sys",
                "json.loads(sys.stdin.read())",
                "print(json.dumps({",
                '  "backend": "private_topocore_fixture",',
                '  "fallback": "not_applicable",',
                '  "score": 81,',
                '  "verdict": "GOOD",',
                '  "blockers_summary": ["No blockers."],',
                '  "warnings_summary": ["Fixture path only."],',
                '  "evidence_summary": ["Fixture processed the request."],',
                '  "public_notes": ["Fixture completed safely."],',
                '  "capability_markers": ["topocore.fixture.v1"]',
                "}))",
            ]
        ),
        encoding="utf-8",
    )
    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(
            command=f"{sys.executable} {script}",
            timeout_s=5,
        )
    )

    result = adapter.invoke({"command": "score"})

    assert result.backend == "private_topocore_fixture"
    assert result.score == 81
    assert result.capability_markers == ["topocore.fixture.v1"]


def test_topocore_command_mode_timeout_returns_stable_error() -> None:
    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["python"], timeout=1)

    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(command="python fake.py", timeout_s=1),
        subprocess_run=_timeout,
    )

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_ENTRYPOINT_TIMEOUT"


def test_topocore_command_mode_invalid_json_returns_stable_error() -> None:
    def _invalid(*args, **kwargs):
        return subprocess.CompletedProcess(args=["python"], returncode=0, stdout="not-json", stderr="")

    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(command="python fake.py"),
        subprocess_run=_invalid,
    )

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_RESPONSE_INVALID"


def test_topocore_command_mode_rejects_unsafe_token_or_authorization_output() -> None:
    def _unsafe(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout='{"backend":"private_topocore","public_notes":["Authorization: Bearer abc.def.ghi"]}',
            stderr="",
        )

    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(command="python fake.py"),
        subprocess_run=_unsafe,
    )

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_RESPONSE_UNSAFE"


def test_topocore_command_mode_rejects_private_topocore_path_output() -> None:
    def _unsafe_path(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout='{"backend":"private_topocore","public_notes":["C:\\\\private\\\\topocore\\\\run.py"]}',
            stderr="",
        )

    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(command="python fake.py"),
        subprocess_run=_unsafe_path,
    )

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_RESPONSE_UNSAFE"


def test_topocore_command_mode_hides_secretive_stderr_in_public_error() -> None:
    def _failed(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["python"],
            returncode=1,
            stdout="",
            stderr="Authorization: Bearer secret-token",
        )

    adapter = TopoCoreEntrypointAdapter(
        TopoCoreEntrypointConfig(command="python fake.py"),
        subprocess_run=_failed,
    )

    with pytest.raises(TopoCoreEntrypointError) as exc_info:
        adapter.invoke({"command": "score"})

    assert exc_info.value.code == "TOPOCORE_ENTRYPOINT_FAILED"
    assert "secret-token" not in exc_info.value.message
