"""RepoBrain package metadata."""

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_VERSION_FILE = _ROOT / "VERSION"

try:
    __version__ = _VERSION_FILE.read_text(encoding="utf-8").strip()
except OSError:
    __version__ = "0.5.0-rc.1"

__all__ = ["__version__"]
