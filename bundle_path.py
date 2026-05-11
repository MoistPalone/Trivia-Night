"""
Resolve paths to bundled data files whether running from source or as a
PyInstaller frozen executable.

PyInstaller extracts data files to sys._MEIPASS at runtime; in source mode
we fall back to the project root (one directory above this file).
"""
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    _ROOT = Path(sys._MEIPASS)  # type: ignore[attr-defined]
else:
    _ROOT = Path(__file__).parent


def bundle_path(*parts: str) -> Path:
    """Return an absolute Path to a bundled asset, e.g. bundle_path('assets', 'sounds')."""
    return _ROOT.joinpath(*parts)
