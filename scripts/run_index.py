from __future__ import annotations

from pathlib import Path

from repobrain.index_store import build_index


def main() -> int:
    root = Path.cwd()
    out = root / "artifacts"
    out.mkdir(exist_ok=True)
    index_path = out / "index-package.zip"
    build_index(root=root, out_zip=index_path, store_text=True)
    print(f"OK: wrote {index_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
