from pathlib import Path
import sys


def _base_dir() -> Path:
    """Resolve base directory for resources (handles PyInstaller _MEIPASS)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    # src/utils -> project root
    return Path(__file__).resolve().parent.parent


def resource_path(*relative_parts: str, prefer_external: bool = True) -> Path:
    """Return path for resource; prefer external overrides when present."""
    rel_path = Path(*relative_parts)
    if prefer_external:
        external = Path.cwd() / rel_path
        if external.exists():
            return external
    return _base_dir() / rel_path
