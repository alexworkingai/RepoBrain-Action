from __future__ import annotations

from pathlib import Path

from repobrain.config import env_reference_rows


def _format_allowed(row: dict[str, object]) -> str:
    allowed = row.get("allowed", [])
    if isinstance(allowed, list) and allowed:
        return ", ".join(str(item) for item in allowed)
    min_value = row.get("min")
    max_value = row.get("max")
    if min_value is None and max_value is None:
        return "-"
    if min_value is None:
        return f"<= {max_value}"
    if max_value is None:
        return f">= {min_value}"
    return f"{min_value}..{max_value}"


def render_markdown() -> str:
    lines: list[str] = []
    lines.append("# RepoBrain Environment Reference")
    lines.append("")
    lines.append("This file is generated from `repobrain/config.py` by `scripts/gen_env_reference.py`.")
    lines.append("")
    lines.append("| ENV | Type | Default | Allowed / Range | Description |")
    lines.append("| --- | --- | --- | --- | --- |")
    for row in env_reference_rows():
        lines.append(
            "| "
            f"`{row['name']}` | {row['type']} | `{row['default']}` | "
            f"{_format_allowed(row)} | {row['description']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    output = Path("docs") / "env_reference.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(), encoding="utf-8")
    print(f"Wrote {output.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
