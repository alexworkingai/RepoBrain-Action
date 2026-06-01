from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown


def test_locate_route_label_is_locate_and_output_stays_sanitized() -> None:
    md = render_answer_markdown(
        answer_text='unused for locate',
        evidence=[
            EvidenceItem(file_path='.topocore-v6/private.py', line_start=1, line_end=5, score=0.9),
            EvidenceItem(file_path='.github/workflows/repobrain.yml', line_start=1, line_end=20, score=0.8),
        ],
        audit_summary={
            'command': 'locate',
            'route_final': 'REVIEW',
            'selected': 2,
        },
        next_steps='Open evidence links and verify logic',
        command='locate',
    )

    assert 'Route: `LOCATE`' in md
    assert '.topocore-v6' not in md
    assert '.github/workflows/repobrain.yml' in md
