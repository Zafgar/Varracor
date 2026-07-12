"""Runtime integration for the playable Drowned Chapel Tier 0 area."""
from __future__ import annotations


_INSTALLED = False


def _patch_world_map_data() -> None:
    import lore.world_map_data as world_map

    if "drowned_chapel" not in world_map.LOCATIONS:
        world_map.LOCATIONS["drowned_chapel"] = world_map._location(
            "Drowned Chapel",
            "sundered_heartlands",
            (475, 425),
            (3, 5),
            "ruins",
            "A flooded Saint Lumen chapel and sunken graveyard east of Whisper Marsh.",
            "Water-risen pilgrims, quarantine fires and a drowned bell mark the first holy field operation outside Muckford.",
            target_state="regional_staging",
            content_state="playable",
            services=("holy field work", "rescue", "foraging", "quarantine rest"),
            threats=("Water-risen Pilgrims", "Flooded Acolytes", "Bell Wraiths", "Bell-Drowned Pilgrim"),
            materials=("Medicinal Herb", "Grave-Lotus", "Sanctified Wax", "River Clay"),
        )
    else:
        location = world_map.LOCATIONS["drowned_chapel"]
        location["content_state"] = "playable"
        location["target_state"] = "regional_staging"
        location["services"] = ("holy field work", "rescue", "foraging", "quarantine rest")
        location["threats"] = ("Water-risen Pilgrims", "Flooded Acolytes", "Bell Wraiths", "Bell-Drowned Pilgrim")
        location["materials"] = ("Medicinal Herb", "Grave-Lotus", "Sanctified Wax", "River Clay")
        location["boss"] = "The Bell-Drowned Pilgrim"
        location["story_state"] = "playable quest chain"

    if world_map.get_route("whisper_marsh", "drowned_chapel") is None:
        world_map.ROUTES.append(
            world_map._route("whisper_marsh", "drowned_chapel", 3, 4, "Drowned pilgrim path")
        )

    # The area is visible and physically reachable from the beginning. Its level
    # range is a warning, never an invisible level gate.
    if "drowned_chapel" not in world_map.STARTING_DISCOVERED_LOCATIONS:
        world_map.STARTING_DISCOVERED_LOCATIONS = (
            tuple(world_map.STARTING_DISCOVERED_LOCATIONS) + ("drowned_chapel",)
        )

    try:
        import systems.world_progression as progression

        progression.STARTING_DISCOVERED_LOCATIONS = world_map.STARTING_DISCOVERED_LOCATIONS
        progression.VALID_ROUTE_KEYS = {
            progression.route_key(route["a"], route["b"])
            for route in world_map.ROUTES
        }
    except Exception:
        pass


def _patch_loot_tables() -> None:
    from loot_data import LOOT_DROPS
    from units.drowned_chapel_monsters import DROWNED_CHAPEL_LOOT

    LOOT_DROPS.update(DROWNED_CHAPEL_LOOT)


def _patch_game_manager() -> None:
    from game_manager import GameManager
    from citys.mucford.drowned_chapel import drowned_chapel_state

    if getattr(GameManager, "_drowned_chapel_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.chapel_return = False
        drowned_chapel_state(self)

    GameManager.__init__ = __init__
    GameManager._drowned_chapel_installed = True


def _patch_regional_staging_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_drowned_chapel_factory_installed", False):
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
        if "drowned_chapel" in (pending, world_pending, current):
            manager.pending_local_area = None
            manager.pending_world_location = "drowned_chapel"
            from citys.mucford.drowned_chapel import DrownedChapelMenu

            return DrownedChapelMenu(manager)
        return previous_new(cls, manager, *args, **kwargs)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._drowned_chapel_factory_installed = True


def _patch_whisper_marsh_route() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu

    if getattr(ForestExcursionMenu, "_drowned_chapel_route_installed", False):
        return
    previous_enter = ForestExcursionMenu.on_enter
    previous_update = ForestExcursionMenu.update
    previous_draw = ForestExcursionMenu.draw

    def on_enter(self):
        returning = bool(getattr(self.manager, "chapel_return", False))
        result = previous_enter(self)
        if returning:
            self.manager.chapel_return = False
            self.player.rect.center = (self.arena.width - 180, 720)
            self.player.facing_right = False
            self._update_camera()
        return result

    def update(self):
        result = previous_update(self)
        if self.player.rect.right > self.arena.width - 8 and not getattr(self, "marsh_dialogue_active", False):
            self.manager.match_in_progress = False
            self.manager.pending_local_area = "drowned_chapel"
            self.manager.pending_world_location = "drowned_chapel"
            self.next_state = "regional_staging"
        return result

    def draw(self, screen):
        result = previous_draw(self, screen)
        if self.player.rect.centerx > self.arena.width - 430:
            try:
                from ui_kit import draw_text, font_small
                from settings import GRAY

                draw_text(
                    "East path: Drowned Chapel — OPEN RISK Lv 3-5",
                    font_small,
                    GRAY,
                    screen,
                    36,
                    134,
                )
            except Exception:
                pass
        return result

    ForestExcursionMenu.on_enter = on_enter
    ForestExcursionMenu.update = update
    ForestExcursionMenu.draw = draw
    ForestExcursionMenu._drowned_chapel_route_installed = True


def install_drowned_chapel_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    _patch_loot_tables()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_regional_staging_factory()
    _patch_whisper_marsh_route()
    _INSTALLED = True


_patch_world_map_data()
_patch_loot_tables()
