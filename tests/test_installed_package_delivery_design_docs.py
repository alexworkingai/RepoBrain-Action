from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_delivery_design_doc_exists() -> None:
    assert (ROOT / "docs/release/INSTALLED_PACKAGE_DELIVERY_DESIGN.md").exists()


def test_installed_package_delivery_design_doc_covers_required_sections() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_DELIVERY_DESIGN.md").lower()

    assert "selected delivery path" in text
    assert "token model" in text
    assert "artifact/package integrity" in text or "artifact integrity" in text
    assert "source checkout avoided" in text
    assert "wheel readability caveat" in text or "readable" in text
    assert "rejected alternatives" in text
