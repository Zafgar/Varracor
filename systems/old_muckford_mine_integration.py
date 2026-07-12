"""Runtime integration for the expanded Old Muckford Mine."""
from __future__ import annotations


_INSTALLED = False


def _patch_world_map_data() -> None:
    from lore.world_map_data import LOCATIONS

    location = LOCATIONS.get("old_mine_road")
    if not location:
        return
    location["summary"] = (
        "Marda's key opens an undead-haunted mine road and a multi-chamber "
        "industrial ruin beneath Muckford."
    )
    location["lore"] = (
        "The old mine can be restored by relighting its lantern network, rescuing "
        "Torra Flintvein's crew, clearing collapsed rails and destroying the "
        "Cave Broodmother's Webbed Depths."
    )
    location["content_state"] = "playable"
    location["target_state"] = "mine_road"
    location["services"] = (
        "mining",
        "mine restoration",
        "daily ore production",
        "deep chamber hunting",
    )
    location["threats"] = (
        "Grave Pickmen",
        "Rail Wraiths",
        "Web Crawlers",
        "Crystal Husks",
        "Cave Broodmother",
    )
    location["materials"] = (
        "Iron Ore",
        "Coal",
        "Stone",
        "Chipped Ruby",
        "Silver Ore",
        "Spider Silk",
    )
    location["boss"] = "Cave Broodmother"
    location["story_state"] = "playable restoration chain"


def _patch_loot_tables() -> None:
    from loot_data import LOOT_DROPS
    from units.old_muckford_mine_monsters import OLD_MINE_LOOT

    LOOT_DROPS.update(OLD_MINE_LOOT)


def apply_daily_mine_production(manager) -> bool:
    """Deliver a modest daily share after the player restores production."""
    from citys.mucford.old_muckford_mine import _day_key, old_mine_state

    state = old_mine_state(manager)
    if not state.get("production_restarted"):
        return False
    day_key = _day_key(manager)
    if state.get("last_production_day") == day_key:
        return False
    state["last_production_day"] = day_key
    storage = getattr(manager, "city_storage", None)
    if not isinstance(storage, dict):
        manager.city_storage = {}
        storage = manager.city_storage
    storage["Iron Ore"] = int(storage.get("Iron Ore", 0)) + 2
    storage["Coal"] = int(storage.get("Coal", 0)) + 1
    return True


def _patch_game_manager() -> None:
    from game_manager import GameManager
    from citys.mucford.old_muckford_mine import old_mine_state

    if getattr(GameManager, "_old_muckford_mine_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        old_mine_state(self)
        apply_daily_mine_production(self)

    GameManager.__init__ = __init__
    GameManager._old_muckford_mine_installed = True


def _patch_mine_cave_factory() -> None:
    from citys.mucford.mine_cave_menu import MineCaveMenu

    if getattr(MineCaveMenu, "_expanded_old_mine_factory_installed", False):
        return

    def __new__(cls, manager, *args, **kwargs):
        from citys.mucford.old_muckford_mine import OldMuckfordMineMenu

        return OldMuckfordMineMenu(manager)

    MineCaveMenu.__new__ = staticmethod(__new__)
    MineCaveMenu._expanded_old_mine_factory_installed = True


def _patch_mine_road_persistence() -> None:
    from citys.mucford.mine_road_menu import MineRoadMenu
    from citys.mucford.old_muckford_mine import old_mine_state

    if getattr(MineRoadMenu, "_persistent_mine_road_installed", False):
        return
    previous_spawn = MineRoadMenu._spawn_undead
    previous_enter = MineRoadMenu.on_enter
    previous_draw = MineRoadMenu.draw

    def _spawn_undead(self):
        state = old_mine_state(self.manager)
        if state.get("road_secured"):
            for unit in list(getattr(self, "undead", ())):
                if unit in self.manager.all_units:
                    self.manager.all_units.remove(unit)
            self.undead = []
            return
        return previous_spawn(self)

    def on_enter(self):
        result = previous_enter(self)
        apply_daily_mine_production(self.manager)
        return result

    def draw(self, screen):
        result = previous_draw(self, screen)
        state = old_mine_state(self.manager)
        if state.get("road_secured"):
            try:
                from settings import SCREEN_WIDTH
                from ui_kit import draw_text, font_small

                text = "Torra's crew keeps the mine road permanently clear."
                surface = font_small.render(text, True, (180, 220, 180))
                screen.blit(surface, (SCREEN_WIDTH // 2 - surface.get_width() // 2, 155))
            except Exception:
                pass
        return result

    MineRoadMenu._spawn_undead = _spawn_undead
    MineRoadMenu.on_enter = on_enter
    MineRoadMenu.draw = draw
    MineRoadMenu._persistent_mine_road_installed = True


def install_old_muckford_mine_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    _patch_loot_tables()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_mine_cave_factory()
    _patch_mine_road_persistence()
    _INSTALLED = True


_patch_world_map_data()
_patch_loot_tables()
