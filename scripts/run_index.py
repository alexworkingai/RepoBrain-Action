from __future__ import annotations

import os
from pathlib import Path
import shutil

from repobrain.index_store import build_index


def _commit_sha() -> str:
    value = os.getenv("GITHUB_SHA", "").strip()
    if value:
        return value
    return "local"


def main() -> int:
    root = Path.cwd()
    out = root / "artifacts"
    out.mkdir(exist_ok=True)
    index_path = out / "index-package.zip"
    build_index(root=root, out_zip=index_path, store_text=False)
    named_index_path = out / f"repobrain-index-{_commit_sha()}.zip"
    shutil.copyfile(index_path, named_index_path)
    print(f"OK: wrote {index_path.as_posix()}")
    print(f"OK: wrote {named_index_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
