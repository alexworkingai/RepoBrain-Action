from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_THRESHOLD = 800
STRICT_THRESHOLD = 1500


def iter_modules() -> list[tuple[str, int]]:
    rows: list[tuple[str, int]] = []
    for path in sorted(ROOT.rglob('*.py')):
        if '.venv' in path.parts or '__pycache__' in path.parts:
            continue
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except UnicodeDecodeError:
            continue
        rows.append((str(path.relative_to(ROOT)).replace('\\', '/'), len(lines)))
    rows.sort(key=lambda item: item[1], reverse=True)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description='Report oversized Python module hotspots.')
    parser.add_argument('--threshold', type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--limit', type=int, default=15)
    args = parser.parse_args()

    rows = iter_modules()
    status = 'PASS'
    warn_count = 0
    for _, lines in rows:
        if lines >= args.threshold:
            warn_count += 1
    if warn_count:
        status = 'WARN'
    if args.strict and any(lines >= STRICT_THRESHOLD for _, lines in rows):
        status = 'FAIL'

    print(f'MODULE_HOTSPOT_STATUS={status}')
    print(f'MODULE_HOTSPOT_THRESHOLD={args.threshold}')
    print(f'MODULE_HOTSPOT_WARN_COUNT={warn_count}')
    for path, lines in rows[: max(1, args.limit)]:
        level = 'normal'
        if lines >= STRICT_THRESHOLD:
            level = 'critical'
        elif lines >= args.threshold:
            level = 'warning'
        print(f'{path}|{lines}|{level}')

    return 1 if status == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
