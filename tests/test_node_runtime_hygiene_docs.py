from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_internal_and_example_workflows_use_updated_action_refs() -> None:
    repobrain = _read('.github/workflows/repobrain.yml')
    example = _read('docs/examples/repobrain_external_pilot_workflow.yml')
    action = _read('action.yml')

    combined = '\n'.join((repobrain, example, action))
    assert 'actions/checkout@v5' in combined
    assert 'actions/setup-python@v6' in combined
    assert 'actions/github-script@v9' in combined
    assert 'actions/checkout@v4' not in combined
    assert 'actions/setup-python@v5' not in combined
    assert 'actions/github-script@v7' not in combined


def test_example_workflow_keeps_read_mostly_permissions_and_no_pull_request_target() -> None:
    text = _read('docs/examples/repobrain_external_pilot_workflow.yml')

    assert 'contents: read' in text
    assert 'checks: read' in text
    assert 'pull-requests: read' in text
    assert 'contents: write' not in text
    assert 'checks: write' not in text
    assert 'pull-requests: write' not in text
    assert 'pull_request_target' not in text


def test_example_workflow_sets_explicit_private_checkout_runtime_mode() -> None:
    text = _read('docs/examples/repobrain_external_pilot_workflow.yml')

    assert 'RB_TOPOCORE_V6_RUNTIME_MODE: private_checkout' in text
