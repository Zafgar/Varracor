# tests/test_playtest10_fixes.py
"""Pelitestikierros 10: commanderin XP näkyviin, COMMAND-johtamispuu
(tiimikoko, huudot, läsnäolo) omalle välilehdelleen, tiimikäskyt
taistelussa ja NPC:iden sprintti."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))

from settings import PLAYER_TEAM, ENEMY_TEAM, GREEN


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# COMMAND-puu ja tiimikoko
# ----------------------------------------------------------------------

def test_command_tree_nodes_exist():
    from skills.commander_skills_data import COMMANDER_COMMAND_TREE
    for node in ("leader_1", "leader_2", "shout_rally", "shout_charge",
                 "drillmaster", "iron_presence"):
        assert node in COMMANDER_COMMAND_TREE
    effects = COMMANDER_COMMAND_TREE["leader_2"]["effects"]
    assert effects["team_cap"] == 10


def test_leadership_caps_roster_with_bunks():
    from units.human import Human
    m = _manager()
    m.team_registered = True
    m.gold = 10000
    pc = m.player_character
    # Barracks tasolla 3 (10 punkkaa) mutta johtajuus oletuksena 6
    m.barracks_level = 3
    assert m.team_capacity() == 6, "johtajuus rajaa vaikka punkkia riittää"
    for i in range(5):
        m.my_team.add(Human(f"F{i}", 0, 0, PLAYER_TEAM))
    assert not m.has_free_bunk()
    rec = Human("Extra", 0, 0, PLAYER_TEAM)
    assert m.hire_unit_by_reference(rec, 10) is False
    assert "leadership" in m.hire_block_message.lower()
    # Recruiter I avaa tilaa
    pc.unlocked_skills.add("leader_1")
    pc.calculate_final_stats()
    assert pc.team_capacity == 8
    assert m.team_capacity() == 8
    assert m.hire_unit_by_reference(rec, 10) is True


def test_shouts_unlock_from_tree():
    m = _manager()
    pc = m.player_character
    assert getattr(pc, "shouts", set()) == set()
    pc.unlocked_skills.update({"shout_rally", "shout_charge"})
    pc.calculate_final_stats()
    assert pc.shouts == {"rally", "charge"}


def test_drillmaster_and_iron_presence_morale():
    from units.human import Human
    m = _manager()
    u = Human("Glad", 0, 0, PLAYER_TEAM)
    m.my_team.add(u)
    pc = m.player_character
    m.mode = "Duel"
    m.current_enemy_team = None
    # Ilman noodeja: +4 / -6
    u.morale = 50
    m.end_match(True);  assert u.morale == 54
    m.end_match(False); assert u.morale == 48
    # Drillmaster + Iron Presence: +8 / -3
    pc.unlocked_skills.update({"drillmaster", "iron_presence"})
    pc.calculate_final_stats()
    u.morale = 50
    m.end_match(True);  assert u.morale == 58
    m.end_match(False); assert u.morale == 55


# ----------------------------------------------------------------------
# Tiimikäskyt taistelussa
# ----------------------------------------------------------------------

def _battle_setup():
    from units.human import Human
    m = _manager()
    pc = m.player_character
    pc.rect.center = (500, 500)
    ally = Human("Ally", 1200, 500, PLAYER_TEAM)
    foe = Human("Foe", 2000, 500, ENEMY_TEAM)
    m.my_team.add(ally)
    m.update_all_groups()

    class _Arena:
        obstacles = []
    m.current_arena = _Arena()
    return m, pc, ally, foe


def test_rally_order_pulls_ally_to_commander():
    m, pc, ally, foe = _battle_setup()
    m.team_order = {"type": "rally"}
    m.team_order_timer = 300
    x0 = ally.rect.centerx
    for _ in range(30):
        ally.run_combat_ai([pc, ally, foe], [], manager=m)
        ally.update([], m)
    assert ally.rect.centerx < x0, "rally vetää gladiaattorin kohti komentajaa"


def test_charge_order_sends_ally_at_enemy():
    m, pc, ally, foe = _battle_setup()
    m.team_order = {"type": "charge"}
    m.team_order_timer = 300
    x0 = ally.rect.centerx
    for _ in range(30):
        ally.run_combat_ai([pc, ally, foe], [], manager=m)
        ally.update([], m)
    assert ally.rect.centerx > x0, "charge ajaa kohti lähintä vihollista"
    assert ally.is_sprinting or ally.rect.centerx > x0 + 40, \
        "charge-käskyllä juostaan"


def test_shout_input_sets_order_and_cooldown():
    m, pc, ally, foe = _battle_setup()
    pc.unlocked_skills.add("shout_rally")
    pc.calculate_final_stats()

    class _Keys:
        def __getitem__(self, code):
            return code == pygame.K_g
    pc._update_shouts(_Keys(), m)
    assert m.team_order == {"type": "rally"}
    assert m.team_order_timer == 300
    assert pc.shout_cooldown > 0
    # Cooldownin aikana ei uutta käskyä
    m.team_order = None
    pc._update_shouts(_Keys(), m)
    assert m.team_order is None, "cooldown estää spämmin"


def test_order_timer_expires():
    m, pc, ally, foe = _battle_setup()
    m.team_order = {"type": "rally"}
    m.team_order_timer = 2
    pc.shout_cooldown = 100

    class _NoKeys:
        def __getitem__(self, code):
            return False
    pc._update_shouts(_NoKeys(), m)
    pc._update_shouts(_NoKeys(), m)
    assert m.team_order_timer == 0
    assert m.team_order is None, "käsky raukeaa ajallaan"


# ----------------------------------------------------------------------
# NPC-sprintti
# ----------------------------------------------------------------------

def test_ai_sprints_when_far_with_stamina():
    from units.human import Human
    m = _manager()
    a = Human("Runner", 0, 300, ENEMY_TEAM)
    t = Human("Target", 900, 300, PLAYER_TEAM)
    m.all_units.empty(); m.all_units.add([a, t])

    class _Arena:
        obstacles = []
    m.current_arena = _Arena()
    a.current_stamina = a.max_stamina
    sprinted = False
    for _ in range(40):
        a.run_combat_ai([a, t], [], manager=m)
        if a.is_sprinting:
            sprinted = True
        a.update([], m)
    assert sprinted, "NPC juoksee kohti kaukaista vihollista"
    # Väsyneenä ei sprintata
    a.rect.center = (0, 300)
    a.current_stamina = a.max_stamina * 0.2
    a.run_combat_ai([a, t], [], manager=m)
    assert not a.is_sprinting, "matala stamina -> ei sprinttiä"


# ----------------------------------------------------------------------
# Skill-valikko
# ----------------------------------------------------------------------

def test_skill_menu_tabs_and_xp_bar():
    m = _manager()
    from menus.commander_skill_menu import CommanderSkillMenu
    menu = CommanderSkillMenu(m)
    assert menu.active_tab == "COMMAND", "johtamispuu on oletusnäkymä"
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    assert menu.tab_rects, "välilehdet piirtyvät"
    # Pelitesti 19: toinen välilehti on VORTEX (Abyss-magia); tradecraft
    # siirtyi Commander PATHS -polkuihin (XP tekemisestä)
    rect, name = next((r, n) for r, n in menu.tab_rects if n == "VORTEX")
    menu._handle_click(rect.center)
    assert menu.active_tab == "VORTEX"
    menu.draw(surf)


def test_keybinds_have_shouts():
    from systems import keybinds
    assert keybinds.keys_for("shout_rally")
    assert keybinds.keys_for("shout_charge")
    labels = dict(keybinds.LABELS)
    assert "shout_rally" in labels and "shout_charge" in labels
