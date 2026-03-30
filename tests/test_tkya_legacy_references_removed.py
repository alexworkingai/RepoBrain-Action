from __future__ import annotations

from pathlib import Path
import re


def test_user_facing_docs_do_not_expose_legacy_backend_controls() -> None:
    user_docs = [
        Path("README.md"),
        Path("docs/tkya_contract.md"),
        Path("docs/artifacts.md"),
        Path("docs/e2e_testing.md"),
        Path("docs/env_reference.md"),
    ]

    combined = "\n".join(path.read_text(encoding="utf-8") for path in user_docs)
    lowered = combined.lower()

    assert "rb_tkya_strict_original" not in lowered
    assert "rb_tkya_original_path" not in lowered
    assert not re.search(r"rb_tkya_backend[^\n]*\boriginal\b", lowered)
