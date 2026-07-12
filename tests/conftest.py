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
except Exception:
    _wmd = None
    _PRISTINE_LOCATIONS = None


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

    def _restore_pristine():
        _wmd.LOCATIONS.clear()
        _wmd.LOCATIONS.update(copy.deepcopy(_PRISTINE_LOCATIONS))
        if rbi is not None:
            rbi._INSTALLED = False

    _restore_pristine()
    modname = getattr(getattr(request, "module", None), "__name__", "")
    if rbi is not None and "rattlebridge" in modname:
        try:
            rbi.install_rattlebridge_integration()
        except Exception:
            pass
    yield
    _restore_pristine()


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
