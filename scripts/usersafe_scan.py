from __future__ import annotations

import argparse
from pathlib import Path
import re

STRONG_SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"BEGIN (?:RSA )?PRIVATE KEY"),
)

FORBIDDEN_SECRET_VAR_REFERENCES = (
    re.compile(r"GITHUB_TOKEN"),
    re.compile(r"API_KEY"),
    re.compile(r"HMAC_SECRET"),
    re.compile(r"PASSWORD"),
)


def _default_scan_paths() -> list[Path]:
    paths = [
        Path("repobrain/output_md.py"),
        Path("repobrain/formatting.py"),
    ]
    config_snapshot = Path("artifacts/config_snapshot.json")
    if config_snapshot.exists():
        paths.append(config_snapshot)
    return paths


def scan_paths(paths: list[Path] | None = None) -> list[str]:
    issues: list[str] = []
    scan_list = paths if paths is not None else _default_scan_paths()
    for path in scan_list:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in STRONG_SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(f"{path.as_posix()}: matched forbidden pattern {pattern.pattern}")
        if path.name.endswith(".py") and (
            "output_md.py" in path.as_posix() or "formatting.py" in path.as_posix()
        ):
            for pattern in FORBIDDEN_SECRET_VAR_REFERENCES:
                if pattern.search(text):
                    issues.append(
                        f"{path.as_posix()}: contains forbidden secret variable reference {pattern.pattern}"
                    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", help="Optional files/directories to scan.")
    args = parser.parse_args()
    scan_list: list[Path] | None = None
    if args.paths:
        scan_list = []
        for raw in args.paths:
            path = Path(raw)
            if path.is_dir():
                for item in path.rglob("*"):
                    if item.is_file():
                        scan_list.append(item)
            else:
                scan_list.append(path)
    issues = scan_paths(scan_list)
    if issues:
        for item in issues:
            print(item)
        print("Usersafe scan failed: strong secret-like values or env leakage found.")
        return 1
    print("Usersafe scan passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
