from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_rc_tag_and_pinning_plan_doc_exists() -> None:
    assert (ROOT / 'docs/release/RC_TAG_AND_PINNING_PLAN.md').exists()


def test_rc_tag_and_pinning_plan_states_recommended_tag_and_approval_gate() -> None:
    text = _read('docs/release/RC_TAG_AND_PINNING_PLAN.md').lower()

    assert 'v0.5.0-rc.1' in text
    assert 'annotated tag preferred' in text
    assert 'only after explicit owner approval' in text
    assert 'do not create the tag automatically in sprint 85' in text
    assert 'rc_tag_ready_pending_owner_approval' in text
    assert 'do not rewrite public tags' in text


def test_rc_tag_and_pinning_plan_does_not_claim_tag_created_without_approval() -> None:
    text = _read('docs/release/RC_TAG_AND_PINNING_PLAN.md').lower()

    assert 'tag created: `yes`' not in text
    assert 'rc_tag_created' in text
    assert 'if owner approval is later explicit and the tag is created' in text
