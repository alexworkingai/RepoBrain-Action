from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _build_audit_markdown


@pytest.mark.parametrize(
    ("mode", "kwargs"),
    [
        ("narrative", {"narrative_requested": True}),
        ("executive", {"executive_requested": True}),
        ("premium", {"narrative_requested": True, "profile": "premium"}),
    ],
)
def test_audit_narrative_modes_remove_unsupported_maxed_category_recommendations(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    kwargs: dict[str, object],
) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    monkeypatch.setattr(
        "repobrain.github_flow._maybe_generate_llm_text",
        lambda **_kwargs: (
            "## Narrative interpretation\n"
            "- Improve AI-readiness / repository intelligence next.\n"
            "- Improve dependency hygiene through additional cleanup.\n"
            "- Improve GitHub governance controls and documentation.\n",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "execution_mode": "retrieval_plus_llm",
                "llm_decision_reason_short": f"LLM used: audit {mode} narrative requested after TopoCore scoring.",
                "llm_decision_reason_code": "AUDIT_NARRATIVE_REQUESTED",
                "llm_runtime_override_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tokens_total": 111,
            },
        ),
    )
    monkeypatch.setattr(
        "repobrain.github_flow._maxed_category_names",
        lambda _report: ["AI-readiness / repository intelligence", "Dependency hygiene"],
    )

    build_kwargs = dict(kwargs)
    if mode == "premium":
        monkeypatch.setattr(
            "repobrain.github_flow._resolve_audit_narrative_mode",
            lambda **_k: (True, "premium"),
        )
        build_kwargs = {"narrative_requested": True}
    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Focus on MCP product readiness and partner pilot suitability.",
        tky_mode="local",
        **build_kwargs,
    )

    lowered = markdown.lower()
    assert "improve ai-readiness / repository intelligence" not in lowered
    assert "improve dependency hygiene" not in lowered
    assert "improve github governance controls" in lowered
    assert "improve github governance controls and documentation" not in lowered
    assert "score modified by llm: `no`" in lowered
