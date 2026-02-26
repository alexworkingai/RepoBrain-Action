from __future__ import annotations


def make_line_link(
    repo: str | None,
    sha: str | None,
    file_path: str,
    line_start: int,
    line_end: int,
) -> str:
    """Build a markdown line link (absolute for GitHub, else relative anchor)."""
    label = f"{file_path}:L{line_start}-L{line_end}"
    if repo and sha:
        url = f"https://github.com/{repo}/blob/{sha}/{file_path}#L{line_start}-L{line_end}"
    else:
        url = f"{file_path}#L{line_start}-L{line_end}"
    return f"[`{label}`]({url})"
