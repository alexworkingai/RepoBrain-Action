from __future__ import annotations

from typing import Any, Mapping


_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_DOC_FILENAMES = {
    "readme.md",
    "changelog.md",
    "license",
    "license.md",
    "contributing.md",
    "security.md",
}


def is_docs_only_path(path: str) -> bool:
    lowered = str(path or "").strip().lower()
    if not lowered:
        return False
    if lowered.startswith("docs/"):
        return True
    if lowered.startswith(".github/workflows/"):
        return False
    if lowered.startswith(".github/") and lowered.endswith(_DOC_EXTENSIONS):
        return True
    filename = lowered.rsplit("/", 1)[-1]
    if filename in _DOC_FILENAMES:
        return True
    return lowered.endswith(_DOC_EXTENSIONS)


def build_pr_impact_facts(
    *,
    github_context: Mapping[str, Any] | None = None,
    changed_files: list[str] | None = None,
    pr_number: int | None = None,
    primary_segment: str = "none",
    support_segments: str = "none",
    cross_segment: bool = False,
) -> dict[str, Any]:
    context = github_context if isinstance(github_context, Mapping) else {}
    changed = changed_files if isinstance(changed_files, list) else context.get("changed_files", [])
    cleaned_files = [str(item).strip() for item in changed if str(item).strip()]
    unique_files = list(dict.fromkeys(cleaned_files))
    docs_only = bool(unique_files) and all(is_docs_only_path(path) for path in unique_files)
    pr_number_value = pr_number if pr_number is not None else context.get("pr_number")

    if docs_only:
        change_type = "docs-only"
        behavior_affecting = False
        functionality_impact = "no direct impact"
        runtime_impact = "no direct impact"
        security_impact = "no direct impact"
        validation_needed = "docs accuracy review plus optional docs checks"
        production_effect = "neutral or minor positive documentation polish"
        partner_effect = "neutral or minor positive documentation clarity"
        risk_level = "LOW"
    elif unique_files:
        change_type = "behavior-affecting or mixed"
        behavior_affecting = None
        functionality_impact = "not visible from changed-file evidence"
        runtime_impact = "not visible from changed-file evidence"
        security_impact = "not visible from changed-file evidence"
        validation_needed = "changed-file review plus relevant CI/runtime checks"
        production_effect = "requires changed-file review before calling production-readiness impact neutral"
        partner_effect = "depends on whether changed files alter runtime, workflow, or partner-facing behavior"
        risk_level = "MEDIUM"
    else:
        change_type = "unknown"
        behavior_affecting = None
        functionality_impact = "changed-file evidence unavailable"
        runtime_impact = "changed-file evidence unavailable"
        security_impact = "changed-file evidence unavailable"
        validation_needed = "recover changed-file metadata before relying on PR-scoped claims"
        production_effect = "unknown until changed-file evidence is available"
        partner_effect = "unknown until changed-file evidence is available"
        risk_level = "UNKNOWN"

    limitations = [
        "PR-scoped assessment only; not a merge, security, legal, or production approval.",
        "RepoBrain-Action is the analysis tool; the target product remains the PR repository.",
    ]

    return {
        "pr_number": pr_number_value,
        "title": str(context.get("pr_title", "") or "").strip(),
        "changed_files_total": len(unique_files),
        "changed_files": unique_files,
        "primary_segment": str(primary_segment or "none").strip() or "none",
        "support_segments": str(support_segments or "none").strip() or "none",
        "cross_segment": bool(cross_segment),
        "change_type": change_type,
        "docs_only": docs_only,
        "behavior_affecting": behavior_affecting,
        "product_functionality_impact": functionality_impact,
        "architecture_runtime_impact": runtime_impact,
        "security_posture_impact": security_impact,
        "tests_validation_needed": validation_needed,
        "production_readiness_effect": production_effect,
        "partner_pilot_effect": partner_effect,
        "risk_level": risk_level,
        "limitations": limitations,
    }


def render_pr_impact_summary_lines(facts: Mapping[str, Any]) -> list[str]:
    changed_files_raw = facts.get("changed_files", [])
    changed_files = (
        [str(item).strip() for item in changed_files_raw if str(item).strip()]
        if isinstance(changed_files_raw, list)
        else []
    )
    behavior = facts.get("behavior_affecting")
    if behavior is True:
        behavior_text = "yes"
    elif behavior is False:
        behavior_text = "no"
    else:
        behavior_text = "not visible from changed-file evidence"

    lines = [
        f"- Changed files: {', '.join(f'`{path}`' for path in changed_files[:5]) if changed_files else '`not available from PR metadata`'}",
        f"- Change type: `{str(facts.get('change_type', 'unknown') or 'unknown')}`",
        f"- Behavior-affecting: `{behavior_text}`",
        f"- Architecture/runtime impact: {str(facts.get('architecture_runtime_impact', 'unknown') or 'unknown')}",
        f"- Security impact: {str(facts.get('security_posture_impact', 'unknown') or 'unknown')}",
        f"- Validation needed: {str(facts.get('tests_validation_needed', 'unknown') or 'unknown')}",
        f"- Production readiness effect: {str(facts.get('production_readiness_effect', 'unknown') or 'unknown')}",
        f"- Partner-pilot effect: {str(facts.get('partner_pilot_effect', 'unknown') or 'unknown')}",
        f"- Risk level: `{str(facts.get('risk_level', 'UNKNOWN') or 'UNKNOWN')}`",
        f"- Limitations: {str((facts.get('limitations') or ['PR-scoped only.'])[0])}",
    ]
    return lines
