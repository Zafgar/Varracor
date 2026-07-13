# tests/conftest.py
"""
Testien yhteinen alustus: headless pygame (ei ikkunaa eikä ääntä).
Aja testit projektin juuresta:  python -m pytest tests/ -v
"""
import os
import sys

# Headless-ajurit ENNEN pygamen importtia
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Projektin juuri polkuun ja työhakemistoksi (asset-polut ovat suhteellisia)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import copy
import pygame
import pytest

# Tilannekuva maailmankartan PUHTAASTA perusdatasta OTETAAN heti (ennen kuin
# mikaan testimoduuli importtaa barracks_menun, joka asentaa Rattlebridge-
# integraation ja muokkaa LOCATIONS["rattlebridge"]-dictia). Nain per-testi-
# eristys voi palauttaa aidon perustilan.
try:
    from lore import world_map_data as _wmd
    _PRISTINE_LOCATIONS = copy.deepcopy(_wmd.LOCATIONS)
    _PRISTINE_ROUTES = copy.deepcopy(_wmd.ROUTES)
except Exception:
    _wmd = None
    _PRISTINE_LOCATIONS = None
    _PRISTINE_ROUTES = None


# The Muckford opening world integration adds runtime LOCATIONS/ROUTES/content
# that most tests (city, world systems, quests, etc.) rely on ambiently. Only a
# few modules assert the PRISTINE static world graph and must NOT see the runtime
# additions. Re-install the integration for everyone except those.
_STATIC_GRAPH_MODULES = (
    "world_map_progression",
    "causeway_journey",
)


@pytest.fixture(autouse=True)
def _isolate_world_map(request):
    """Eristaa maailmankartan globaali data testien valilta.

    Rattlebridge-integraatio patchaa LOCATIONS["rattlebridge"]:n playable-tilaan
    (target_state -> rattlebridge_city). Progression/UI-testit odottavat
    perustilaa (regional_staging), rattlebridge-testit patchattua. Ilman
    eristysta importin sivuvaikutus vuoti ja aiheutti jarjestysriippuvaisen
    hajoamisen. Palautetaan puhdas perustila, ja patchataan vain jos testi
    kuuluu rattlebridge-moduuliin."""
    if _wmd is None or _PRISTINE_LOCATIONS is None:
        yield
        return
    try:
        import systems.rattlebridge_integration as rbi
    except Exception:
        rbi = None

    def _restore_locations():
        _wmd.LOCATIONS.clear()
        _wmd.LOCATIONS.update(copy.deepcopy(_PRISTINE_LOCATIONS))
        if rbi is not None:
            rbi._INSTALLED = False

    def _set_routes(routes):
        _wmd.ROUTES[:] = copy.deepcopy(routes)
        try:
            import systems.world_progression as _wp
            _wp.VALID_ROUTE_KEYS = {
                _wp.route_key(r["a"], r["b"]) for r in _wmd.ROUTES
            }
        except Exception:
            pass

    modname = getattr(getattr(request, "module", None), "__name__", "")
    is_static_graph = any(tag in modname for tag in _STATIC_GRAPH_MODULES)

    _restore_locations()
    # Only the static-graph modules require a pristine ROUTES table. Runtime
    # integrations (Muckford outskirts, Kingsreach, ...) append routes globally;
    # restoring only LOCATIONS left those routes pointing at wiped nodes and
    # corrupted the graph for these tests. Snapshot the ambient routes and put
    # them back on teardown so other modules keep their runtime world content.
    ambient_routes = None
    if is_static_graph:
        ambient_routes = [copy.deepcopy(r) for r in _wmd.ROUTES]
        _set_routes(_PRISTINE_ROUTES)

    if rbi is not None and "rattlebridge" in modname:
        try:
            rbi.install_rattlebridge_integration()
        except Exception:
            pass
    yield
    _restore_locations()
    if ambient_routes is not None:
        _set_routes(ambient_routes)


@pytest.fixture(scope="session", autouse=True)
def pygame_headless():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield
    pygame.quit()


@pytest.fixture()
def manager():
    """Tuore GameManager per testi."""
    from game_manager import GameManager
    return GameManager()


def run_duel(m, unit_a, unit_b, max_frames=3600):
    """Ajaa kaksintaistelun loppuun tai max_frames asti. Palauttaa dictin."""
    from settings import PLAYER_TEAM, ENEMY_TEAM
    unit_a.team_color = PLAYER_TEAM
    unit_b.team_color = ENEMY_TEAM
    m.match_in_progress = True
    m.current_arena = None
    m.my_team.add(unit_a)
    m.enemy_team.add(unit_b)
    m.all_units.add(unit_a, unit_b)

    hp_start = (unit_a.current_hp, unit_b.current_hp)
    damaged = False
    for frame in range(max_frames):
        for u in (unit_a, unit_b):
            if not u.is_dead:
                u.run_combat_ai(m.all_units, None, manager=m)
                u.update(None, manager=m)
        m.vfx.update(obstacles=None)
        if unit_a.current_hp < hp_start[0] or unit_b.current_hp < hp_start[1]:
            damaged = True
        if unit_a.is_dead or unit_b.is_dead:
            return {"ended": True, "damaged": damaged, "frames": frame,
                    "winner": unit_a if unit_b.is_dead else unit_b}
    return {"ended": False, "damaged": damaged, "frames": max_frames, "winner": None}
