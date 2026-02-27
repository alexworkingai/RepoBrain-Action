from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from repobrain.index_store import build_index


def _prepare_repo(tmp_path: Path, *, fail_open: bool) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    (repo_root / "repobrain").mkdir(parents=True, exist_ok=True)
    (repo_root / "repobrain" / "sample.py").write_text(
        "class TKYProvider:\n    pass\n",
        encoding="utf-8",
    )
    (repo_root / "README.md").write_text("RepoBrain test\n", encoding="utf-8")
    (repo_root / ".repobrain.yml").write_text(
        (
            "tky:\n"
            "  remote_enabled: true\n"
            "  remote_allow_branches: []\n"
            "  remote_allow_repos: []\n"
            f"  remote_fail_open: {'true' if fail_open else 'false'}\n"
        ),
        encoding="utf-8",
    )
    index_path = repo_root / "artifacts" / "index-package.zip"
    build_index(root=repo_root, out_zip=index_path, store_text=False)
    return repo_root, index_path


def _run_ask(repo_root: Path, index_path: Path) -> subprocess.CompletedProcess[str]:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_ask.py"
    env = os.environ.copy()
    base_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(Path(__file__).resolve().parents[1])
        + (os.pathsep + base_pythonpath if base_pythonpath else "")
    )
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--question",
            "Where is TKYProvider?",
            "--tky-mode",
            "remote",
            "--remote-url",
            "http://127.0.0.1:9/v1/tky/decide",
            "--index-path",
            str(index_path),
        ],
        cwd=repo_root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_run_ask_remote_down_fallback(tmp_path: Path) -> None:
    repo_root, index_path = _prepare_repo(tmp_path, fail_open=True)
    proc = _run_ask(repo_root, index_path)
    assert proc.returncode == 0
    assert "TKY: fallback baseline (REMOTE_" in proc.stdout
    assert "Traceback" not in proc.stderr


def test_run_ask_remote_down_fail_closed_returns_nonzero(tmp_path: Path) -> None:
    repo_root, index_path = _prepare_repo(tmp_path, fail_open=False)
    proc = _run_ask(repo_root, index_path)
    assert proc.returncode != 0
    assert "Remote TKY unavailable and fail-open is disabled." in proc.stdout
    assert "Traceback" not in proc.stderr
