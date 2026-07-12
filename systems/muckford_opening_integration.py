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

_INSTALLED = False


def install_muckford_opening_integration() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    from systems.muckford_opening_core import install_muckford_opening_core
    from systems.muckford_forest_tutorial import install_muckford_forest_tutorial
    from systems.muckford_city_opening import install_muckford_city_opening
    from systems.muckford_outskirts_integration import (
        install_muckford_outskirts_integration,
    )

    install_muckford_opening_core()
    install_muckford_forest_tutorial()
    install_muckford_city_opening()
    install_muckford_outskirts_integration()
    _INSTALLED = True
