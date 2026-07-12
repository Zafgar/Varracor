"""Runtime integration for the playable Greywash Ford crossing."""
from __future__ import annotations

import pygame


_INSTALLED = False


def _patch_world_map_data() -> None:
    import lore.world_map_data as world_map

    location = world_map.LOCATIONS["greywash_ford"]
    location["content_state"] = "playable"
    location["target_state"] = "regional_staging"
    location["services"] = (
        "ford crossing",
        "river fishing",
        "bridge development",
        "caravan escort",
        "Crown road scouting",
    )
    location["threats"] = (
        "Greywash Riverjaws",
        "Crown Deserters",
        "Ford Brutes",
        "Captain Garran Vale",
        "flood current",
    )
    location["materials"] = (
        "River Reed",
        "Clay",
        "Driftwood",
        "Scrap Iron",
        "ford fish",
    )
    location["boss"] = "Captain Garran Vale"
    location["story_state"] = "playable ford-security chain"

    route_specs = (
        ("whisper_marsh", "greywash_ford", 3, 5, "Lower Greywash bank trail"),
    )
    for a, b, hours, danger, label in route_specs:
        if world_map.get_route(a, b) is None:
            world_map.ROUTES.append(world_map._route(a, b, hours, danger, label))

    try:
        import systems.world_progression as progression

        progression.VALID_ROUTE_KEYS = {
            progression.route_key(route["a"], route["b"])
            for route in world_map.ROUTES
        }
    except Exception:
        pass


def _patch_loot_and_fish_tables() -> None:
    from loot_data import LOOT_DROPS
    from minigames.marsh_fishing import FISH_TABLES, FishEntry
    from units.greywash_ford_monsters import GREYWASH_LOOT

    LOOT_DROPS.update(GREYWASH_LOOT)
    FISH_TABLES["greywash_ford"] = {
        "Greywash Ford": (
            FishEntry("Ford Dace", 31, 9, 104, 2),
            FishEntry("Crownscale Perch", 27, 13, 122, 3),
            FishEntry("Stonebelly Carp", 22, 17, 142, 3),
            FishEntry("Flood Eel", 14, 24, 168, 4),
            FishEntry("Greywash Pike", 6, 38, 205, 4),
        )
    }


def _patch_game_manager() -> None:
    from citys.mucford.greywash_ford import ford_state
    from game_manager import GameManager

    if getattr(GameManager, "_greywash_ford_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.greywash_entry = None
        ford_state(self)

    GameManager.__init__ = __init__
    GameManager._greywash_ford_installed = True


def _patch_regional_staging_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_greywash_ford_factory_installed", False):
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
        if "greywash_ford" in (pending, world_pending, current):
            manager.pending_local_area = None
            manager.pending_world_location = "greywash_ford"
            from citys.mucford.greywash_ford import GreywashFordMenu

            return GreywashFordMenu(manager)
        return previous_new(cls, manager, *args, **kwargs)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._greywash_ford_factory_installed = True


def _patch_fishing_awards() -> None:
    from citys.mucford.greywash_ford import ford_state
    from minigames.marsh_fishing import MarshFishingMenu
    from sound_manager import sound_system

    if getattr(MarshFishingMenu, "_greywash_awards_installed", False):
        return
    previous_award = MarshFishingMenu._award_catch

    def _award_catch(self):
        if getattr(self.anchor, "fish_table", "") != "greywash_ford":
            return previous_award(self)
        fish = self.current_fish
        if fish is None:
            self._lose("The line came back empty.")
            return
        self.manager.inventory[fish.name] = int(self.manager.inventory.get(fish.name, 0)) + 1
        state = ford_state(self.manager)
        state["fish_caught"] = int(state.get("fish_caught", 0)) + 1
        catches = state.setdefault("catches", {})
        catches[fish.name] = int(catches.get(fish.name, 0)) + 1
        try:
            self.manager.record_tier0_event("quest", "greywash_ford_first_catch")
        except Exception:
            pass
        self.phase = "result"
        self.result_success = True
        self.result_text = f"Caught {fish.name}! Market value: {fish.value_sp} SP."
        try:
            sound_system.play_sound("recruit")
        except Exception:
            pass

    MarshFishingMenu._award_catch = _award_catch
    MarshFishingMenu._greywash_awards_installed = True


def _patch_muckford_return_spawn() -> None:
    from citys.mucford.muckford_city_menu import MuckfordCityMenu

    if getattr(MuckfordCityMenu, "_greywash_return_installed", False):
        return
    previous_enter = MuckfordCityMenu.on_enter

    def on_enter(self):
        returning = getattr(self.manager, "city_spawn_point", None) == "greywash_gate"
        result = previous_enter(self)
        if returning:
            self.player.rect.center = (120, max(180, self.arena.height // 2 - 180))
            self.player.facing_right = True
            self._update_camera()
        return result

    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu._greywash_return_installed = True


def _patch_whisper_marsh_bank_route() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu

    if getattr(ForestExcursionMenu, "_greywash_bank_route_installed", False):
        return
    previous_enter = ForestExcursionMenu.on_enter
    previous_update = ForestExcursionMenu.update
    previous_draw = ForestExcursionMenu.draw

    def on_enter(self):
        returning = getattr(self.manager, "marsh_entry", None) == "greywash_ford"
        self.manager.marsh_entry = None
        result = previous_enter(self)
        if returning:
            self.player.rect.center = (145, 1230)
            self.player.facing_right = True
            self._update_camera()
        return result

    def update(self):
        result = previous_update(self)
        if (
            self.next_state is None
            and self.player.rect.left < 7
            and 930 <= self.player.rect.centery <= 1540
            and not getattr(self, "marsh_dialogue_active", False)
        ):
            self.manager.pending_local_area = "greywash_ford"
            self.manager.pending_world_location = "greywash_ford"
            self.manager.greywash_entry = "whisper_marsh"
            self.next_state = "regional_staging"
        return result

    def draw(self, screen):
        result = previous_draw(self, screen)
        route = pygame.Rect(0, 930, 120, 610)
        if self.player.rect.colliderect(route.inflate(110, 100)):
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    route.centerx,
                    route.top - 18,
                    "WALK",
                    (self.camera_x, self.camera_y),
                    "Lower bank trail: Greywash Ford — OPEN RISK Lv 5-7",
                )
            except Exception:
                pass
        return result

    ForestExcursionMenu.on_enter = on_enter
    ForestExcursionMenu.update = update
    ForestExcursionMenu.draw = draw
    ForestExcursionMenu._greywash_bank_route_installed = True


def install_greywash_ford_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    _patch_loot_and_fish_tables()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_regional_staging_factory()
    _patch_fishing_awards()
    _patch_muckford_return_spawn()
    _patch_whisper_marsh_bank_route()
    _INSTALLED = True


_patch_world_map_data()
_patch_loot_and_fish_tables()
