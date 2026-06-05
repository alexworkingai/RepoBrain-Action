from __future__ import annotations

from pathlib import Path

from repobrain.audit_contract import merge_audit_report_with_v6
from repobrain.evidence import EvidenceItem
from repobrain.github_flow import _maybe_refine_operational_ask_answer
from repobrain.output_md import render_answer_markdown, render_audit_markdown, render_score_markdown


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_final_audit_markdown_filters_v6_maxed_category_leakage() -> None:
    static_report = {
        "overall_score": 78,
        "readiness_band": "GOOD",
        "executive_summary": "Static baseline summary.",
        "categories": [],
        "critical_blockers": [],
        "top_improvements": [],
        "roadmap": {},
        "evidence_summary": {},
        "confidence": "medium",
        "limitations": [],
    }
    validated_response = {
        "overall_score": 77,
        "readiness_band": "GOOD",
        "categories": [
            {
                "key": "dependency_hygiene",
                "title": "Dependency hygiene",
                "score": 8,
                "max_score": 8,
                "label": "STRONG",
                "rationale": "Already maxed.",
                "evidence_paths": ["pyproject.toml"],
            },
            {
                "key": "github_governance",
                "title": "GitHub governance",
                "score": 3,
                "max_score": 8,
                "label": "WEAK",
                "rationale": "Needs work.",
                "evidence_paths": [".github/CODEOWNERS"],
            },
        ],
        "critical_blockers": [],
        "top_improvements": [
            {
                "category": "Dependency hygiene",
                "title": "Improve dependency hygiene coverage",
                "rationale": "Should not survive final output.",
                "expected_score_impact": "medium",
                "affected_files": ["pyproject.toml"],
            },
            {
                "category": "GitHub governance",
                "title": "Improve branch and review governance",
                "rationale": "Should remain visible.",
                "expected_score_impact": "high",
                "affected_files": [".github/CODEOWNERS"],
            },
        ],
        "roadmap": {
            "30_days": [
                "Improve dependency hygiene coverage (Dependency hygiene)",
                "Improve branch and review governance (GitHub governance)",
            ],
            "60_days": ["Keep dependency hygiene drift monitored (Dependency hygiene)"],
            "90_days": [],
        },
        "confidence": "medium",
        "limitations": [],
        "score_adjustments": [],
        "diagnostics": {},
    }

    merged = merge_audit_report_with_v6(static_report=static_report, validated_response=validated_response)
    merged["audit_narrative_text"] = (
        "- Improve dependency hygiene coverage immediately.\n"
        "- Improve branch and review governance with required checks."
    )
    md = render_audit_markdown(
        report=merged,
        audit_summary={"route_final": "AUDIT", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "Improve dependency hygiene coverage" not in md
    assert "Improve branch and review governance" in md
    assert "Keep dependency hygiene drift monitored" in md


def test_final_score_markdown_filters_maxed_category_improvements() -> None:
    report = {
        "overall_score": 77,
        "readiness_band": "GOOD",
        "categories": [
            {"title": "Documentation and onboarding", "score": 8, "max_score": 8, "label": "STRONG", "rationale": "", "evidence_paths": ["README.md"]},
            {"title": "Testing and validation", "score": 8, "max_score": 12, "label": "GOOD", "rationale": "", "evidence_paths": ["tests/test_example.py"]},
        ],
        "critical_blockers": [],
        "top_improvements": [
            {
                "category": "Documentation and onboarding",
                "title": "Improve documentation and onboarding",
                "rationale": "Should be dropped.",
                "expected_score_impact": "medium",
                "affected_files": ["README.md"],
            },
            {
                "category": "Testing and validation",
                "title": "Raise testing and validation confidence",
                "rationale": "Should remain.",
                "expected_score_impact": "high",
                "affected_files": ["tests/test_example.py"],
            },
        ],
    }

    md = render_score_markdown(
        report=report,
        audit_summary={"route_final": "SCORE", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "Improve documentation and onboarding" not in md
    assert "Raise testing and validation confidence" in md


def test_final_pr_score_markdown_filters_maxed_category_improvements() -> None:
    report = {
        "overall_score": 85,
        "readiness_band": "STRONG",
        "categories": [
            {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7, "label": "STRONG", "rationale": "", "evidence_paths": ["README.md"]},
            {"title": "GitHub governance", "score": 3, "max_score": 8, "label": "WEAK", "rationale": "", "evidence_paths": [".github/CODEOWNERS"]},
        ],
        "critical_blockers": [],
        "top_improvements": [
            {
                "category": "AI-readiness / repository intelligence",
                "title": "Improve ai-readiness / repository intelligence",
                "rationale": "Should be dropped.",
                "expected_score_impact": "medium",
                "affected_files": ["README.md"],
            },
            {
                "category": "GitHub governance",
                "title": "Improve branch and review governance",
                "rationale": "Should remain.",
                "expected_score_impact": "high",
                "affected_files": [".github/CODEOWNERS"],
            },
        ],
        "pr_context": {"is_pr": True, "pr_number": 41},
    }

    md = render_score_markdown(
        report=report,
        audit_summary={"route_final": "SCORE", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "Improve ai-readiness / repository intelligence" not in md
    assert "Improve branch and review governance" in md


def test_final_issue_premium_markdown_uses_bounded_fallback_when_text_is_incomplete() -> None:
    report = {
        "overall_score": 77,
        "readiness_band": "GOOD",
        "executive_summary": "Summary",
        "categories": [
            {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7, "label": "STRONG", "rationale": "", "evidence_paths": ["README.md"]},
            {"title": "GitHub governance", "score": 3, "max_score": 8, "label": "WEAK", "rationale": "", "evidence_paths": [".github/CODEOWNERS"]},
        ],
        "critical_blockers": [{"title": "Missing required checks", "category": "GitHub governance", "rationale": "Checks are still deferred.", "evidence_paths": [".github/workflows/ci.yml"]}],
        "top_improvements": [
            {
                "category": "AI-readiness / repository intelligence",
                "title": "Improve ai-readiness / repository intelligence",
                "rationale": "Should be removed.",
                "expected_score_impact": "medium",
                "affected_files": ["README.md"],
            },
            {
                "category": "GitHub governance",
                "title": "Improve branch and review governance",
                "rationale": "Should remain.",
                "expected_score_impact": "high",
                "affected_files": [".github/CODEOWNERS"],
            },
        ],
        "roadmap": {"30_days": [], "60_days": [], "90_days": []},
        "evidence_summary": {},
        "confidence": "medium",
        "limitations": [],
        "audit_narrative_mode": "premium",
        "audit_narrative_text": "- improve ai-readiness / repository intelligence\n- maintaining an informational stance without pres",
    }

    md = render_audit_markdown(
        report=report,
        audit_summary={"route_final": "AUDIT", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "improve ai-readiness / repository intelligence" not in md.lower()
    assert "without pres" not in md
    assert "Premium narrative fallback:" in md


def test_final_pr_premium_markdown_preserves_docs_only_facts_and_filters_maxed_targets() -> None:
    report = {
        "overall_score": 85,
        "readiness_band": "STRONG",
        "executive_summary": "Summary",
        "categories": [
            {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7, "label": "STRONG", "rationale": "", "evidence_paths": ["README.md"]},
            {"title": "GitHub governance", "score": 3, "max_score": 8, "label": "WEAK", "rationale": "", "evidence_paths": [".github/CODEOWNERS"]},
        ],
        "critical_blockers": [],
        "top_improvements": [
            {
                "category": "AI-readiness / repository intelligence",
                "title": "Improve ai-readiness / repository intelligence",
                "rationale": "Should be removed.",
                "expected_score_impact": "medium",
                "affected_files": ["README.md"],
            },
            {
                "category": "GitHub governance",
                "title": "Improve branch and review governance",
                "rationale": "Should remain.",
                "expected_score_impact": "high",
                "affected_files": [".github/CODEOWNERS"],
            },
        ],
        "roadmap": {
            "30_days": ["Improve ai-readiness / repository intelligence (AI-readiness / repository intelligence)", "Improve branch and review governance (GitHub governance)"],
            "60_days": [],
            "90_days": [],
        },
        "evidence_summary": {},
        "confidence": "medium",
        "limitations": [],
        "pr_context": {"is_pr": True, "pr_number": 41},
        "audit_narrative_mode": "premium",
        "audit_narrative_text": "General premium narrative.",
        "audit_pr_narrative_text": (
            "- change type: docs-only\n"
            "- behavior-affecting: no\n"
            "- architecture/runtime impact: no direct impact\n"
            "- security impact: no direct impact\n"
            "- risk level: LOW\n"
            "- Score modified by LLM: no\n"
            "- Improve ai-readiness / repository intelligence"
        ),
    }

    md = render_audit_markdown(
        report=report,
        audit_summary={"route_final": "AUDIT", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "docs-only" in md
    assert "behavior-affecting: no" in md
    assert "architecture/runtime impact: no direct impact" in md
    assert "security impact: no direct impact" in md
    assert "risk level: LOW" in md
    assert "Score modified by LLM: no" in md
    assert "Improve ai-readiness / repository intelligence" not in md
    assert "Improve branch and review governance" in md


def test_final_product_analysis_markdown_uses_evidence_grounded_identity(tmp_path: Path, monkeypatch) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "repobrain.yml",
        "name: RepoBrain\npermissions:\n  contents: read\n  issues: write\n",
    )
    _write(tmp_path / "src" / "mcpServer.ts", "export const mcpServer = true;\n")
    _write(tmp_path / "src" / "index.ts", "export const bootstrap = true;\n")
    _write(tmp_path / "src" / "auth" / "index.ts", "export const auth = true;\n")
    _write(tmp_path / "prisma" / "schema.prisma", "datasource db { provider = 'postgresql' }\n")
    _write(tmp_path / "k8s" / "deployment.yaml", "apiVersion: apps/v1\n")
    _write(tmp_path / "README.md", "# Elen MCP Server\n\nQdrant GitHub OAuth\n")
    _write(tmp_path / "docs" / "ENTERPRISE_READINESS.md", "# Enterprise readiness\n")
    _write(tmp_path / "SECURITY.md", "# Security\n")
    control_plane_root = tmp_path / "repobrain-control"
    _write(control_plane_root / "pyproject.toml", "[project]\nname = 'repobrain-control'\n")
    _write(
        control_plane_root / "docs" / "release" / "PUBLIC_READINESS_ASSESSMENT.md",
        "- current public readiness decision: `SPRINT_92H_IMPLEMENTATION_MERGED_LIVE_RETEST_PENDING`\n",
    )
    _write(
        control_plane_root / "docs" / "release" / "INSTALLED_PACKAGE_LIVE_PROOF.md",
        "- `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`\n",
    )
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(control_plane_root))
    monkeypatch.setenv("RB_TOPOCORE_V6_RUNTIME_MODE", "private_checkout")

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="What does this repository do and what should a partner understand before pilot testing?",
        answer_text="Question: test\nRoute: REVIEW",
        next_steps="placeholder",
        audit_summary={
            "route_final": "REVIEW",
            "requested_backend": "auto",
            "resolved_backend": "not_applicable",
            "fallback_used": "not_applicable",
            "fallback_reason": "status_report_only",
            "llm_used": False,
            "selected": 0,
        },
        github_context={"repository": "alexworkingai/Elen-MCP-v.2.2.0"},
    )
    override_paths = audit_summary["operational_evidence_override_paths"]
    md = render_answer_markdown(
        answer_text=answer_text,
        evidence=[
            EvidenceItem(file_path=path, line_start=1, line_end=1, score=1.0 - (idx * 0.05))
            for idx, path in enumerate(override_paths)
        ],
        audit_summary=audit_summary,
        next_steps=next_steps,
        command="ask",
    )

    assert "Main runtime/application surfaces:" in md
    assert "### 📍 Evidence used" in md
    assert "src/mcpServer.ts" in md
    assert "docs/ENTERPRISE_READINESS.md" in md
    assert ".github/workflows/repobrain.yml" in md
    assert "repobrain/github_flow.py" not in md
