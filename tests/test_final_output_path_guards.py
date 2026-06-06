from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.audit_contract import merge_audit_report_with_v6
from repobrain.evidence import EvidenceItem
import repobrain.github_flow as github_flow
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
            {"key": "architecture_modularity", "title": "Architecture and modularity", "score": 15, "max_score": 15, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["src/index.ts"]},
            {"key": "code_quality", "title": "Code quality and maintainability", "score": 12, "max_score": 12, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["src/index.ts"]},
            {"key": "testing_validation", "title": "Testing and validation", "score": 8, "max_score": 12, "label": "NEEDS_ATTENTION", "rationale": "Needs work.", "evidence_paths": ["tests/test_example.py"]},
            {"key": "security_posture", "title": "Security posture", "score": 12, "max_score": 12, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["SECURITY.md"]},
            {"key": "cicd_automation", "title": "CI/CD and automation", "score": 8, "max_score": 10, "label": "GOOD", "rationale": "Can improve.", "evidence_paths": [".github/workflows/ci.yml"]},
            {"key": "dependency_hygiene", "title": "Dependency hygiene", "score": 8, "max_score": 8, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["pyproject.toml"]},
            {"key": "docs_onboarding", "title": "Documentation and onboarding", "score": 8, "max_score": 8, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["README.md"]},
            {"key": "release_ops", "title": "Release and operations readiness", "score": 5, "max_score": 8, "label": "NEEDS_ATTENTION", "rationale": "Needs work.", "evidence_paths": ["docs/release.md"]},
            {"key": "github_governance", "title": "GitHub governance", "score": 3, "max_score": 8, "label": "WEAK", "rationale": "Needs work.", "evidence_paths": [".github/CODEOWNERS"]},
            {"key": "ai_readiness", "title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7, "label": "STRONG", "rationale": "Already maxed.", "evidence_paths": ["README.md"]},
        ],
        "critical_blockers": [],
        "top_improvements": [],
        "roadmap": {
            "30_days": ["Raise testing and validation confidence (Testing and validation)"],
            "60_days": [
                "Raise release and operations readiness confidence (Release and operations readiness)",
                "Raise github governance confidence (GitHub governance)",
            ],
            "90_days": ["Improve github governance (GitHub governance)"],
            "priorities": [
                "Improve release and operations readiness",
                "Improve ai-readiness / repository intelligence",
                "Improve dependency hygiene",
                "Improve documentation",
                "Improve automation coverage",
            ],
        },
        "confidence": "medium",
        "limitations": [],
        "score_adjustments": [],
        "diagnostics": {},
    }

    merged = merge_audit_report_with_v6(static_report=static_report, validated_response=validated_response)
    merged["audit_narrative_text"] = "Narrative summary."
    md = render_audit_markdown(
        report=merged,
        audit_summary={"route_final": "AUDIT", "resolved_backend": "v6", "fallback_used": "no", "fallback_reason": "none"},
    )

    assert "30/60/90-day roadmap" not in md
    assert "30 days" not in md
    assert "60 days" not in md
    assert "90 days" not in md
    assert "## Recommended next priorities" in md
    assert "Improve ai-readiness / repository intelligence" not in md
    assert "Improve AI-readiness / repository intelligence" not in md
    assert "Improve repository intelligence" not in md
    assert "repository intelligence capabilities" not in md
    assert "AI-readiness enhancements" not in md
    assert "Improve dependency hygiene" not in md
    assert "Improve documentation" not in md
    assert "Raise testing and validation confidence" in md
    assert "Raise release and operations readiness confidence" in md
    assert "Raise github governance confidence" in md
    assert "Improve github governance" in md
    assert "Improve release and operations readiness" in md
    assert "Improve automation coverage" in md


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

    assert "30/60/90-day decisions" not in md
    assert "30 days" not in md
    assert "60 days" not in md
    assert "90 days" not in md
    assert "improve ai-readiness / repository intelligence" not in md.lower()
    assert "without pres" not in md
    assert "Premium narrative fallback:" in md


