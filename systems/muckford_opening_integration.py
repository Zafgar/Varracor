"""Install and expose the complete Muckford opening and outskirts arc."""

from systems.muckford_opening_core import (
    FOREST_ROAD_WIDTH,
    REGISTRATION_CREATURE_WINS,
    REGISTRATION_FEE_SP,
    REGISTRATION_REPUTATION,
    _opening,
    opening_progress,
    register_team,
    registration_status,
)
from systems.muckford_outskirts_integration import (
    install_muckford_outskirts_integration,
)

# Outskirts contains pure world-map metadata plus idempotent runtime wrappers.
# Install it eagerly so a previously cached opening integration cannot skip the
# new area when import order differs between the game, tests and old saves.
install_muckford_outskirts_integration()

_INSTALLED = False


def install_muckford_opening_integration() -> None:
    global _INSTALLED
    # Keep the outskirts call outside the guard. Its installer is idempotent and
    # this guarantees newly added area hooks are present even when the older
    # opening hooks were installed earlier in the same Python process.
    install_muckford_outskirts_integration()
    if _INSTALLED:
        return
    from systems.muckford_opening_core import install_muckford_opening_core
    from systems.muckford_forest_tutorial import install_muckford_forest_tutorial
    from systems.muckford_city_opening import install_muckford_city_opening

    install_muckford_opening_core()
    install_muckford_forest_tutorial()
    install_muckford_city_opening()
    _INSTALLED = True
