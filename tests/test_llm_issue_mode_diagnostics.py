from __future__ import annotations

import pytest

from repobrain.github_flow import _runtime_override_reason_from_skip
from repobrain.output_md import render_answer_markdown


def test_policy_blocked_llm_is_reported_consistently() -> None:
    override = _runtime_override_reason_from_skip('issue_comment_policy_disabled')
    md = render_answer_markdown(
        answer_text='Answer text',
        evidence=[],
        audit_summary={
            'command': 'ask',
            'route_final': 'DEEP',
            'execution_mode': 'retrieval_plus_llm',
            'llm_used': False,
            'llm_skip_reason': 'issue_comment_policy_disabled',
            'llm_decision_reason_short': 'LLM used: multi-source synthesis required after retrieval.',
            'llm_decision_reason_code': 'MULTI_SOURCE_SYNTHESIS_REQUIRED',
            'llm_runtime_override_reason': override,
        },
        next_steps='Validate evidence',
        command='ask',
    )

    assert '### 🤖 LLM' in md
    assert '- LLM: not called' in md
    assert 'policy disabled' in md
    assert 'Runtime override: LLM blocked: issue_comment policy disabled.' not in md
    assert 'LLM used: no (issue_comment_policy_disabled)' not in md


def test_verbose_mode_can_still_render_llm_diagnostics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('RB_REPOBRAIN_VERBOSE_DIAGNOSTICS', '1')
    md = render_answer_markdown(
        answer_text='Answer text',
        evidence=[],
        audit_summary={
            'command': 'ask',
            'route_final': 'DEEP',
            'execution_mode': 'retrieval_plus_llm',
            'llm_used': True,
            'llm_skip_reason': 'n/a',
            'llm_model_used': 'openai/gpt-4.1-mini',
            'llm_tokens_prompt': 12,
            'llm_tokens_completion': 5,
            'llm_tokens_total': 17,
            'llm_decision_reason_short': 'LLM used: multi-source synthesis required after retrieval.',
            'llm_decision_reason_code': 'MULTI_SOURCE_SYNTHESIS_REQUIRED',
        },
        next_steps='Validate evidence',
        command='ask',
    )

    assert 'TKYA LLM decision: used' in md
    assert 'LLM used: yes' in md
    assert 'Tokens used: prompt=12 completion=5 total=17' in md
