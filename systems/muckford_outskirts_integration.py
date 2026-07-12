"""Runtime hooks for the playable Whisper Marsh outskirts."""
from __future__ import annotations


_INSTALLED = False


def _patch_world_map_data() -> None:
    from lore.world_map_data import LOCATIONS

    location = LOCATIONS.get("whisper_marsh")
    if not location:
        return
    location["summary"] = (
        "Playable flooded woodland south-east of Muckford, crossed by the "
        "Greywash channel and a player-developed survey post."
    )
    location["content_state"] = "playable"
    location["services"] = (
        "foraging",
        "monster hunting",
        "survey-post development",
        "fishing foundation",
    )
    location["materials"] = (
        "Bogwort",
        "River Reed",
        "Driftwood",
        "Clay",
    )
    location["threats"] = (
        "Marsh Rats",
        "Drowned Crows",
        "Greywash Troll",
        "flood ambushes",
    )


def _patch_game_manager() -> None:
    from game_manager import GameManager

    if getattr(GameManager, "_muckford_outskirts_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.current_fishing_spots = []
        self.fishing_return_state = "forest_excursion"

    def get_fishing_spots(self):
        return list(getattr(self, "current_fishing_spots", []))

    GameManager.__init__ = __init__
    GameManager.get_fishing_spots = get_fishing_spots
    GameManager._muckford_outskirts_installed = True


def _patch_forest_excursion() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu

    if getattr(ForestExcursionMenu, "_outskirts_integration_installed", False):
        return
    previous_enter = ForestExcursionMenu.on_enter

    def on_enter(self):
        result = previous_enter(self)
        self.manager.current_fishing_spots = list(
            getattr(self.arena, "fishing_spots", [])
        )
        self.manager.fishing_return_state = "forest_excursion"
        return result

    ForestExcursionMenu.on_enter = on_enter
    ForestExcursionMenu._outskirts_integration_installed = True


def _patch_muckford_return_spawn() -> None:
    from citys.mucford.muckford_city_menu import MuckfordCityMenu

    if getattr(MuckfordCityMenu, "_outskirts_spawn_installed", False):
        return
    previous_enter = MuckfordCityMenu.on_enter

    def on_enter(self):
        return_to_forest_gate = (
            getattr(self.manager, "city_spawn_point", None) == "forest_gate"
        )
        result = previous_enter(self)
        if return_to_forest_gate:
            try:
                gate = self._forest_gate_rect()
                self.player.rect.centerx = gate.centerx
                self.player.rect.bottom = max(60, gate.top - 22)
                self.player.facing_right = True
                self._update_camera()
            except Exception:
                pass
        return result

    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu._outskirts_spawn_installed = True


def install_muckford_outskirts_integration() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _patch_world_map_data()
    _patch_game_manager()
    _patch_forest_excursion()
    _patch_muckford_return_spawn()
    _INSTALLED = True