def test_final_issue_premium_markdown_strips_repository_intelligence_from_mixed_allowed_sentence() -> None:
    report = {
        "overall_score": 77,
        "readiness_band": "GOOD",
        "executive_summary": "Summary",
        "categories": [
            {"title": "AI-readiness / repository intelligence", "score": 7, "max_score": 7, "label": "STRONG", "rationale": "", "evidence_paths": ["README.md"]},
            {"title": "CI/CD and automation", "score": 8, "max_score": 10, "label": "GOOD", "rationale": "", "evidence_paths": [".github/workflows/ci.yml"]},
            {"title": "GitHub governance", "score": 3, "max_score": 8, "label": "WEAK", "rationale": "", "evidence_paths": [".github/CODEOWNERS"]},
        ],
        "critical_blockers": [],
        "top_improvements": [],
        "roadmap": {"30_days": [], "60_days": [], "90_days": []},
        "evidence_summary": {},
        "confidence": "medium",
        "limitations": [],
        "audit_narrative_mode": "premium",
        "audit_narrative_text": (
            "The recommended priorities focus on raising confidence in testing, release readiness, and governance, "
            "alongside improving automation and repository intelligence capabilities."
        ),
    }

    md = render_audit_markdown(
        report=report,
        audit_summary={
            "route_final": "AUDIT",
            "resolved_backend": "v6",
            "fallback_used": "no",
            "fallback_reason": "none",
            "audit_narrative_requested": True,
            "audit_narrative_mode": "premium",
        },
    )

    assert "repository intelligence capabilities" not in md.lower()
    assert "improve ai-readiness" not in md.lower()
    assert "ai-readiness capabilities" not in md.lower()
    assert "ai-readiness improvements" not in md.lower()
    assert "improving automation" in md.lower() or "ci/cd automation" in md.lower()
    assert "- Score modified by LLM: `no`" in md


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
            "- The recommended priorities focus on raising confidence in testing, release readiness, and governance, alongside improving automation and repository intelligence capabilities.\n"
            "- Improve ai-readiness / repository intelligence"
        ),
    }

    md = render_audit_markdown(
        report=report,
        audit_summary={
            "route_final": "AUDIT",
            "resolved_backend": "v6",
            "fallback_used": "no",
            "fallback_reason": "none",
            "audit_narrative_requested": True,
            "audit_narrative_mode": "premium",
        },
    )

    assert "30/60/90-day roadmap" not in md
    assert "30/60/90-day decisions" not in md
    assert "30 days" not in md
    assert "60 days" not in md
    assert "90 days" not in md
    assert "docs-only" in md
    assert "behavior-affecting: no" in md
    assert "architecture/runtime impact: no direct impact" in md
    assert "security impact: no direct impact" in md
    assert "risk level: LOW" in md
    assert "Score modified by LLM: no" in md
    assert "Improve ai-readiness / repository intelligence" not in md
    assert "repository intelligence capabilities" not in md.lower()
    assert "improving automation" in md.lower() or "ci/cd automation" in md.lower()
    assert "Improve branch and review governance" in md


