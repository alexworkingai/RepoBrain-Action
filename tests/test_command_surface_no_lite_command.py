from __future__ import annotations

from pathlib import Path

from repobrain.commands import parse_command
from repobrain.github_flow import run_github_flow


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_help_and_active_docs_do_not_advertise_lite_alias(capsys) -> None:
    status = run_github_flow(
        repo_root=ROOT,
        dry_run=True,
        comment_text='/repobrain help',
        issue_number=None,
    )
    output = capsys.readouterr().out
    assert status == 'DRY_RUN_OK'
    assert '/repobrain fix-lite' not in output

    active_docs = '\n'.join(
        _read(path)
        for path in (
            'README.md',
            'docs/commands/REPOBRAIN_COMMANDS.md',
            'docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md',
            'docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md',
            'docs/release/FINAL_COMMAND_SURFACE_MATRIX.md',
        )
    )
    assert '/repobrain fix-lite' not in active_docs


def test_old_lite_alias_parses_as_generic_unsupported_command() -> None:
    parsed = parse_command('/repobrain ' + 'fix' + '-lite')
    assert parsed == {'cmd': 'unsupported', 'query': ''}
