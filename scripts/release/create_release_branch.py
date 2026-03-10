from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


def read_version(version_path: Path) -> str:
    version = version_path.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError(f"Version file is empty: {version_path.as_posix()}")
    return version


def build_release_branch_name(version: str) -> str:
    return f"release/{version}"


def build_commands(version: str, base_branch: str = "main") -> list[list[str]]:
    branch_name = build_release_branch_name(version)
    return [
        ["git", "checkout", base_branch],
        ["git", "pull"],
        ["git", "checkout", "-b", branch_name],
    ]


def _format_commands(commands: list[list[str]]) -> str:
    return "\n".join(" ".join(command) for command in commands)


def _run_commands(commands: list[list[str]]) -> None:
    for command in commands:
        print(f"Running: {' '.join(command)}")
        subprocess.run(command, check=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print or execute release branch creation commands.")
    parser.add_argument(
        "--version-file",
        default="VERSION",
        help="Path to VERSION file (default: VERSION).",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch used for release branch creation (default: main).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute git commands. Default mode is dry-run (print only).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    version = read_version(Path(args.version_file))
    commands = build_commands(version=version, base_branch=args.base_branch)
    print("Release branch creation plan:")
    print(_format_commands(commands))
    if args.execute:
        _run_commands(commands)
        print("Release branch commands executed.")
    else:
        print("Dry-run mode: no git commands executed. Use --execute to run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
