from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

DEFAULT_INCLUDE_GLOBS = [
    "src/**",
    "repobrain/**",
    "scripts/**",
    "tests/**",
    "README.md",
    "*.md",
]

DEFAULT_EXCLUDE_GLOBS = [
    ".venv/**",
    "**/.venv/**",
    "venv/**",
    ".git/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*.pem",
    "**/*.pem",
    "*.key",
    "**/*.key",
    "*id_rsa*",
    "**/*id_rsa*",
    "*secrets*",
    "**/*secrets*",
    "*credential*",
    "**/*credential*",
]


def _matches_glob(rel_posix: str, pattern: str) -> bool:
    rel_path = PurePosixPath(rel_posix)
    if rel_path.match(pattern):
        return True
    if pattern.endswith("/**"):
        base_pattern = pattern[:-3]
        return rel_path.match(base_pattern)
    return False


def _load_ignore_patterns(root: Path, ignore_file: str) -> list[str]:
    ignore_path = root / ignore_file
    if not ignore_path.exists():
        return []

    patterns: list[str] = []
    for line in ignore_path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        patterns.append(value)
    return patterns


def scan_files(
    root: Path,
    include_globs: list[str] | None = None,
    exclude_globs: list[str] | None = None,
    ignore_file: str = ".repobrainignore",
) -> list[Path]:
    """Scan text candidate files under root using simple glob-based include/exclude rules."""
    root = root.resolve()
    include_patterns = include_globs or list(DEFAULT_INCLUDE_GLOBS)
    exclude_patterns = (exclude_globs or list(DEFAULT_EXCLUDE_GLOBS)) + _load_ignore_patterns(
        root, ignore_file
    )

    def is_included(rel_posix: str) -> bool:
        return any(_matches_glob(rel_posix, pattern) for pattern in include_patterns)

    def is_excluded(rel_posix: str) -> bool:
        return any(_matches_glob(rel_posix, pattern) for pattern in exclude_patterns)

    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        current_dir = Path(dirpath)

        pruned_dirs: list[str] = []
        for dirname in dirnames:
            child_path = current_dir / dirname
            rel_posix = child_path.relative_to(root).as_posix()
            if is_excluded(rel_posix):
                continue
            pruned_dirs.append(dirname)
        dirnames[:] = pruned_dirs

        for filename in filenames:
            file_path = current_dir / filename
            rel_posix = file_path.relative_to(root).as_posix()
            if is_excluded(rel_posix):
                continue
            if not is_included(rel_posix):
                continue
            results.append(file_path)

    return sorted(results)
