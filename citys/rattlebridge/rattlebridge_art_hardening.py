"""Asset-selection hardening for Rattlebridge placeholder graphics."""

from __future__ import annotations

from pathlib import Path


_INSTALLED = False


def install_rattlebridge_art_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    from citys.rattlebridge import rattlebridge_art as art

    def _candidate_paths(key):
        filename = art.CANONICAL_ASSETS[key]
        stem = Path(filename).stem

        # User-supplied final artwork must always win, even when the game has
        # already generated a canonical placeholder PNG on an earlier launch.
        yield art.ASSET_DIR / f"{stem}_final.png"
        yield art.ASSET_DIR / f"{stem}_final.jpg"
        yield art.ASSET_DIR / f"{stem}_final.jpeg"

        # A non-PNG canonical file may also be supplied by the user.
        for alternate in art.ALTERNATE_ASSETS.get(key, ()):
            yield art.ASSET_DIR / alternate

        # The generated canonical PNG is deliberately the last candidate.
        yield art.ASSET_DIR / filename

    art._candidate_paths = _candidate_paths
    art.clear_rattlebridge_asset_cache()
    _INSTALLED = True
