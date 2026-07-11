"""Small safety wrappers for the Muckford farming expansion.

Kept separate so the main expansion remains focused on gameplay.  These guards
prevent farmer NPCs from selecting crops their current sickle cannot harvest
and keep farming prompts underneath modal city UI.
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


def install_farming_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    from ai.villager_ai import VillagerAI
    from citys.mucford.farming_expansion import CropPlot, FarmingSystem

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

    previous_draw = FarmingSystem.draw

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

    FarmingSystem.draw = draw
    _INSTALLED = True
