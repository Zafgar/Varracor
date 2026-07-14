# tests/test_playtest19_fixes.py
"""Pelitestikierros 19: Commander-puiden rework.
1) Skill-valikon välilehdet: COMMAND + VORTEX (tradecraft pois -
   elämäntaidot elävät PATHS-poluissa, XP tekemisestä)
2) VORTEX-puu: noodit maksavat SP + Vortex-kristalleja; reitit
   palauttavat introssa menetetyt loitsut (SeamCut/VortexWarp/RiftPulse)
   ja antavat passiiveja (mana, teho, cooldownit, työntövoima)
3) Rift-eventti: Vortex-repeämä aukeaa Muckfordiin; sinetöinti
   (keräyskanava) antaa Vortex-kristalleja; sinetöimätön sulkeutuu
4) Matalan tierin työkalut käyvät käteen ilman puun noodeja
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ----------------------------------------------------------------------
# 1) Välilehdet
# ----------------------------------------------------------------------

def test_skill_menu_has_command_and_vortex_tabs():
    from menus.commander_skill_menu import CommanderSkillMenu
    m = _manager()
    menu = CommanderSkillMenu(m)
    names = [n for n, _t in menu.tabs]
    assert names == ["COMMAND", "VORTEX"], \
        "tradecraft poistui - työkalut/elämäntaidot PATHS-poluissa"
    surf = pygame.Surface((1920, 1080))
    menu.draw(surf)
    menu.active_tab = "VORTEX"
    menu.draw(surf)  # vortex-puu piirtyy kaatumatta


# ----------------------------------------------------------------------
# 2) VORTEX-puu
# ----------------------------------------------------------------------

def test_vortex_node_requires_crystals():
    from menus.commander_skill_menu import CommanderSkillMenu
    from skills.vortex_tree_data import CRYSTAL_ITEM
    m = _manager()
    menu = CommanderSkillMenu(m)
    menu.active_tab = "VORTEX"
    hero = m.player_character
    hero.level = 5
    hero.skill_points = 10
    # Ilman kristalleja ei aukea
    menu._try_unlock("riftbound")
    assert "riftbound" not in hero.unlocked_skills
    assert hero.skill_points == 10, "pisteitä ei kulunut turhaan"
    # Kristallien kanssa aukeaa ja kristallit kuluvat
    m.inventory[CRYSTAL_ITEM] = 3
    menu._try_unlock("riftbound")
    assert "riftbound" in hero.unlocked_skills
    assert m.inventory.get(CRYSTAL_ITEM, 0) == 2
    assert hero.skill_points == 9


def test_vortex_route_grants_spell_and_passives():
    from menus.commander_skill_menu import CommanderSkillMenu
    from skills.vortex_tree_data import CRYSTAL_ITEM
    from spells.commander.rift_pulse import RiftPulse
    m = _manager()
    menu = CommanderSkillMenu(m)
    menu.active_tab = "VORTEX"
    hero = m.player_character
    hero.level = 10
    hero.skill_points = 20
    m.inventory[CRYSTAL_ITEM] = 20
    # Tyhjennä spell-slotit jotta myöntö näkyy
    for slot in ("spell1", "spell2", "spell3", "spell4", "spell5",
                 "spell6"):
        hero.equipment[slot] = None
    hero.calculate_final_stats()
    mana0 = hero.max_mana

    menu._try_unlock("riftbound")
    assert hero.max_mana == mana0 + 15, "Riftbound antaa manaa"

    menu._try_unlock("vortex_pulse_1")
    granted = [hero.equipment.get(s) for s in
               ("spell1", "spell2", "spell3")]
    assert any(isinstance(sp, RiftPulse) for sp in granted), \
        "reitti palauttaa Rift Pulsen slottiin"

    menu._try_unlock("vortex_pulse_2")
    assert hero.pulse_force == 60, "Concussive Breach lisää työntöä"

    # Passiivi osuu itse loitsuun: työntö 160 + 60
    from units.human import Human
    from settings import ENEMY_TEAM
    hero.rect.center = (1000, 1000)
    hero.current_mana = hero.max_mana
    foe = Human("Uhri", 0, 0, ENEMY_TEAM)
    foe.rect.center = (1050, 1000)
    m.all_units.empty()
    m.all_units.add([hero, foe])
    m.current_arena = None
    spell = next(sp for sp in granted if isinstance(sp, RiftPulse))
    assert spell.cast(hero, None, m) is True
    dist = abs(foe.rect.centerx - hero.rect.centerx)
    assert dist >= 250, f"tehostettu työntö kantaa ({dist}px)"


def test_vortex_cdr_reduces_cooldown():
    from spells.commander.rift_pulse import RiftPulse
    m = _manager()
    hero = m.player_character
    hero.equipment["spell1"] = RiftPulse()
    hero.current_mana = hero.max_mana = 200
    hero.unlocked_skills.update({"riftbound", "vortex_step_1",
                                 "vortex_step_2"})
    hero.calculate_final_stats()
    assert hero.vortex_cdr == pytest.approx(0.20)
    m.all_units.empty()
    m.all_units.add([hero])
    m.current_arena = None
    hero.current_mana = hero.max_mana
    assert hero._try_use_slot("spell1", 1000, 1000, [hero], m)
    cd = hero.spell_cooldowns["spell1"]
    assert cd == int(300 * 0.8), "Slipstream: -20% cooldown"


# ----------------------------------------------------------------------
# 3) Rift-eventti
# ----------------------------------------------------------------------

def test_rift_spawns_and_sealing_grants_crystals():
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import RiftFissure
    m = _manager()
    city = MuckfordCityMenu(m)
    city.on_enter()
    city._update_rift_event()   # alustaa kentät
    city._spawn_rift()
    rift = city._rift
    assert isinstance(rift, RiftFissure)
    assert rift in city.arena.props
    assert "rift" in city._event_banner_text.lower()
    # Sinetöinti keräyskanavalla
    m.player_character.rect.center = (rift.rect.centerx + 40,
                                      rift.rect.centery)
    assert rift.try_begin_channel(m.player_character, m) is True
    for _ in range(rift.swing_interval * rift.channel_swings_needed + 2):
        rift.update(None, m)
    assert rift.is_empty, "repeämä sinetöity"
    assert m.inventory.get("Vortex Crystal", 0) >= 1, \
        "sinetöinti antoi kristalleja"
    # Poistuu kentältä pienen viiveen jälkeen
    for _ in range(120):
        city._update_rift_event()
    assert city._rift is None
    assert rift not in city.arena.props


def test_unsealed_rift_expires():
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = _manager()
    city = MuckfordCityMenu(m)
    city.on_enter()
    city._update_rift_event()
    city._spawn_rift()
    rift = city._rift
    rift.expire_frames = 1
    rift.update(None, m)
    assert rift.expired
    city._update_rift_event()
    assert city._rift is None, "sinetöimätön repeämä sulkeutui"
    assert m.inventory.get("Vortex Crystal", 0) == 0


# ----------------------------------------------------------------------
# 4) Matalan tierin työkalut vapaita
# ----------------------------------------------------------------------

def test_low_tier_tools_equip_without_tree_nodes():
    from items.tools.weak_pickaxe import WeakPickaxe
    from items.tools.weak_lumberaxe import WeakLumberAxe
    from systems import commander_progression as prog
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills = set()   # EI puun noodeja
    hero.calculate_final_stats()
    for tool in (WeakPickaxe(), WeakLumberAxe()):
        ok, _msg = hero.can_equip_item_to_slot("main_hand", tool) \
            if isinstance(hero.can_equip_item_to_slot("main_hand", tool),
                          tuple) else (hero.can_equip_item_to_slot(
                              "main_hand", tool), "")
        assert ok, f"{tool.name} käy käteen ilman noodeja"
    # Tier 1 -työkalu läpäisee polkuportin heti (taso 1)
    ok, req = prog.tool_allowed(m, hero, WeakLumberAxe(), "forestry",
                                "forestry_level_required")
    assert ok, "tier 1 -kirves ei vaadi polkutasoja"
