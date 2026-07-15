"""Runtime integration for the playable Muckford Warrens crisis area."""
from __future__ import annotations

import pygame


_INSTALLED = False


def _patch_world_map_data() -> None:
    import lore.world_map_data as world_map

    if "muckford_warrens" not in world_map.LOCATIONS:
        world_map.LOCATIONS["muckford_warrens"] = world_map._location(
            "Muckford Warrens",
            "sundered_heartlands",
            (372, 356),
            (4, 6),
            "dungeon",
            "Sewers, food tunnels and collapsed cellars beneath Muckford.",
            "Violet-eyed rats use stolen food and Vortex waste to sustain an organised army beneath the Tier 0 city.",
            target_state="regional_staging",
            content_state="playable",
            services=("rat-tail hunting", "city crisis", "salvage", "food recovery"),
            threats=("Sewer Rat Swarms", "Violet-Eyed Rats", "Rat Riders", "Waste Gnawers", "Rat King"),
            materials=("Rat Tail", "Rotten Flesh", "Vortex Residue", "Scrap Iron"),
        )

    location = world_map.LOCATIONS["muckford_warrens"]
    location["content_state"] = "playable"
    location["target_state"] = "regional_staging"
    location["services"] = ("rat-tail hunting", "city crisis", "salvage", "food recovery")
    location["threats"] = (
        "Giant Rats",
        "Rat Riders",
        "Brute Rats",
        "Rat King",
    )
    location["materials"] = ("Rat Tail", "Rotten Flesh", "Vortex Residue", "Scrap Iron")
    location["boss"] = "The Rat King of Muckford"
    location["story_state"] = "playable city-crisis chain"

    route_specs = (
        ("muckford", "muckford_warrens", 1, 4, "Hamo's cellar hatch"),
        ("low_fields", "muckford_warrens", 1, 4, "Flood-bank drain culvert"),
    )
    for a, b, hours, danger, label in route_specs:
        if world_map.get_route(a, b) is None:
            world_map.ROUTES.append(world_map._route(a, b, hours, danger, label))

    if "muckford_warrens" not in world_map.STARTING_DISCOVERED_LOCATIONS:
        world_map.STARTING_DISCOVERED_LOCATIONS = (
            tuple(world_map.STARTING_DISCOVERED_LOCATIONS) + ("muckford_warrens",)
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
    # Pelitesti 25: warrens käyttää nyt OIKEITA rottayksiköitä (Giant Rat,
    # Rat Rider, Rat King), joilla on jo omat LOOT_DROPS-taulut. Erillistä
    # WARRENS_LOOT-taulua ei enää tarvita.
    return


def _patch_game_manager() -> None:
    from citys.mucford.muckford_warrens import warrens_state
    from game_manager import GameManager

    if getattr(GameManager, "_muckford_warrens_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.warrens_entry = None
        warrens_state(self)

    GameManager.__init__ = __init__
    GameManager._muckford_warrens_installed = True


def _patch_regional_staging_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_muckford_warrens_factory_installed", False):
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
        if "muckford_warrens" in (pending, world_pending, current):
            manager.pending_local_area = None
            manager.pending_world_location = "muckford_warrens"
            from citys.mucford.muckford_warrens import MuckfordWarrensMenu

            return MuckfordWarrensMenu(manager)
        return previous_new(cls, manager, *args, **kwargs)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._muckford_warrens_factory_installed = True


def _patch_muckford_hatch_and_raids() -> None:
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from citys.mucford.muckford_warrens import CitySewerHatch, warrens_state
    from sound_manager import sound_system

    if getattr(MuckfordCityMenu, "_muckford_warrens_hatch_installed", False):
        return

    previous_init = MuckfordCityMenu.__init__
    previous_enter = MuckfordCityMenu.on_enter
    previous_handle = MuckfordCityMenu.handle_event
    previous_draw = MuckfordCityMenu.draw
    previous_rat_king_defeated = MuckfordCityMenu._rat_king_defeated
    previous_update_raids = MuckfordCityMenu._update_raids

    def __init__(self, manager, *args, **kwargs):
        previous_init(self, manager, *args, **kwargs)
        state = warrens_state(manager)
        hamo = getattr(self, "hamo", None)
        if hamo is not None:
            x = hamo.rect.centerx - 52
            y = hamo.rect.bottom + 36
        else:
            x = self.arena.width // 2 + 145
            y = self.arena.height // 2 + 175
        self.warrens_hatch = CitySewerHatch(
            int(x),
            int(y),
            cleared=bool(state.get("city_raids_ended")),
        )
        self.arena.props.append(self.warrens_hatch)

    def on_enter(self):
        return_to_hatch = getattr(self.manager, "city_spawn_point", None) == "warrens_hatch"
        result = previous_enter(self)
        state = warrens_state(self.manager)
        hatch = getattr(self, "warrens_hatch", None)
        if hatch is not None:
            hatch.cleared = bool(state.get("city_raids_ended"))
            hatch._redraw()
        if return_to_hatch and hatch is not None:
            self.player.rect.centerx = hatch.rect.centerx
            self.player.rect.top = hatch.rect.bottom + 24
            self.player.facing_right = False
            self._update_camera()
        return result

    def handle_event(self, event):
        hatch = getattr(self, "warrens_hatch", None)
        if (
            hatch is not None
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_e
            and not getattr(self, "show_map", False)
            and not getattr(self, "show_pause_menu", False)
            and getattr(self, "active_smeltery", None) is None
            and not getattr(self.manager, "active_dialogue", None)
            and self.player.rect.colliderect(hatch.rect.inflate(54, 54))
        ):
            self.manager.pending_local_area = "muckford_warrens"
            self.manager.pending_world_location = "muckford_warrens"
            self.manager.warrens_entry = "muckford"
            self.next_state = "regional_staging"
            try:
                sound_system.play_sound("click")
            except Exception:
                pass
            return
        return previous_handle(self, event)

    def draw(self, screen):
        result = previous_draw(self, screen)
        hatch = getattr(self, "warrens_hatch", None)
        if (
            hatch is not None
            and not getattr(self, "show_map", False)
            and not getattr(self, "show_pause_menu", False)
            and getattr(self, "active_smeltery", None) is None
            and self.player.rect.colliderect(hatch.rect.inflate(88, 88))
        ):
            state = warrens_state(self.manager)
            label = (
                "Enter secured Muckford Warrens"
                if state.get("city_raids_ended")
                else "Enter Muckford Warrens (OPEN RISK Lv 4-6)"
            )
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    hatch.rect.centerx,
                    hatch.rect.top - 18,
                    "E",
                    (self.camera_x, self.camera_y),
                    label,
                )
            except Exception:
                pass
        return result

    def _rat_king_defeated(self):
        state = warrens_state(self.manager)
        if state.get("boss_defeated") or state.get("city_raids_ended"):
            return True
        return previous_rat_king_defeated(self)

    def _update_raids(self):
        state = warrens_state(self.manager)
        if state.get("city_raids_ended"):
            for rat in list(getattr(self, "raid_rats", ())):
                if rat in self.manager.all_units:
                    self.manager.all_units.remove(rat)
            self.raid_rats = []
            self.raid_state = "idle"
            self.manager.next_raid_day = 10 ** 9
            if not getattr(self, "_warrens_peace_announced", False):
                self.raid_result = "The Warrens are secured. No rat raid comes."
                self.raid_result_timer = 300
                self._warrens_peace_announced = True
            return
        return previous_update_raids(self)

    MuckfordCityMenu.__init__ = __init__
    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu.handle_event = handle_event
    MuckfordCityMenu.draw = draw
    MuckfordCityMenu._rat_king_defeated = _rat_king_defeated
    MuckfordCityMenu._update_raids = _update_raids
    MuckfordCityMenu._muckford_warrens_hatch_installed = True


def _patch_low_fields_drain() -> None:
    from citys.mucford.low_fields import LowFieldsMenu

    if getattr(LowFieldsMenu, "_muckford_warrens_drain_installed", False):
        return
    previous_enter = LowFieldsMenu.on_enter
    previous_update = LowFieldsMenu.update
    previous_draw = LowFieldsMenu.draw

    def on_enter(self):
        returning_from_warrens = getattr(self.manager, "low_fields_entry", None) == "warrens"
        result = previous_enter(self)
        if returning_from_warrens:
            self.player.rect.center = (150, self.arena.height - 420)
            self.player.facing_right = True
            self._update_camera()
        return result

    def update(self):
        result = previous_update(self)
        if (
            self.next_state is None
            and self.player.rect.left < 7
            and self.player.rect.centery > self.arena.height - 760
            and not getattr(self, "dialogue_active", False)
        ):
            self.manager.match_in_progress = False
            self.manager.pending_local_area = "muckford_warrens"
            self.manager.pending_world_location = "muckford_warrens"
            self.manager.warrens_entry = "low_fields"
            self.next_state = "regional_staging"
        return result

    def draw(self, screen):
        result = previous_draw(self, screen)
        drain = pygame.Rect(0, self.arena.height - 720, 120, 520)
        if self.player.rect.colliderect(drain.inflate(100, 90)):
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    drain.centerx,
                    drain.top - 16,
                    "WALK",
                    (self.camera_x, self.camera_y),
                    "Drain culvert: Muckford Warrens — OPEN RISK Lv 4-6",
                )
            except Exception:
                pass
        return result

    LowFieldsMenu.on_enter = on_enter
    LowFieldsMenu.update = update
    LowFieldsMenu.draw = draw
    LowFieldsMenu._muckford_warrens_drain_installed = True


def install_muckford_warrens_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    _patch_loot_tables()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_regional_staging_factory()
    _patch_muckford_hatch_and_raids()
    _patch_low_fields_drain()
    _INSTALLED = True


_patch_world_map_data()
_patch_loot_tables()
