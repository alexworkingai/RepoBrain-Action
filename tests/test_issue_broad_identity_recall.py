from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _maybe_refine_operational_ask_answer


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_broad_identity_query_expands_across_multiple_repository_surface_families(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write(tmp_path / ".github" / "workflows" / "repobrain.yml", "name: RepoBrain\n")
    _write(tmp_path / "src" / "mcpServer.ts", "export const mcpServer = true;\n")
    _write(tmp_path / "src" / "index.ts", "export const bootstrap = true;\n")
    _write(tmp_path / "src" / "runtimePaths.ts", "export const runtimePaths = true;\n")
    _write(tmp_path / "src" / "auth" / "index.ts", "export const auth = true;\n")
    _write(tmp_path / "src" / "admin" / "routes.ts", "export const adminRoutes = true;\n")
    _write(tmp_path / "apps" / "console" / "src" / "main.tsx", "export const app = true;\n")
    _write(tmp_path / "prisma" / "schema.prisma", "datasource db { provider = \"postgresql\" }\n")
    _write(tmp_path / "k8s" / "deployment.yaml", "apiVersion: apps/v1\n")
    _write(tmp_path / "Dockerfile", "FROM node:20\n")
    _write(tmp_path / "SECURITY.md", "# Security\n")
    _write(tmp_path / "docs" / "ARCHITECTURE.md", "# Architecture\n")
    _write(tmp_path / "docs" / "API_ENDPOINTS.md", "# API\n")
    _write(tmp_path / "docs" / "ENTERPRISE_READINESS.md", "# Enterprise readiness\n")
    _write(tmp_path / "README.md", "# Target Product\nQdrant OAuth Prometheus OpenTelemetry Grafana\n")

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
    _write(
        control_plane_root / "docs" / "security" / "REPO_GOVERNANCE_MODEL.md",
        "- `PROTECTED_MAIN_BASELINE_ENABLED`\n- `GOVERNANCE_PARTIAL_REQUIRED_CHECKS_DEFERRED_SOLO_OWNER_MODEL`\n",
    )
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(control_plane_root))

    answer_text, _next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="What is this repository, what are its main runtime surfaces, and what should a partner understand before pilot testing?",
        answer_text="placeholder",
        next_steps="placeholder",
        audit_summary={"route_final": "FAST", "llm_used": False},
        github_context={"repository": "owner/consumer-repo"},
    )

    assert "Main runtime/application surfaces:" in answer_text
    assert "Security/admin/data surfaces:" in answer_text
    assert "What a partner should check during pilot:" in answer_text
    assert "`src/mcpServer.ts`" in answer_text
    assert "`src/index.ts`" in answer_text
    assert "`src/auth/`" in answer_text
    assert "`src/admin/`" in answer_text
    assert "`apps/console/src/main.tsx`" in answer_text
    assert "`prisma/`" in answer_text
    assert "`k8s/`" in answer_text
    assert "`Dockerfile`" in answer_text
    assert "`docs/ENTERPRISE_READINESS.md`" in answer_text
    assert "RepoBrain-Action currently looks like" not in answer_text
    assert audit_summary["operational_ask_kind"] == "product_analysis"
