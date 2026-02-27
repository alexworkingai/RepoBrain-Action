from pathlib import Path

import requests

import repobrain.github_flow as github_flow
from repobrain.config import RepoBrainConfig
from repobrain.tky_provider import CandidateChunk


def test_remote_error_falls_back_to_baseline_and_records_audit(monkeypatch, capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        github_flow,
        "load_config",
        lambda *_args, **_kwargs: RepoBrainConfig(
            tky_remote_enabled=True,
            tky_remote_allow_commands=("ask", "explain"),
            tky_remote_allow_branches=(),
            tky_remote_allow_repos=(),
            tky_remote_fail_open=True,
        ),
    )

    monkeypatch.setattr(
        github_flow,
        "load_or_build_chunks_with_meta",
        lambda *_args, **_kwargs: (
            [
            CandidateChunk(
                chunk_id="repobrain/tky_provider.py:1-5",
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=5,
                score=0.2,
                signature=[1, 2, 3],
            )
            ],
            "artifact_present",
            0.1,
        ),
    )

    def fake_post(*args, **kwargs):
        raise requests.RequestException("network down")

    monkeypatch.setattr("repobrain.tky_remote.requests.post", fake_post)

    status = github_flow.run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Where is TKYProvider?",
        issue_number=None,
        tky_mode="remote",
        remote_url="https://example.com/v1/tky/decide",
    )
    output = capsys.readouterr().out

    assert status == "DRY_RUN_OK"
    assert "tky_mode_requested" in output
    assert "tky_mode_used" in output
    assert "baseline" in output
    assert "tky_fallback_reason" in output
    assert "remote_error" in output
    assert "fallback_reason_code" in output
