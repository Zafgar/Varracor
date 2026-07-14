"""Safety and persistence wrappers for the Muckford farming expansion.

The main expansion owns the gameplay. This module adds integration guards:

* farmer NPCs only choose ripe crops supported by their current tool tier;
* farming prompts stay below modal city UI;
* watered crops keep growing while the player is away from Muckford;
* saved meal buffs are restored immediately after loading a game.
"""

from __future__ import annotations


_INSTALLED = False


def _npc_harvest_tool_tier(unit) -> int:
    tier = 0
    equipped = getattr(unit, "equipment", {}).get("main_hand")
    if getattr(equipped, "tool_type", "") == "harvest":
        tier = max(tier, int(getattr(equipped, "tool_tier", 0)))
    for item in getattr(unit, "inventory", []) or []:
        if getattr(item, "tool_type", "") == "harvest":
            tier = max(tier, int(getattr(item, "tool_tier", 0)))
    return tier


def _absolute_world_minutes(manager) -> float:
    from world_clock import DAYS_PER_YEAR

    clock = getattr(manager, "world_clock", None)
    if clock is None:
        return 0.0
    year = int(getattr(clock, "year", 0))
    day = int(getattr(clock, "day", 1))
    minutes = float(getattr(clock, "minutes", 0.0))
    return ((year * DAYS_PER_YEAR + max(0, day - 1)) * 1440.0) + minutes


def _record_world_time(system):
    state = system._state_root()
    state["last_world_minutes"] = _absolute_world_minutes(system.manager)


def _advance_offscreen_growth(system):
    """Apply the world-clock time elapsed since Muckford was last active."""
    from world_clock import MINUTES_PER_FRAME

    state = system._state_root()
    now = _absolute_world_minutes(system.manager)
    previous = state.get("last_world_minutes")
    state["last_world_minutes"] = now
    if previous is None:
        return

    elapsed_minutes = max(0.0, now - float(previous))
    if elapsed_minutes <= 0 or MINUTES_PER_FRAME <= 0:
        return

    # WorldClock uses floating-point minutes. Direct int() truncation can lose
    # one whole frame because values such as 49.999999999 become 49. Round to
    # the nearest simulated frame before applying growth.
    elapsed_frames = max(0, int(round(elapsed_minutes / MINUTES_PER_FRAME)))
    if elapsed_frames <= 0:
        return

    for plot in system.plots:
        if not plot.watered or plot.ready:
            continue
        plot.growth_ticks = min(
            int(plot.data["growth_frames"]),
            int(plot.growth_ticks) + elapsed_frames,
        )
        plot._save_state()
        plot._redraw(force=True)


def install_farming_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    import save_manager
    from ai.villager_ai import VillagerAI
    from citys.mucford.farming_expansion import (
        CropPlot,
        FarmingSystem,
        _restore_meal_buff,
    )
    from citys.mucford.muckford_city_menu import MuckfordCityMenu

    # The base expansion is already installed before this function is called,
    # so this wraps its crop-aware work selector rather than replacing the
    # village's original job system.
    previous_find_work = VillagerAI._find_farm_work

    def _find_farm_work(self, all_units, manager):
        temporarily_blocked = []
        if (
            getattr(self, "job", None) == "Farmer"
            and manager
            and getattr(manager, "current_arena", None)
        ):
            tool_tier = _npc_harvest_tool_tier(self.unit)
            for plot in getattr(manager.current_arena, "crop_plots", []) or []:
                if not isinstance(plot, CropPlot) or not plot.ready:
                    continue
                if int(plot.data.get("required_tool_tier", 1)) > tool_tier:
                    if not plot.being_worked_on:
                        plot.being_worked_on = True
                        temporarily_blocked.append(plot)
        try:
            return previous_find_work(self, all_units, manager)
        finally:
            for plot in temporarily_blocked:
                plot.being_worked_on = False

    VillagerAI._find_farm_work = _find_farm_work

    previous_system_init = FarmingSystem.__init__
    previous_rebind_state = FarmingSystem.rebind_state
    previous_draw = FarmingSystem.draw

    def __init__(self, city_menu):
        previous_system_init(self, city_menu)
        _advance_offscreen_growth(self)

    def rebind_state(self):
        result = previous_rebind_state(self)
        _advance_offscreen_growth(self)
        return result

    def draw(self, screen):
        city = self.city
        manager = self.manager
        modal_open = (
            getattr(city, "show_pause_menu", False)
            or getattr(city, "show_map", False)
            or getattr(city, "active_smeltery", None) is not None
            or getattr(manager, "show_inventory", False)
            or getattr(manager, "active_dialogue", None) is not None
            or getattr(city, "editor_active", False)
        )
        if modal_open:
            return
        return previous_draw(self, screen)

    FarmingSystem.__init__ = __init__
    FarmingSystem.rebind_state = rebind_state
    FarmingSystem.draw = draw

    # Keep the last active Muckford timestamp current, so returning to the city
    # advances only the time truly spent elsewhere.
    previous_city_update = MuckfordCityMenu.update

    def update(self):
        result = previous_city_update(self)
        system = getattr(self, "farming_system", None)
        if system:
            _record_world_time(system)
        return result

    MuckfordCityMenu.update = update

    # save_manager.load_game replaces npc_state. Restore any persisted meal
    # effect before the player can launch another battle from the hub.
    previous_load_game = save_manager.load_game

    def load_game(manager, *args, **kwargs):
        loaded = previous_load_game(manager, *args, **kwargs)
        if loaded:
            _restore_meal_buff(manager)
        return loaded

    save_manager.load_game = load_game
    _INSTALLED = True
