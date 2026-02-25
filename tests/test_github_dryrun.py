from pathlib import Path

from scripts.run_github import run_github_flow


def test_run_github_flow_dry_run_outputs_markdown_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    output = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        tky_mode="baseline",
        comment_text="/repobrain ask Где реализована логика TKYProvider?",
    )

    assert "Mode=DRY_RUN" in output
    assert "Cmd=ask" in output
    assert "### ✅ Answer" in output
    assert "### 📌 Evidence" in output
