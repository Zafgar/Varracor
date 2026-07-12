"""Runtime integration for the playable Rattlebridge expansion."""

from __future__ import annotations

import pygame


_INSTALLED = False
RATTLEBRIDGE_STATES = {
    "rattlebridge_city",
    "rattlebridge_span",
    "rattlebridge_hospital",
    "rattlebridge_scrapring",
    "rattlebridge_contracts",
    "rattlebridge_canalworks",
}


def _patch_world_location():
    from lore.world_map_data import LOCATIONS

    location = LOCATIONS.get("rattlebridge")
    if not location:
        return
    location.update({
        "level_range": (6, 10),
        "target_state": "rattlebridge_city",
        "content_state": "playable",
        "services": (
            "The Scrapring Tier 1 league",
            "Ironspan Union Market",
            "The Span",
            "Bridgeward Chapel-Hospital",
            "Canalworks patrols",
            "Freight storage",
        ),
        "threats": (
            "Gutter Swarm",
            "Hush-Mantle",
            "bridge gangs",
            "Crown toll corruption",
        ),
        "materials": (
            "Iron Ore",
            "Iron Ingot",
            "Parchment Sheet",
            "Nightcap Fungus",
            "Tanned Hide",
        ),
    })


def _patch_global_ui():
    from game_manager import GameManager

    if getattr(GameManager, "_rattlebridge_ui_installed", False):
        return
    previous_handle = GameManager.handle_ui_event
    previous_draw = GameManager.draw_ui_overlay

    def handle_ui_event(self, event, current_state_key):
        # Rattlebridge's local maps own E/M/TAB/ESC and draw their own overlays.
        if current_state_key in RATTLEBRIDGE_STATES:
            return None
        return previous_handle(self, event, current_state_key)

    def draw_ui_overlay(self, screen, current_state_key):
        if current_state_key in RATTLEBRIDGE_STATES:
            return None
        return previous_draw(self, screen, current_state_key)

    GameManager.handle_ui_event = handle_ui_event
    GameManager.draw_ui_overlay = draw_ui_overlay
    GameManager._rattlebridge_ui_installed = True


def _patch_market_return():
    from menus.market_menu import MarketMenu
    from settings import GOLD_COLOR
    from ui_kit import font_title

    if getattr(MarketMenu, "_rattlebridge_return_installed", False):
        return
    previous_event = MarketMenu.handle_event
    previous_draw = MarketMenu.draw

    def _return_state(self):
        return getattr(self.manager, "market_return_state", None) or "muckford_city"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = _return_state(self)
            return
        if self.btn_back.is_clicked(event):
            self.next_state = _return_state(self)
            return
        return previous_event(self, event)

    def draw(self, screen):
        result = previous_draw(self, screen)
        if _return_state(self) == "rattlebridge_city":
            title = font_title.render("IRONSPAN UNION MARKET", True, GOLD_COLOR)
            self.draw_header_bar(screen, title)
        return result

    MarketMenu.handle_event = handle_event
    MarketMenu.draw = draw
    MarketMenu._rattlebridge_return_installed = True


def _patch_storage_return():
    from menus.city_storage_menu import CityStorageMenu
    from settings import GOLD_COLOR, WHITE
    from ui_kit import draw_text, font_small

    if getattr(CityStorageMenu, "_rattlebridge_return_installed", False):
        return
    previous_event = CityStorageMenu.handle_event
    previous_draw = CityStorageMenu.draw

    def _return_state(self):
        return getattr(self.manager, "city_storage_return_state", None) or "muckford_city"

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.next_state = _return_state(self)
            return
        if self.btn_back.is_clicked(event):
            self.next_state = _return_state(self)
            return
        return previous_event(self, event)

    def draw(self, screen):
        result = previous_draw(self, screen)
        if _return_state(self) == "rattlebridge_city":
            draw_text("IRONSPAN FREIGHT WAREHOUSE", font_small, GOLD_COLOR,
                      screen, self.px + 300, self.py + 20)
            draw_text("Shared city storage", font_small, WHITE,
                      screen, self.px + 410, self.py + 48)
        return result

    CityStorageMenu.handle_event = handle_event
    CityStorageMenu.draw = draw
    CityStorageMenu._rattlebridge_return_installed = True


def _patch_game_manager_defaults():
    from game_manager import GameManager

    if getattr(GameManager, "_rattlebridge_defaults_installed", False):
        return
    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        self.market_return_state = getattr(self, "market_return_state", "muckford_city")
        self.city_storage_return_state = getattr(
            self, "city_storage_return_state", "muckford_city"
        )
        self.npc_state.setdefault("rattlebridge", {
            "visited": False,
            "districts_visited": [],
            "hush_mantle_sightings": 0,
            "gutter_patrols": 0,
        })

    GameManager.__init__ = __init__
    GameManager._rattlebridge_defaults_installed = True


def install_rattlebridge_integration():
    global _INSTALLED
    if _INSTALLED:
        return
    _patch_world_location()
    _patch_global_ui()
    _patch_market_return()
    _patch_storage_return()
    _patch_game_manager_defaults()
    _INSTALLED = True
