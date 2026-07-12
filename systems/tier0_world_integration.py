"""Runtime hooks exposing the Tier 0 world plan and player tracker."""
from __future__ import annotations

from lore.tier0_world_plan import CURRENT_FOCUS, TIER0_AREAS, next_development_batch
from systems.tier0_world_tracker import (
    ensure_tier0_state,
    mark_tier0_event,
    next_player_objectives,
    tier0_area_advice,
    tier0_phase,
)


_INSTALLED = False


def install_tier0_world_integration() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    from game_manager import GameManager

    if getattr(GameManager, "_tier0_world_tracker_installed", False):
        _INSTALLED = True
        return

    previous_init = GameManager.__init__

    def __init__(self, *args, **kwargs):
        previous_init(self, *args, **kwargs)
        ensure_tier0_state(self)
        self.tier0_world_plan = TIER0_AREAS
        self.tier0_current_development_focus = CURRENT_FOCUS

    def get_tier0_area_advice(self, area_id):
        return tier0_area_advice(self, area_id)

    def record_tier0_event(self, event_type, value, amount=1):
        return mark_tier0_event(self, event_type, value, amount=amount)

    def get_tier0_objectives(self, limit=4):
        return next_player_objectives(self, limit=limit)

    def get_tier0_phase(self):
        return tier0_phase(self)

    def get_tier0_development_queue(self, limit=8):
        # Developer/debug helper. It is static project data, not player state.
        return next_development_batch(limit=limit)

    GameManager.__init__ = __init__
    GameManager.get_tier0_area_advice = get_tier0_area_advice
    GameManager.record_tier0_event = record_tier0_event
    GameManager.get_tier0_objectives = get_tier0_objectives
    GameManager.get_tier0_phase = get_tier0_phase
    GameManager.get_tier0_development_queue = get_tier0_development_queue
    GameManager._tier0_world_tracker_installed = True
    _INSTALLED = True