def test_final_product_analysis_markdown_uses_evidence_grounded_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(
        tmp_path / ".github" / "workflows" / "repobrain.yml",
        "name: RepoBrain\npermissions:\n  contents: read\n  issues: write\n",
    )
    _write(tmp_path / "src" / "mcpServer.ts", "export const mcpServer = true;\n")
    _write(tmp_path / "src" / "index.ts", "export const bootstrap = true;\n")
    _write(tmp_path / "src" / "runtimePaths.ts", "export const runtimePaths = true;\n")
    _write(tmp_path / "apps" / "console" / "src" / "main.tsx", "export const app = true;\n")
    _write(tmp_path / "src" / "auth" / "index.ts", "export const auth = true;\n")
    _write(tmp_path / "src" / "admin" / "routes.ts", "export const admin = true;\n")
    _write(tmp_path / "prisma" / "schema.prisma", "datasource db { provider = 'postgresql' }\n")
    _write(tmp_path / "k8s" / "deployment.yaml", "apiVersion: apps/v1\n")
    _write(tmp_path / "Dockerfile", "FROM node:20\n")
    _write(tmp_path / "README.md", "# Elen MCP Server\n\nQdrant GitHub OAuth\n")
    _write(tmp_path / "docs" / "ENTERPRISE_READINESS.md", "# Enterprise readiness\n")
    _write(tmp_path / "docs" / "ARCHITECTURE.md", "# Architecture\n")
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

    assert "Evidence-backed runtime/application surfaces:" in md
    assert "Evidence used" in md
    assert "src/mcpServer.ts" in md
    assert "src/runtimePaths.ts" in md
    assert "apps/console/src/main.tsx" in md
    assert "src/admin" in md
    assert ".github/workflows/repobrain.yml" in md
    assert "Dockerfile" not in md
    assert "docker-compose" not in md
    assert "k8s" not in md
    assert "Qdrant" not in md
    assert "OAuth" not in md
    assert "JWKS" not in md
    assert "Prometheus" not in md
    assert "OpenTelemetry" not in md
    assert "Grafana" not in md
    assert "GitLab" not in md
    assert "SECURITY.md" not in md
    assert "docs/ARCHITECTURE.md" not in md
    assert "docs/API_ENDPOINTS.md" not in md
    assert "docs/ENTERPRISE_READINESS.md" not in md
    assert "docs/repobrain_pilot.md" not in md
    assert "SPRINT_92H_" not in md
    assert "Run the Sprint 92H live issue/PR retest" not in md
    assert "repobrain/github_flow.py" not in md


def test_final_product_analysis_markdown_can_expand_only_selected_extra_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / ".github" / "workflows" / "repobrain.yml", "name: RepoBrain\n")
    _write(tmp_path / "src" / "mcpServer.ts", "export const mcpServer = true;\n")
    _write(tmp_path / "src" / "index.ts", "export const bootstrap = true;\n")
    _write(tmp_path / "src" / "runtimePaths.ts", "export const runtimePaths = true;\n")
    _write(tmp_path / "apps" / "console" / "src" / "main.tsx", "export const app = true;\n")
    _write(tmp_path / "src" / "auth" / "index.ts", "export const auth = true;\n")
    _write(tmp_path / "src" / "admin" / "routes.ts", "export const admin = true;\n")
    _write(tmp_path / "prisma" / "schema.prisma", "datasource db { provider = 'postgresql' }\n")
    _write(tmp_path / "Dockerfile", "FROM node:20\n")
    _write(tmp_path / "k8s" / "deployment.yaml", "apiVersion: apps/v1\n")
    _write(tmp_path / "SECURITY.md", "# Security\n")
    _write(tmp_path / "docs" / "ARCHITECTURE.md", "# Architecture\n")
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
    monkeypatch.setattr(
        github_flow,
        "_target_repo_product_analysis_evidence_paths",
        lambda _repo_root: [
            ".github/workflows/repobrain.yml",
            "src/mcpServer.ts",
            "src/index.ts",
            "src/runtimePaths.ts",
            "apps/console/src/main.tsx",
            "src/auth",
            "src/admin",
            "prisma",
            "Dockerfile",
            "k8s",
            "SECURITY.md",
            "docs/ARCHITECTURE.md",
        ],
    )

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="What is this repository, what are its main runtime surfaces, and what should a partner understand before pilot testing?",
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
    md = render_answer_markdown(
        answer_text=answer_text,
        evidence=[
            EvidenceItem(file_path=path, line_start=1, line_end=1, score=1.0 - (idx * 0.05))
            for idx, path in enumerate(audit_summary["operational_evidence_override_paths"])
        ],
        audit_summary=audit_summary,
        next_steps=next_steps,
        command="ask",
    )

    assert "Dockerfile" in md
    assert "k8s" in md
    assert "SECURITY.md" in md
    assert "docs/ARCHITECTURE.md" in md
    assert "docs/API_ENDPOINTS.md" not in md
    assert "Qdrant" not in md
    assert "OAuth" not in md
