from pathlib import Path

from repobrain.github_flow import run_github_flow


def test_run_github_flow_dry_run_outputs_markdown_sections(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain ask Где реализована логика TKYProvider?",
        issue_number=None,
        tky_mode="baseline",
    )
    output = capsys.readouterr().out

    assert status == "DRY_RUN_OK"
    assert "Mode=DRY_RUN" in output
    assert "Cmd=ask" in output
    assert "Answer" in output
    assert "Evidence" in output
