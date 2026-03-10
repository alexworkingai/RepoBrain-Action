from __future__ import annotations

import argparse
from pathlib import Path
import re


def _extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    in_section = False
    collected: list[str] = []
    for line in lines:
        if line.strip().startswith("## "):
            if in_section:
                break
            if line.strip() == heading:
                in_section = True
                continue
        if in_section:
            collected.append(line)
    return "\n".join(collected).strip()


def extract_merge_branches(text: str) -> list[str]:
    section = _extract_section(text, "## Recommended merge order")
    pattern = re.compile(r"^\s*\d+\.\s+`([^`]+)`\s*$")
    branches: list[str] = []
    for line in section.splitlines():
        match = pattern.match(line)
        if match:
            branches.append(match.group(1))
    return branches


def extract_conflict_hotspots(text: str) -> list[str]:
    section = _extract_section(text, "## Expected conflict hotspots")
    pattern = re.compile(r"^\s*-\s+`([^`]+)`\s*$")
    hotspots: list[str] = []
    for line in section.splitlines():
        match = pattern.match(line)
        if match:
            hotspots.append(match.group(1))
    return hotspots


def render_plan_output(branches: list[str], hotspots: list[str]) -> str:
    lines: list[str] = []
    lines.append("Recommended merge order:")
    for index, branch in enumerate(branches, start=1):
        lines.append(f"{index}. {branch}")
    lines.append("")
    lines.append("Conflict hotspots:")
    for path in hotspots:
        lines.append(f"- {path}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print release merge order and conflict hotspots.")
    parser.add_argument(
        "--plan-path",
        default="docs/release_merge_plan.md",
        help="Path to release merge plan markdown file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan_path = Path(args.plan_path)
    if not plan_path.exists():
        print(f"Missing release merge plan: {plan_path.as_posix()}")
        return 1
    text = plan_path.read_text(encoding="utf-8")
    branches = extract_merge_branches(text)
    hotspots = extract_conflict_hotspots(text)
    print(render_plan_output(branches, hotspots))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
