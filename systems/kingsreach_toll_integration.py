"""Runtime integration for the playable Kingsreach Toll checkpoint."""
from __future__ import annotations


_INSTALLED = False


def _patch_world_map_data() -> None:
    import lore.world_map_data as world_map

    location = world_map.LOCATIONS["kingsreach_toll"]
    location["content_state"] = "playable"
    location["target_state"] = "regional_staging"
    location["services"] = (
        "Crown travel papers",
        "toll payment",
        "quarantine service",
        "checkpoint market",
        "smuggler route",
    )
    location["threats"] = (
        "Fevered Escapees",
        "Causeway Bandits",
        "Crown Toll Enforcers",
        "Tollmaster Hadrik Crowl",
        "water-fever haze",
    )
    location["materials"] = (
        "Parchment Sheet",
        "Wax Seal",
        "Feverfew",
        "Clean Bandage",
        "Charcoal",
    )
    location["boss"] = "Tollmaster Hadrik Crowl"
    location["story_state"] = "playable checkpoint-resolution chain"
    location["formal_routes"] = (
        "official evidence",
        "full toll payment",
        "quarantine service",
        "smuggler culvert",
    )


def _patch_loot_tables() -> None:
    from loot_data import LOOT_DROPS
    from units.kingsreach_toll_monsters import KINGSREACH_LOOT

    LOOT_DROPS.update(KINGSREACH_LOOT)


def _patch_game_manager() -> None:
    from citys.mucford.kingsreach_toll import kingsreach_state
    from game_manager import GameManager

    if getattr(GameManager, "_kingsreach_toll_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.kingsreach_entry = None
        kingsreach_state(self)

    GameManager.__init__ = __init__
    GameManager._kingsreach_toll_installed = True


def _patch_regional_staging_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_kingsreach_toll_factory_installed", False):
        return
    previous_new = RegionalStagingMenu.__new__

    def __new__(cls, manager, *args, **kwargs):
        pending = getattr(manager, "pending_local_area", None)
        world_pending = getattr(manager, "pending_world_location", None)
        current = (
            getattr(manager, "npc_state", {})
            .get("world_progression", {})
            .get("current_location")
        )
        if "kingsreach_toll" in (pending, world_pending, current):
            manager.pending_local_area = None
            manager.pending_world_location = "kingsreach_toll"
            from citys.mucford.kingsreach_toll import KingsreachTollMenu

            return KingsreachTollMenu(manager)
        return previous_new(cls, manager, *args, **kwargs)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._kingsreach_toll_factory_installed = True


def _patch_kingsreach_save_migration() -> None:
    from citys.mucford.kingsreach_toll import KingsreachTollMenu, kingsreach_state, sync_kingsreach_story

    if getattr(KingsreachTollMenu, "_kingsreach_save_migration_installed", False):
        return
    previous_enter = KingsreachTollMenu.on_enter
    previous_update = KingsreachTollMenu.update

    def _sync_flags(menu):
        state = kingsreach_state(menu.manager)
        if state.get("completed") or state.get("pass_issued"):
            try:
                menu.manager.record_tier0_event("quest", "kingsreach_toll_cleared")
                menu.manager.record_tier0_event("flag", "kingsreach_cleared")
                menu.manager.record_tier0_event("flag", "bram_recommendation_requested")
            except Exception:
                pass
        engine = getattr(menu.manager, "league_engine", None)
        if state.get("completed") and int(getattr(engine, "tier", 1)) >= 2:
            flags = (
                menu.manager.npc_state.setdefault("tier0_world", {})
                .setdefault("story_flags", {})
            )
            if not flags.get("tier1_promoted"):
                try:
                    menu.manager.record_tier0_event("flag", "tier1_promoted")
                except Exception:
                    flags["tier1_promoted"] = True
                menu.manager.inventory["Bram's Recommendation"] = max(
                    1,
                    int(menu.manager.inventory.get("Bram's Recommendation", 0)),
                )
                menu.manager.inventory.pop("Crown Promotion Docket", None)
                try:
                    menu.manager.record_deed(
                        "tier0_promotion",
                        "earned Bram Carrow's recommendation and promotion to the Scrapring Circuit",
                    )
                except Exception:
                    pass
            sync_kingsreach_story(menu.manager)

    def on_enter(self):
        result = previous_enter(self)
        _sync_flags(self)
        return result

    def update(self):
        result = previous_update(self)
        _sync_flags(self)
        return result

    KingsreachTollMenu.on_enter = on_enter
    KingsreachTollMenu.update = update
    KingsreachTollMenu._kingsreach_save_migration_installed = True


def install_kingsreach_toll_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    _patch_loot_tables()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_regional_staging_factory()
    _patch_kingsreach_save_migration()
    _INSTALLED = True


_patch_world_map_data()
_patch_loot_tables()
