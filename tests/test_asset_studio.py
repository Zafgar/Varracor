# tests/test_asset_studio.py
"""
Asset Studio: katalogi kattaa koodin viittaamat asset-paikat, inbox-tiedosto
asentuu oikeaan polkuun oikealla nimellä (väärä tyyppi estetään), hitbox-
override tallentuu ja vaikuttaa Prop-instansseihin heti, ja studio aukeaa
F10:llä mistä tahansa valikosta.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems import asset_studio


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def test_catalog_covers_referenced_assets():
    cat = asset_studio.build_catalog()
    assert len(cat) > 100, "skannerin pitää löytää koodin asset-viittaukset"
    kinds = {c["kind"] for c in cat}
    assert {"image", "sound", "music"} <= kinds
    paths = {c["path"] for c in cat}
    assert "assets/gear/axes/scrap_axe.png" in paths
    assert any(p.endswith(".wav") for p in paths)


def test_assign_copies_renames_and_blocks_type_mismatch():
    asset_studio.ensure_inbox()
    src = os.path.join(asset_studio.INBOX_DIR, "_test_art.png")
    target_rel = "assets/gear/axes/weak_axe.png"
    target = os.path.join(asset_studio.ROOT, target_rel)
    surf = pygame.Surface((8, 8))
    pygame.image.save(surf, src)
    try:
        assert not os.path.exists(target), "testi olettaa puuttuvan slotin"
        ok, msg = asset_studio.assign_asset("_test_art.png", target_rel)
        assert ok, msg
        assert os.path.exists(target), "tiedosto kopioitui ja nimettiin oikein"

        ok2, msg2 = asset_studio.assign_asset("_test_art.png",
                                              "assets/gear/axes/axe_1.wav")
        assert not ok2 and "mismatch" in msg2.lower()

        missing, msg3 = asset_studio.assign_asset("_does_not_exist.png", target_rel)
        assert not missing
    finally:
        for p in (src, target):
            if os.path.exists(p):
                os.remove(p)
        asset_studio.refresh_missing_report()


def test_hitbox_override_applies_and_clears():
    from assets.tiles.muckford_objects import ScrapBarrel
    base = ScrapBarrel(100, 100).rect
    try:
        asset_studio.save_hitbox_override("ScrapBarrel", 5, 20, 40, 30)
        boxed = ScrapBarrel(100, 100).rect
        assert (boxed.x, boxed.y, boxed.w, boxed.h) == (105, 120, 40, 30)
    finally:
        asset_studio.clear_hitbox_override("ScrapBarrel")
    reset = ScrapBarrel(100, 100).rect
    assert (reset.x, reset.y, reset.w, reset.h) == \
        (base.x, base.y, base.w, base.h), "RESET palauttaa koodin oletuksen"


def test_editable_prop_classes_constructible():
    props = asset_studio.editable_prop_classes()
    assert len(props) >= 20
    names = [n for n, _ in props]
    assert "ScrapBarrel" in names and "AppleTree" in names
    for _name, cls in props[:5]:
        inst = cls(0, 0)
        assert hasattr(inst, "rect") and hasattr(inst, "image")


def test_studio_menu_draws_both_tabs_and_returns():
    m = _manager()
    m.asset_studio_return_state = "muckford_city"
    from menus.asset_studio_menu import AssetStudioMenu
    menu = AssetStudioMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.selected = menu.catalog[0]
    menu.update()
    menu.draw(surf)
    menu.tab = "HITBOX"
    menu._select_prop(*menu.prop_classes[0])
    menu.update()
    menu.draw(surf)
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.next_state == "muckford_city", "ESC palaa lähtötilaan"


def test_f10_opens_studio_from_any_menu_in_cheat_mode():
    m = _manager()
    import menus.base_menu as bm
    old = bm.CHEAT_MODE
    bm.CHEAT_MODE = True
    try:
        from menus.town_hub import TownHub
        hub = TownHub(m)
        handled = hub.handle_editor_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F10))
        assert handled is True
        assert hub.next_state == "asset_studio"
    finally:
        bm.CHEAT_MODE = old


def test_asset_studio_state_registered():
    import inspect
    import main
    src = inspect.getsource(main.main)
    assert '"asset_studio": AssetStudioMenu' in src
    assert 'manager.asset_studio_return_state = old_key' in src
