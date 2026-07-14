# tests/test_playtest21_fixes.py
"""Pelitestikierros 21: retkikunta + rescue + sääkorjaus.
1) KeyError 'cloudy' korjattu world_clock.draw_hudissa
2) COMMAND-puun Warband-haara: retkikapasiteetti 2/4/6/8/10 ja
   taktiikkanoodit (kite/defend)
3) Muster barracksin sotapöydältä kunnioittaa kapasiteettia
4) Retkikunta spawnaa retkikartalle ja FOLLOW ME pitää ryhmän koossa
5) [T]-taktiikkavalikko: numerot valitsevat käskyn EIVÄTKÄ castaa
6) Kaatunut retkeläinen: pois kentältä + vammat; sairaana viety voi kuolla
7) Commanderin kaatuminen: herää Sunk Caskista (noutopalkkio Mardalle)
   tai barracksista (toveri kertoo raahauksesta)
8) Retkikunta ja käsky säilyvät savessa
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


def _with_party(m, n=2, cap_node="warband_1"):
    """Sankarille warband-noodi ja n soturia retkikuntaan."""
    from units.human import Human
    hero = m.player_character
    hero.unlocked_skills.add(cap_node)
    hero.calculate_final_stats()
    from systems import expedition
    for i in range(n):
        u = Human(f"Retki{i}", 900 + i * 40, 900, PLAYER_TEAM)
        m.my_team.add(u)
        ok, msg = expedition.toggle_member(m, u)
        assert ok, msg
    return hero


def _rift(m, location="rift_whisper_marsh"):
    from menus.rift_site_menu import RiftSiteMenu
    m.pending_world_location = location
    menu = RiftSiteMenu(m)
    menu.on_enter()
    return menu


# ----------------------------------------------------------------------
# 1) Sää-HUD ei kaadu pilviseen päivään
# ----------------------------------------------------------------------

def test_weather_hud_survives_cloudy():
    from ui_kit import font_small
    m = _manager()
    surf = pygame.Surface((1920, 1080))
    for weather in ("clear", "wind", "rain", "storm", "cloudy"):
        m.world_clock.weather = weather
        m.world_clock.draw_hud(surf, font_small)  # ei KeyErroria


# ----------------------------------------------------------------------
# 2) Warband-haara
# ----------------------------------------------------------------------

def test_warband_nodes_and_caps():
    from skills.commander_skills_data import COMMANDER_COMMAND_TREE as T
    caps = [("warband_1", 2), ("warband_2", 4), ("warband_3", 6),
            ("warband_4", 8), ("warband_5", 10)]
    for node, cap in caps:
        assert T[node]["effects"]["expedition_cap"] == cap
    assert T["tactic_kite"]["effects"]["tactic"] == "kite"
    assert T["tactic_defend"]["effects"]["tactic"] == "defend"


def test_expedition_cap_and_tactics_from_tree():
    from systems import expedition
    m = _manager()
    hero = m.player_character
    hero.calculate_final_stats()
    assert hero.expedition_cap == 0, "ilman noodeja ei retkikuntaa"
    assert expedition.party_cap(m) == 0
    base = [oid for oid, _n, _d in expedition.available_orders(hero)]
    assert base == ["follow", "free"], "kite/defend vaativat noodit"
    hero.unlocked_skills.update({"warband_2", "tactic_kite"})
    hero.calculate_final_stats()
    assert hero.expedition_cap == 4
    orders = [oid for oid, _n, _d in expedition.available_orders(hero)]
    assert "kite" in orders and "defend" not in orders


# ----------------------------------------------------------------------
# 3) Muster
# ----------------------------------------------------------------------

def test_muster_respects_cap():
    from units.human import Human
    from systems import expedition
    m = _manager()
    extra = Human("Liikaa", 0, 0, PLAYER_TEAM)
    m.my_team.add(extra)
    # Ilman noodia ei ketään mukaan
    ok, msg = expedition.toggle_member(m, extra)
    assert not ok and "Warband" in msg
    _with_party(m, n=2)  # warband_1 = cap 2, täyteen
    ok, msg = expedition.toggle_member(m, extra)
    assert not ok, "kapasiteetti rajaa"
    # Poisto vapauttaa paikan
    first = m.expedition_party[0]
    ok, _msg = expedition.toggle_member(m, first)
    assert ok and first not in m.expedition_party
    ok, _msg = expedition.toggle_member(m, extra)
    assert ok


def test_barracks_muster_panel_draws():
    from citys.mucford.barracks_interior_menu import BarracksInteriorMenu
    m = _manager()
    _with_party(m, n=1)
    menu = BarracksInteriorMenu(m)
    menu.on_enter()
    menu.show_muster = True
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu._muster_rows, "rosterin rivit klikattavissa"


# ----------------------------------------------------------------------
# 4) Retkikunta kentällä
# ----------------------------------------------------------------------

def test_party_spawns_on_rift_map_and_follows():
    from systems import expedition
    m = _manager()
    _with_party(m, n=2)
    menu = _rift(m)
    assert m.expedition_field_active
    members = menu.expedition_units()
    assert len(members) == 2, "retkikunta spawnasi mukaan"
    px, py = m.player_character.rect.center
    for u in members:
        d = pygame.math.Vector2(u.rect.centerx - px,
                                u.rect.centery - py).length()
        assert d < 250, "spawn Commanderin viereen"
    # FOLLOW ME: kauas raahattu soturi palaa Commanderin luo
    m.expedition_order = "follow"
    stray = members[0]
    stray.rect.center = (px + 700, py)
    d0 = abs(stray.rect.centerx - px)
    for _ in range(90):
        menu.update()
    d1 = abs(stray.rect.centerx - m.player_character.rect.centerx)
    assert d1 < d0 - 100, f"follow vetää takaisin ({d0} -> {d1})"


# ----------------------------------------------------------------------
# 5) Taktiikkavalikko
# ----------------------------------------------------------------------

class _Keys:
    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, code):
        return code in self.down


def test_tactics_menu_selects_order_and_blocks_casts():
    from systems import expedition
    m = _manager()
    hero = _with_party(m, n=1)
    hero.unlocked_skills.add("tactic_kite")
    hero.calculate_final_stats()
    m.expedition_field_active = True
    hero.prev_keys = _Keys()

    # [T] avaa valikon
    open_now = expedition.handle_tactics_input(hero, _Keys(pygame.K_t), m)
    assert open_now and m.tactics_menu_open
    # Valikon ollessa auki numerot varattu käskyille (check_toggle ohittaa)
    hero.prev_keys = _Keys()
    busy = expedition.handle_tactics_input(hero, _Keys(pygame.K_3), m)
    assert busy is True
    assert m.expedition_order == "kite", "3 = KITE (follow/free/kite)"
    assert not m.tactics_menu_open, "valinta sulkee valikon"
    # Ilman retkikenttää valikko ei aukea
    m.expedition_field_active = False
    hero.prev_keys = _Keys()
    assert not expedition.handle_tactics_input(hero, _Keys(pygame.K_t), m)
    assert not m.tactics_menu_open


def test_keybind_tactics_exists():
    from systems import keybinds
    assert keybinds.keys_for("tactics")
    assert "tactics" in dict(keybinds.LABELS)


# ----------------------------------------------------------------------
# 6) Retkeläisen kaatuminen
# ----------------------------------------------------------------------

def test_member_down_gets_wounds_and_leaves_field():
    from systems import expedition, conditions
    m = _manager()
    _with_party(m, n=2)
    u = m.expedition_party[0]
    u._prebattle_death_risk = 0.0
    u.is_dead = True
    expedition.check_party_downs(m)
    assert not u.is_dead, "kannetaan pois hengissä"
    assert u._expedition_out, "retki on hänen osaltaan ohi"
    assert u not in expedition.field_party(m)
    assert conditions.has_condition(u, "fatigue"), "tarvitsee lepoa"
    assert u.current_hp <= u.max_hp * 0.15


def test_sick_member_can_die_on_expedition():
    from systems import expedition
    m = _manager()
    _with_party(m, n=1)
    u = m.expedition_party[0]
    u._prebattle_death_risk = 1.0   # sairaana retkelle -> riski realisoituu
    u.is_dead = True
    expedition.check_party_downs(m)
    assert u not in m.my_team, "menehtyi retkellä"
    assert u not in m.expedition_party


# ----------------------------------------------------------------------
# 7) Commanderin rescue
# ----------------------------------------------------------------------

def test_rescue_to_inn_charges_fee():
    from systems import expedition
    m = _manager()
    m.gold = 100
    m.team_registered = False
    day0 = m.world_clock.day
    state = expedition.commander_down(m, "the Mine Road")
    assert state == "muckford_city"
    assert m.gold == 75, "Marda perii 25 SP"
    assert not m.player_character.is_dead
    assert m.player_character.current_hp >= m.player_character.max_hp * 0.3
    assert m.world_clock.day != day0, "herätään seuraavana aamuna"
    # Saapumisdialogi Sunk Caskissa
    assert expedition.deliver_rescue_dialogue(m, "inn") is True
    assert m.active_dialogue and m.active_dialogue["unit"].name == "Marda"
    assert "Mine Road" in m.active_dialogue["text"]
    assert m.pending_rescue is None, "dialogi vain kerran"


def test_rescue_to_barracks_with_team():
    from units.human import Human
    from systems import expedition
    m = _manager()
    m.gold = 100
    m.team_registered = True
    mate = Human("Toveri", 0, 0, PLAYER_TEAM)
    m.my_team.add(mate)
    state = expedition.commander_down(m, "the rift breach")
    assert state == "barracks_interior"
    assert m.gold == 100, "toverit eivät laskuta"
    assert expedition.deliver_rescue_dialogue(m, "barracks") is True
    assert m.active_dialogue["unit"] is mate, "toveri kertoo raahauksesta"


def test_mine_road_death_uses_rescue():
    from citys.mucford.mine_road_menu import MineRoadMenu
    m = _manager()
    m.gold = 50
    menu = MineRoadMenu(m)
    menu.on_enter()
    assert menu.rescue_on_death
    m.player_character.is_dead = True
    menu.update()
    assert menu.next_state == "muckford_city"
    assert m.pending_rescue and m.pending_rescue["fee"] == 25


# ----------------------------------------------------------------------
# 8) Persistenssi
# ----------------------------------------------------------------------

def test_expedition_saves_and_loads(tmp_path):
    import save_manager
    from systems import expedition
    m = _manager()
    hero = _with_party(m, n=2, cap_node="warband_2")
    hero.unlocked_skills.add("tactic_kite")
    m.expedition_order = "kite"
    names = [u.name for u in m.expedition_party]
    path = str(tmp_path / "exp_save.json")
    assert save_manager.save_game(m, path)

    m2 = _manager()
    assert save_manager.load_game(m2, path)
    assert m2.expedition_order == "kite"
    assert [u.name for u in m2.expedition_party] == names
    for u in m2.expedition_party:
        assert u in list(m2.my_team), "viittaukset ladattuun rosteriin"
