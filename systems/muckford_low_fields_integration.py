"""Runtime integration for the playable Muckford Low Fields."""
from __future__ import annotations

import pygame


_INSTALLED = False


def _patch_world_map_data() -> None:
    import lore.world_map_data as world_map

    if "low_fields" not in world_map.LOCATIONS:
        world_map.LOCATIONS["low_fields"] = world_map._location(
            "Muckford Low Fields",
            "sundered_heartlands",
            (385, 372),
            (1, 3),
            "farmland",
            "Wet crop fields and irrigation channels immediately south of Muckford.",
            "These fields feed the Shanty Consortium. Broken sluices, hungry marsh fauna and ruined carts make every harvest a local emergency.",
            target_state="regional_staging",
            content_state="playable",
            services=("gathering", "field work", "settlement development"),
            threats=("Mud Mites", "Reed Skitters", "Marsh Rats"),
            materials=("Carrot", "Potato", "Onion", "River Reed", "Clay", "Softwood"),
        )

    route_specs = (
        ("muckford", "low_fields", 2, 1, "Low Fields track"),
        ("low_fields", "whisper_marsh", 2, 2, "Flood-bank path"),
    )
    for a, b, hours, danger, label in route_specs:
        if world_map.get_route(a, b) is None:
            world_map.ROUTES.append(world_map._route(a, b, hours, danger, label))

    if "low_fields" not in world_map.STARTING_DISCOVERED_LOCATIONS:
        world_map.STARTING_DISCOVERED_LOCATIONS = (
            tuple(world_map.STARTING_DISCOVERED_LOCATIONS) + ("low_fields",)
        )

    # world_progression binds the starting tuple and computes route keys during
    # import. Refresh those derived values when this integration loads later.
    try:
        import systems.world_progression as progression

        progression.STARTING_DISCOVERED_LOCATIONS = world_map.STARTING_DISCOVERED_LOCATIONS
        progression.VALID_ROUTE_KEYS = {
            progression.route_key(route["a"], route["b"])
            for route in world_map.ROUTES
        }
    except Exception:
        pass


def _patch_game_manager() -> None:
    from game_manager import GameManager
    from citys.mucford.low_fields import low_fields_state

    if getattr(GameManager, "_low_fields_state_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.pending_local_area = None
        self.low_fields_entry = None
        self.marsh_return_state = None
        low_fields_state(self)

    GameManager.__init__ = __init__
    GameManager._low_fields_state_installed = True


def _patch_regional_staging_factory() -> None:
    from menus.regional_staging_menu import RegionalStagingMenu

    if getattr(RegionalStagingMenu, "_low_fields_factory_installed", False):
        return

    def __new__(cls, manager, *args, **kwargs):
        pending = getattr(manager, "pending_local_area", None)
        world_pending = getattr(manager, "pending_world_location", None)
        current = (
            getattr(manager, "npc_state", {})
            .get("world_progression", {})
            .get("current_location")
        )
        if "low_fields" in (pending, world_pending, current):
            manager.pending_local_area = None
            manager.pending_world_location = "low_fields"
            from citys.mucford.low_fields import LowFieldsMenu

            return LowFieldsMenu(manager)
        return object.__new__(cls)

    RegionalStagingMenu.__new__ = staticmethod(__new__)
    RegionalStagingMenu._low_fields_factory_installed = True


def _patch_muckford_gate() -> None:
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from sound_manager import sound_system

    if getattr(MuckfordCityMenu, "_low_fields_gate_installed", False):
        return

    def _low_fields_gate_rect(self):
        y = int(self.arena.height * 0.64) - 110
        return pygame.Rect(0, y, 75, 220)

    previous_enter = MuckfordCityMenu.on_enter
    previous_handle = MuckfordCityMenu.handle_event
    previous_draw = MuckfordCityMenu.draw

    def on_enter(self):
        return_to_gate = getattr(self.manager, "city_spawn_point", None) == "low_fields_gate"
        result = previous_enter(self)
        if return_to_gate:
            gate = self._low_fields_gate_rect()
            self.player.rect.left = gate.right + 20
            self.player.rect.centery = gate.centery
            self.player.facing_right = False
            self._update_camera()
        return result

    def handle_event(self, event):
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_e
            and not getattr(self, "show_map", False)
            and not getattr(self, "show_pause_menu", False)
            and getattr(self, "active_smeltery", None) is None
            and not getattr(self.manager, "active_dialogue", None)
            and self.player.rect.colliderect(self._low_fields_gate_rect().inflate(45, 45))
        ):
            self.manager.pending_local_area = "low_fields"
            self.manager.pending_world_location = "low_fields"
            self.manager.low_fields_entry = "muckford"
            self.next_state = "regional_staging"
            try:
                sound_system.play_sound("click")
            except Exception:
                pass
            return
        return previous_handle(self, event)

    def draw(self, screen):
        result = previous_draw(self, screen)
        if (
            not getattr(self, "show_map", False)
            and not getattr(self, "show_pause_menu", False)
            and getattr(self, "active_smeltery", None) is None
            and self.player.rect.colliderect(self._low_fields_gate_rect().inflate(85, 85))
        ):
            gate = self._low_fields_gate_rect()
            try:
                self.manager._draw_floating_prompt(
                    screen,
                    gate.centerx,
                    gate.top - 18,
                    "E",
                    (self.camera_x, self.camera_y),
                    "Enter Muckford Low Fields (Lv 1-3)",
                )
            except Exception:
                pass
        return result

    MuckfordCityMenu._low_fields_gate_rect = _low_fields_gate_rect
    MuckfordCityMenu.on_enter = on_enter
    MuckfordCityMenu.handle_event = handle_event
    MuckfordCityMenu.draw = draw
    MuckfordCityMenu._low_fields_gate_installed = True


def _patch_whisper_marsh_return() -> None:
    from citys.mucford.forest_excursion import ForestExcursionMenu

    if getattr(ForestExcursionMenu, "_low_fields_return_installed", False):
        return
    previous_update = ForestExcursionMenu.update

    def update(self):
        result = previous_update(self)
        if (
            self.next_state == "muckford_city"
            and getattr(self.manager, "marsh_return_state", None) == "low_fields"
        ):
            self.manager.marsh_return_state = None
            self.manager.pending_local_area = "low_fields"
            self.manager.pending_world_location = "low_fields"
            self.manager.low_fields_entry = "whisper_marsh"
            self.next_state = "regional_staging"
        return result

    ForestExcursionMenu.update = update
    ForestExcursionMenu._low_fields_return_installed = True


def install_muckford_low_fields_integration() -> None:
    global _INSTALLED
    _patch_world_map_data()
    if _INSTALLED:
        return
    _patch_game_manager()
    _patch_regional_staging_factory()
    _patch_muckford_gate()
    _patch_whisper_marsh_return()
    _INSTALLED = True


_patch_world_map_data()
