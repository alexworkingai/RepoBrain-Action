from __future__ import annotations

import argparse
from pathlib import Path
import re


def _extract_version_section(changelog: str, version: str) -> list[str]:
    pattern = re.compile(rf"^##\s+\[{re.escape(version)}\].*$")
    lines = changelog.splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        if pattern.match(line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            collected.append(line)
    return [item.strip() for item in collected if item.strip()]


def _extract_named_section_bullets(markdown: str, section_heading: str) -> list[str]:
    lines = markdown.splitlines()
    in_section = False
    items: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if line.startswith("## "):
            if in_section:
                break
            if line == section_heading:
                in_section = True
                continue
        if in_section and line.startswith("- "):
            items.append(line[2:].strip())
    return items


def _select_ai_highlights(changelog_lines: list[str]) -> list[str]:
    keywords = ("LLM", "embedd", "budget governor", "GitHub Models")
    selected: list[str] = []
    for line in changelog_lines:
        if not line.startswith("- "):
            continue
        payload = line[2:].strip()
        lowered = payload.lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            selected.append(payload)
    return selected


def render_release_notes(version: str, changelog_text: str, migration_text: str) -> str:
    highlights = [line[2:].strip() for line in _extract_version_section(changelog_text, version) if line.startswith("- ")]
    workflow_permissions = _extract_named_section_bullets(migration_text, "## 1. Workflow permissions")
    artifacts = _extract_named_section_bullets(migration_text, "## 2. New artifacts")
    commands = _extract_named_section_bullets(migration_text, "## 3. Commands")
    safe_defaults = _extract_named_section_bullets(migration_text, "## 5. Safe defaults")
    ai_highlights = _select_ai_highlights(_extract_version_section(changelog_text, version))

    lines: list[str] = []
    lines.append(f"# RepoBrain Release Notes - {version}")
    lines.append("")
    lines.append("Generated from `VERSION`, `CHANGELOG.md`, and `MIGRATION.md`.")
    lines.append("")

    lines.append("## Highlights")
    if highlights:
        lines.extend(f"- {item}" for item in highlights)
    else:
        lines.append("- No highlights found for this version in CHANGELOG.md.")
    lines.append("")

    lines.append("## Breaking/Behavioral Changes")
    if workflow_permissions:
        lines.append("- Workflow permissions to verify for this release:")
        lines.extend(f"  - `{item}`" for item in workflow_permissions)
    else:
        lines.append("- No explicit permission changes listed.")
    lines.append("- Safe defaults remain conservative unless RB_* flags are explicitly enabled.")
    lines.append("")

    lines.append("## New Artifacts")
    if artifacts:
        lines.extend(f"- `{item}`" for item in artifacts)
    else:
        lines.append("- No additional artifacts listed.")
    lines.append("")

    lines.append("## New Commands")
    if commands:
        lines.extend(f"- `{item}`" for item in commands)
    else:
        lines.append("- No command additions listed.")
    lines.append("")

    lines.append("## LLM / Embeddings / Governor")
    if ai_highlights:
        lines.extend(f"- {item}" for item in ai_highlights)
    else:
        lines.append("- No AI-specific highlights listed in changelog for this version.")
    lines.append("")

    lines.append("## Migration Notes")
    lines.append("- Review `MIGRATION.md` before rollout.")
    lines.append("- Validate environment flags via `docs/env_reference.md`.")
    if safe_defaults:
        lines.append("- Safe defaults from migration guide:")
        lines.extend(f"  - `{item}`" for item in safe_defaults)
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate deterministic release notes artifact.")
    parser.add_argument("--version-file", default="VERSION", help="Path to VERSION file.")
    parser.add_argument("--changelog-file", default="CHANGELOG.md", help="Path to CHANGELOG.md.")
    parser.add_argument("--migration-file", default="MIGRATION.md", help="Path to MIGRATION.md.")
    parser.add_argument(
        "--output",
        default="artifacts/release_notes.md",
        help="Output path for generated release notes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    version = Path(args.version_file).read_text(encoding="utf-8").strip()
    changelog_text = Path(args.changelog_file).read_text(encoding="utf-8")
    migration_text = Path(args.migration_file).read_text(encoding="utf-8")
    markdown = render_release_notes(version=version, changelog_text=changelog_text, migration_text=migration_text)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
