from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_generator_module():
    script_path = Path(__file__).resolve().parent / "gen_env_reference.py"
    spec = importlib.util.spec_from_file_location("repobrain_gen_env_reference", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load scripts/gen_env_reference.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_current() -> tuple[bool, str]:
    module = _load_generator_module()
    expected = str(module.render_markdown())
    target = Path("docs") / "env_reference.md"
    if not target.exists():
        return False, "docs/env_reference.md is missing. Run scripts/gen_env_reference.py"
    current = target.read_text(encoding="utf-8")
    if current != expected:
        return False, "docs/env_reference.md is outdated. Run scripts/gen_env_reference.py"
    return True, "docs/env_reference.md is up to date."


def main() -> int:
    ok, message = check_current()
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
