# tests/test_playtest22_fixes.py
"""Pelitestikierros 22: HP-regen, kyläläisten vuorokausirytmi ja
Rat King -bossitaistelun korjaus.
1) Passiivinen HP-regen: haavat umpeutuvat kun ei oteta osumaa;
   osuma keskeyttää regenin 5 sekunniksi
2) Rat King -jahti EI enää kaadu (spawn_points-lista rikkoi
   _position_unitsin); boss valtaistuimella idässä, pelaajat
   viemärin suulla lännessä, bossipalkki (is_boss)
3) Käyttäjän rikkinäinen bosses/-paketti poistettu - hyvät osat
   (vesi/kuplat/limatipat/putket, vihreä sylkyprojektiili)
   sulautettu maps/rat_sewer- ja vfx-koodiin
4) Griznakin questilinja: hunt_01 valmistuu Rat Kingin kaadosta
5) Kaupungin vuorokausirytmi: toriaikaan (9-17) väki kerääntyy
   kojuille, yöllä (22-07) koteihin; ruuhkaiset paikat hylätään
6) VillagerAI ei aloita töitä yöllä
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM, ENEMY_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _set_hour(clock, hour):
    clock.minutes = hour * 60.0


# ----------------------------------------------------------------------
# 1) Passiivinen HP-regen
# ----------------------------------------------------------------------

def test_passive_hp_regen_heals_over_time():
    from units.human import Human
    u = Human("Toipuja", 0, 0, PLAYER_TEAM)
    u.current_hp = int(u.max_hp * 0.5)
    u.hp_regen_delay = 0
    hp0 = u.current_hp
    for _ in range(600):   # 10 sekuntia
        u.update([], None)
    assert u.current_hp > hp0, "haavat umpeutuvat itsestään"
    # Ei yli maksimin
    u.current_hp = u.max_hp
    for _ in range(120):
        u.update([], None)
    assert u.current_hp == u.max_hp


def test_damage_interrupts_hp_regen():
    from units.human import Human
    u = Human("Kolhittu", 0, 0, PLAYER_TEAM)
    u.take_damage(10, "Physical")
    assert u.hp_regen_delay == 300, "osuma pysäyttää regenin 5 s"
    hp0 = u.current_hp
    for _ in range(200):   # delay vielä voimassa
        u.update([], None)
    assert u.current_hp == hp0, "regen ei käynnisty delayn aikana"


# ----------------------------------------------------------------------
# 2-3) Rat King -jahti
# ----------------------------------------------------------------------

def test_broken_bosses_package_removed():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert not os.path.exists(os.path.join(root, "bosses")), \
        "rikkinäinen bosses/-duplikaatti poistettu"
    import missions.boss_registry as reg
    assert reg.MISSION_REGISTRY["boss_rat_king"] is not None, \
        "maps/rat_sewer-missio latautuu"


def test_rat_king_hunt_starts_and_stages_properly():
    from units.human import Human
    m = _manager()
    f = Human("Jahtaja", 0, 0, PLAYER_TEAM)
    m.my_team.add(f)
    assert m.start_boss_hunt("boss_rat_king") is True, \
        "bossijahti ei saa kaatua spawn_points-listaan"
    king = next((e for e in m.enemy_team if "Rat King" in e.name), None)
    assert king is not None
    assert getattr(king, "is_boss", False), "bossipalkki piirtyy"
    arena = m.current_arena
    assert king.rect.centerx > arena.width * 0.7, "boss valtaistuimella idässä"
    assert f.rect.centerx < 600, "pelaaja viemärin suulla lännessä"
    dist = abs(king.rect.centerx - f.rect.centerx)
    assert dist > 800, "ei enää spawnia päällekkäin bossin kanssa"
    # Henkivartijat putkilla
    guards = [e for e in m.enemy_team if e is not king]
    assert len(guards) >= 2


def test_sewer_arena_atmosphere_draws():
    from maps.rat_sewer.arena import Arena
    arena = Arena()
    assert arena.pipe_points and arena.throne_pos and arena.entry_pos
    b0 = [tuple(b[:2]) for b in arena.bubbles]
    for _ in range(60):
        arena.update(None)
    assert [tuple(b[:2]) for b in arena.bubbles] != b0, "kuplat elävät"
    surf = pygame.Surface((1920, 1080))
    arena.draw_background(surf, (0, 0))
    arena.draw_background(surf, (400, 500))
    arena.draw_foreground(surf, (400, 500))


def test_acid_glob_arcs_and_hits():
    from vfx import VFXManager
    vfx = VFXManager()
    hits = []
    vfx.create_acid_glob((0, 500), (400, 500), on_impact=lambda: hits.append(1))
    glob = [p for p in vfx.particles if type(p).__name__ == "AcidGlob"][0]
    # Kaaren puolivälissä pallo on ilmassa (y < lähtötaso)
    for _ in range(glob.frames_total // 2):
        glob.update()
    assert glob.rect.centery < 480, "limapallo lentää kaaressa"
    for _ in range(glob.frames_total):
        glob.update()
    assert hits == [1], "osuma laukaisi callbackin"


def test_rat_king_kill_completes_griznak_quest():
    from quest_system import quest_manager
    m = _manager()
    quest_manager.accept_quest("hunt_01")
    assert quest_manager.get_quest_status("hunt_01") == "active"
    m.check_quest_completion("boss_rat_king")
    assert quest_manager.get_quest_status("hunt_01") in ("completed",
                                                         "turn_in",
                                                         "finished"), \
        "Rat Kingin kaato kuittaa Griznakin questin"


# ----------------------------------------------------------------------
# 5) Kaupungin vuorokausirytmi
# ----------------------------------------------------------------------

def _city(m):
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    return city


def _sim_npc(city):
    return next(n for n in city.npcs if hasattr(n, "sim_state"))


def test_city_phases_follow_clock():
    m = _manager()
    city = _city(m)
    for hour, phase in ((12, "market"), (19, "evening"), (23, "night"),
                        (3, "night"), (8, "morning")):
        _set_hour(m.world_clock, hour)
        assert city._city_phase() == phase, f"klo {hour} -> {phase}"


def test_market_spots_exist_and_crowding_rejected():
    m = _manager()
    city = _city(m)
    assert city.market_spots, "torilla on oleskelupaikkoja kojujen edessä"
    spot = city.market_spots[0]
    # Ahda 5 NPC:tä samaan pisteeseen -> paikka hylätään
    crowd = [n for n in city.npcs if hasattr(n, "sim_state")][:5]
    for n in crowd:
        n.sim_state = "IDLE"
        n.rect.center = spot
    assert city._spot_crowd(spot) >= 4
    assert city._pick_spot([spot]) is None, "ruuhkainen paikka hylätään"


def test_villagers_go_home_at_night():
    m = _manager()
    city = _city(m)
    _set_hour(m.world_clock, 23)
    npc = _sim_npc(city)
    npc.sim_state = "IDLE"
    npc.sim_timer = 0
    city._sim_choose_action(npc, "night")
    assert npc.sim_state == "ENTERING", "yöllä suunnataan kotiin"
    assert npc.sim_target == npc.sim_home, "koti on pysyvä"
    # Sisällä pysytään koko yö
    npc.sim_state = "INSIDE"
    npc.sim_timer = 1
    city._update_simulation()
    assert npc.sim_state == "INSIDE", "yöllä nukutaan aamuun asti"


def test_market_action_targets_stalls():
    m = _manager()
    city = _city(m)
    _set_hour(m.world_clock, 12)
    npc = _sim_npc(city)
    hits = 0
    for _ in range(40):
        npc.sim_state = "IDLE"
        npc.sim_browse = False
        city._sim_choose_action(npc, "market")
        if getattr(npc, "sim_browse", False):
            hits += 1
    assert hits >= 5, "toriaikaan väki hakeutuu kojuille"


# ----------------------------------------------------------------------
# 6) VillagerAI: yörauha
# ----------------------------------------------------------------------

def test_villager_ai_rests_at_night():
    from units.human import Human
    from ai.villager_ai import VillagerAI, STATE_IDLE
    m = _manager()
    v = Human("Yökukkuja", 500, 500, PLAYER_TEAM)
    ai = VillagerAI(v)
    ai.work_ethic = 1.0   # tekisi AINA töitä
    calls = []
    ai._find_farm_work = lambda *a, **k: calls.append(1) and False
    # Yöllä työnhakua EI edes yritetä
    _set_hour(m.world_clock, 23)
    ai.state_timer = 0
    ai.execute_ai([v], [], manager=m)
    assert ai.state == STATE_IDLE, "yöllä ei aloiteta töitä"
    assert not calls, "työnhaku ohitetaan yöllä"
    # Päivällä työnhaku jatkuu normaalisti
    _set_hour(m.world_clock, 12)
    ai.state_timer = 0
    ai.execute_ai([v], [], manager=m)
    assert calls, "päivällä töitä haetaan taas"
