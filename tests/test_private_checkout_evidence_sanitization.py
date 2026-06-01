from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown, render_audit_markdown, render_score_markdown


def _unsafe_and_safe_evidence() -> list[EvidenceItem]:
    return [
        EvidenceItem(file_path='.topocore-v6/.github/workflows/build_runtime_artifact.yml', line_start=1, line_end=10, score=0.99),
        EvidenceItem(file_path='.github/workflows/repobrain.yml', line_start=1, line_end=20, score=0.8),
    ]


def test_ask_locate_and_explain_omit_private_checkout_paths() -> None:
    for command in ('ask', 'locate', 'explain'):
        md = render_answer_markdown(
            answer_text='Answer',
            evidence=_unsafe_and_safe_evidence(),
            audit_summary={'command': command, 'route_final': 'FAST', 'selected': 2},
            next_steps='n/a',
            command=command,
        )
        assert '.topocore-v6' not in md
        assert '.github/workflows/repobrain.yml' in md


def test_audit_and_score_omit_private_checkout_paths() -> None:
    report = {
        'overall_score': 77,
        'readiness_band': 'GOOD',
        'categories': [
            {
                'title': 'Documentation',
                'score': 8,
                'max_score': 10,
                'label': 'GOOD',
                'rationale': 'Grounded in workflow evidence.',
                'evidence_paths': ['.topocore-v6/private.py', '.github/workflows/repobrain.yml'],
            }
        ],
        'critical_blockers': [
            {
                'title': 'None',
                'category': 'docs',
                'rationale': 'Safe output only.',
                'evidence_paths': ['.topocore-v6/private.py', 'README.md'],
            }
        ],
        'top_improvements': [],
    }
    audit_summary = {'route_final': 'AUDIT', 'resolved_backend': 'v6', 'backend_mode': 'v6', 'fallback_used': 'no', 'fallback_reason': 'none'}

    audit_md = render_audit_markdown(report=report, audit_summary=audit_summary)
    score_md = render_score_markdown(report=report, audit_summary=audit_summary)

    for md in (audit_md, score_md):
        assert '.topocore-v6' not in md
        assert '.github/workflows/repobrain.yml' in md or 'README.md' in md
