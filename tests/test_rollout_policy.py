from pathlib import Path

import repobrain.github_flow as github_flow
from repobrain.config import RepoBrainConfig
from repobrain.tky_provider import CandidateChunk


def _chunks_meta() -> tuple[list[CandidateChunk], str, float]:
    return (
        [
            CandidateChunk(
                chunk_id="repobrain/tky_provider.py:1-8",
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=8,
                score=0.2,
                signature=[1, 2, 3],
            )
        ],
        "artifact_present",
        0.1,
    )


def test_remote_disabled_skips_remote(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(github_flow, "load_or_build_chunks_with_meta", lambda *_args, **_kwargs: _chunks_meta())
    monkeypatch.setattr(
        github_flow,
        "load_config",
        lambda *_args, **_kwargs: RepoBrainConfig(
            tky_remote_enabled=False,
            tky_remote_allow_branches=[],
            tky_remote_allow_repos=[],
        ),
    )
    monkeypatch.setattr(
        "repobrain.tky_remote.requests.post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("remote must be skipped")),
    )

    status = github_flow.run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Where is TKYProvider?",
        issue_number=None,
        tky_mode="remote",
        remote_url="https://example.test/v1/tky/decide",
    )
    audit = github_flow.get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["tky_mode_used"] == "baseline"
    assert audit["remote_skipped_reason"] == "remote_disabled_by_config"


def test_remote_command_allowlist_blocks_locate(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(github_flow, "load_or_build_chunks_with_meta", lambda *_args, **_kwargs: _chunks_meta())
    monkeypatch.setattr(
        github_flow,
        "load_config",
        lambda *_args, **_kwargs: RepoBrainConfig(
            tky_remote_enabled=True,
            tky_remote_allow_commands=["ask", "explain"],
            tky_remote_allow_branches=[],
            tky_remote_allow_repos=[],
        ),
    )
    monkeypatch.setattr(
        "repobrain.tky_remote.requests.post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("remote must be skipped")),
    )

    status = github_flow.run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain locate TKYProvider",
        issue_number=None,
        tky_mode="remote",
        remote_url="https://example.test/v1/tky/decide",
    )
    audit = github_flow.get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["tky_mode_used"] == "baseline"
    assert audit["remote_skipped_reason"] == "command_not_allowed"


def test_remote_repo_allowlist_blocks_other_repo(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(github_flow, "load_or_build_chunks_with_meta", lambda *_args, **_kwargs: _chunks_meta())
    monkeypatch.setattr(
        github_flow,
        "load_config",
        lambda *_args, **_kwargs: RepoBrainConfig(
            tky_remote_enabled=True,
            tky_remote_allow_commands=["ask"],
            tky_remote_allow_branches=[],
            tky_remote_allow_repos=["allowed/repo"],
        ),
    )
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setattr(
        "repobrain.tky_remote.requests.post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("remote must be skipped")),
    )

    status = github_flow.run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Where is TKYProvider?",
        issue_number=None,
        tky_mode="remote",
        remote_url="https://example.test/v1/tky/decide",
    )
    audit = github_flow.get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["tky_mode_used"] == "baseline"
    assert audit["remote_skipped_reason"] == "repo_not_allowed"
