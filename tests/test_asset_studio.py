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


def test_studio_menu_draws_all_tabs_and_returns():
    m = _manager()
    m.asset_studio_return_state = "muckford_city"
    from menus.asset_studio_menu import AssetStudioMenu
    menu = AssetStudioMenu(m)
    surf = pygame.Surface((1920, 1080))
    menu.selected = menu.catalog[0]
    menu.update()
    menu.draw(surf)
    menu.tab = "UNITS"
    menu._spawn_pen_unit(*menu.unit_factories[0])
    menu.update()
    menu.draw(surf)
    menu.tab = "PROPS"
    menu._select_prop(*menu.prop_classes[0])
    menu.update()
    menu.draw(surf)
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert menu.next_state == "muckford_city", "ESC palaa lähtötilaan"


def test_units_pen_covers_races_and_equips_gear():
    """Penkki listaa keskeiset rodut ja varusteet piirtyvät hahmolle."""
    from systems.asset_studio import preview_unit_factories, equipable_items
    names = [n for n, _ in preview_unit_factories()]
    for expected in ("Human", "Orc", "Elf", "Goblin", "Dwarf", "Gnome",
                     "Villager", "Cow", "Chicken", "GiantRat", "Werewolf"):
        assert expected in names, f"{expected} puuttuu penkistä"
    slots = equipable_items()
    assert len(slots["main_hand"]) >= 20
    assert len(slots["off_hand"]) >= 4
    assert slots["head"] and slots["body"]

    m = _manager()
    from menus.asset_studio_menu import AssetStudioMenu
    menu = AssetStudioMenu(m)
    menu.tab = "UNITS"
    idx = [i for i, (n, _) in enumerate(menu.unit_factories) if n == "Orc"][0]
    menu._spawn_pen_unit(*menu.unit_factories[idx])
    menu.equip_index["main_hand"] = slots["main_hand"].index("Scrap Blade") - 1
    menu._cycle_equip("main_hand", 1)
    unit = menu.pen_unit
    assert unit.equipment["main_hand"].name == "Scrap Blade"
    surf = pygame.Surface((1920, 1080))
    menu.update()
    menu.draw(surf)
    assert unit.equipment["main_hand"].image is not None, \
        "proseduraalinen asegrafiikka syntyy piirrossa"


def test_procedural_gear_images_for_all_equipables():
    """Jokaiselle varusteelle syntyy koodigrafiikka jos PNG puuttuu -
    muuten ase olisi näkymätön hahmon kädessä."""
    from systems.asset_studio import equipable_items
    from items.item_registry import create_item
    from items.procedural_gear import ensure_gear_image
    slots = equipable_items()
    for slot, names in slots.items():
        for name in names:
            item = create_item(name)
            assert item is not None
            ensure_gear_image(item)
            assert item.image is not None, f"{name} ({slot}) jäi näkymättömäksi"


def test_procedural_gear_respects_existing_sprite():
    from items.item_registry import create_item
    from items.procedural_gear import ensure_gear_image
    item = create_item("Scrap Blade")
    marker = pygame.Surface((4, 4))
    item.image = marker
    ensure_gear_image(item)
    assert item.image is marker, "oikea sprite ei saa korvautua"


def test_props_pen_behaviours_chop_and_shake():
    import main  # noqa: F401
    from menus.asset_studio_menu import _StudioWorld, _StudioChopper
    from assets.tiles.muckford_objects import MuckfordTree, AppleTree

    world = _StudioWorld()
    chopper = _StudioChopper()
    tree = MuckfordTree(0, 0)
    for _ in range(tree.current_hits):
        tree.chop(chopper, chopper.current_weapon, world)
    assert tree.is_empty, "puu kaatuu studiossa"
    assert world.inventory.get(tree.resource_name, 0) >= 2

    world2 = _StudioWorld()
    apple_tree = AppleTree(0, 0)
    apple_tree.shake(world2)
    assert len(world2.current_arena.props) == 1, "omena tippui mini-maailmaan"


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
