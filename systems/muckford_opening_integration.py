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
from systems.muckford_low_fields_integration import (
    install_muckford_low_fields_integration,
)
from systems.tier0_monster_integration import (
    install_tier0_monster_integration,
)
from systems.tier0_world_integration import (
    install_tier0_world_integration,
)
from systems.whisper_marsh_story import (
    install_whisper_marsh_story,
)
from systems.drowned_chapel_integration import (
    install_drowned_chapel_integration,
)
from systems.old_muckford_mine_integration import (
    install_old_muckford_mine_integration,
)
from systems.muckford_warrens_integration import (
    install_muckford_warrens_integration,
)
from systems.greywash_ford_integration import (
    install_greywash_ford_integration,
)
from systems.kingsreach_toll_integration import (
    install_kingsreach_toll_integration,
)
from systems.tier0_finale_integration import (
    install_tier0_finale_integration,
)

# Outskirts, local areas, ecology, story and world tracking use idempotent
# runtime wrappers plus pure registries. Install them eagerly so import order
# cannot hide new content from main, tests or save migration.
install_muckford_outskirts_integration()
install_muckford_low_fields_integration()
install_tier0_monster_integration()
install_tier0_world_integration()
install_whisper_marsh_story()
install_drowned_chapel_integration()
install_old_muckford_mine_integration()
install_muckford_warrens_integration()
install_greywash_ford_integration()
install_kingsreach_toll_integration()
install_tier0_finale_integration()

_INSTALLED = False


def install_muckford_opening_integration() -> None:
    global _INSTALLED
    # Keep these calls outside the guard. Their installers are idempotent and this
    # guarantees newly added content is present when an older opening integration
    # was already cached in the same Python process.
    install_muckford_outskirts_integration()
    install_muckford_low_fields_integration()
    install_tier0_monster_integration()
    install_tier0_world_integration()
    install_whisper_marsh_story()
    install_drowned_chapel_integration()
    install_old_muckford_mine_integration()
    install_muckford_warrens_integration()
    install_greywash_ford_integration()
    install_kingsreach_toll_integration()
    install_tier0_finale_integration()
    if _INSTALLED:
        return
    from systems.muckford_opening_core import install_muckford_opening_core
    from systems.muckford_forest_tutorial import install_muckford_forest_tutorial
    from systems.muckford_city_opening import install_muckford_city_opening

    install_muckford_opening_core()
    install_muckford_forest_tutorial()
    install_muckford_city_opening()
    _INSTALLED = True
