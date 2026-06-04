from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _maybe_refine_operational_ask_answer
from repobrain.output_md import render_answer_markdown


def test_explain_route_label_is_explain() -> None:
    md = render_answer_markdown(
        answer_text='Explanation text',
        evidence=[],
        audit_summary={'command': 'explain', 'route_final': 'FAST'},
        next_steps='n/a',
        command='explain',
    )

    assert 'Route: `EXPLAIN`' in md


def test_operational_explain_produces_real_explanation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workflow = tmp_path / '.github' / 'workflows' / 'repobrain.yml'
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        'name: RepoBrain\njobs:\n  repobrain:\n    steps:\n      - uses: alexworkingai/RepoBrain-Action@main\n',
        encoding='utf-8',
    )
    control_plane_root = tmp_path / 'repobrain-control'
    control_plane_root.mkdir(parents=True, exist_ok=True)
    (control_plane_root / 'pyproject.toml').write_text('[project]\nname = "repobrain-control"\n', encoding='utf-8')
    release_dir = control_plane_root / 'docs' / 'release'
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / 'PUBLIC_READINESS_ASSESSMENT.md').write_text(
        '# Public Readiness Assessment\n\n- current public readiness decision: `PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY`\n',
        encoding='utf-8',
    )
    (release_dir / 'INSTALLED_PACKAGE_LIVE_PROOF.md').write_text(
        '# Installed Package Live Proof\n\n- `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`\n',
        encoding='utf-8',
    )
    monkeypatch.setenv('GITHUB_ACTION_PATH', str(control_plane_root))
    monkeypatch.setenv('RB_TOPOCORE_V6_RUNTIME_MODE', 'installed_package')

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd='explain',
        question='Explain how this repository is connected to RepoBrain and what runtime mode is used.',
        answer_text='Question: test\nRoute: REVIEW',
        next_steps='placeholder',
        audit_summary={
            'route_final': 'REVIEW',
            'requested_backend': 'auto',
            'resolved_backend': 'v6',
            'fallback_used': 'no',
            'fallback_reason': 'none',
        },
        github_context={'repository': 'alexworkingai/Elen-MCP-v.2.2.0'},
    )

    assert 'RepoBrain is connected through the repository workflow.' in answer_text
    assert '`.github/workflows/repobrain.yml`' in answer_text
    assert '`alexworkingai/RepoBrain-Action@main`' in answer_text
    assert 'Runtime policy requested for this run: `installed_package`.' in answer_text
    assert 'installed private package was requested, but no importable runtime package is available in this run.' in answer_text
    assert 'INSTALLED_PACKAGE_LIVE_PROOF_PASSED' in answer_text
    assert '.topocore-v6' not in answer_text
    assert 'private_checkout' not in answer_text
    assert 'Key modules likely involved' not in answer_text
    assert next_steps
    assert audit_summary['route_final'] == 'EXPLAIN'
