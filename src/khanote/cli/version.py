"""Version check against PyPI (24h cache)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from khanote import __version__

_CACHE_TTL = 86400  # 24 hours


def check_version(khanote_dir: Path | None = None) -> None:
    """Check PyPI for a newer khanote version.

    Prints a notice if a newer version is available.
    Caches the result for 24 hours in .khanote/.version_check.
    Silently no-ops on any error.
    """
    try:
        import httpx  # noqa: F401
    except ImportError:
        return

    try:
        cache_file = _find_cache_file(khanote_dir)
        cached = _read_cache(cache_file)

        if cached and (time.time() - cached.get("checked_at", 0)) < _CACHE_TTL:
            latest = cached.get("latest")
        else:
            latest = _fetch_latest_from_pypi()
            _write_cache(cache_file, latest)

        if latest and latest != __version__ and _is_newer(latest, __version__):
            from rich.console import Console
            Console().print(
                f"[yellow]Update available:[/yellow] khanote {__version__} → {latest}. "
                f"Run [bold]pip install --upgrade khanote[/bold]"
            )
    except Exception:
        pass  # Version check is advisory; never block the user


def _fetch_latest_from_pypi() -> str | None:
    import httpx
    try:
        resp = httpx.get("https://pypi.org/pypi/khanote/json", timeout=3.0)
        resp.raise_for_status()
        return resp.json()["info"]["version"]
    except Exception:
        return None


def _find_cache_file(khanote_dir: Path | None) -> Path | None:
    if khanote_dir:
        return khanote_dir / ".version_check"
    # Try to find vault's .khanote from cwd
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".khanote" / ".version_check"
        if candidate.parent.exists():
            return candidate
    return None


def _read_cache(cache_file: Path | None) -> dict | None:
    if cache_file is None or not cache_file.exists():
        return None
    try:
        return json.loads(cache_file.read_text())
    except Exception:
        return None


def _write_cache(cache_file: Path | None, latest: str | None) -> None:
    if cache_file is None:
        return
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"latest": latest, "checked_at": time.time()}))
    except Exception:
        pass


def _is_newer(latest: str, current: str) -> bool:
    """Compare semantic versions; return True if latest > current."""
    try:
        def parse(v: str) -> tuple[int, ...]:
            return tuple(int(x) for x in v.split(".")[:3])
        return parse(latest) > parse(current)
    except Exception:
        return False
