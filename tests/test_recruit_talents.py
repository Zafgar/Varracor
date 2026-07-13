# tests/test_recruit_talents.py
"""
Uniikit rekryt: synnynnäiset talentit (systems/talents.py).
- roll_talents arpoo 1-3 uniikkia talenttia + mahdollisen heikkouden
- apply_talents leipoo perusstatit base_attributes-sanakirjaan,
  erikoisefektit talent_effects-sanakirjaan ja affinityt asegruppiin
- damage_reduction/xp_mult vaikuttavat taistelussa
- varusteiden stamina-passiivi EI jyräydy (regressio)
- talenttien tarkat kuvaukset näkyvät vain insightilla (Appraiser's Eye)
- talentit säilyvät save/load-kierroksen yli
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems.talents import (TALENTS, QUIRKS, AFFINITY_BONUS,
                             roll_talents, apply_talents)


def _fresh_human(name="Testi"):
    from units.human import Human
    from settings import GREEN
    return Human(name, 0, 0, GREEN, "Common")


def test_roll_talents_counts_and_uniqueness():
    rng = random.Random(42)
    for _ in range(200):
        talents, quirk = roll_talents(rng)
        assert 1 <= len(talents) <= 3
        assert len(set(talents)) == len(talents), "ei duplikaatteja"
        for t in talents:
            assert t in TALENTS
        if quirk is not None:
            assert quirk in QUIRKS


def test_apply_base_stat_talent():
    u = _fresh_human()
    base_str = u.strength
    cost = apply_talents(u, ["Strong"])
    assert u.strength == base_str + 2
    assert "Strong" in u.traits
    assert any(d.startswith("Strong:") for d in u.talent_details)
    assert cost == TALENTS["Strong"]["cost"]
    # base_attributes-reitti -> säilyy calculate_final_statsin yli
    u.calculate_final_stats()
    assert u.strength == base_str + 2


def test_apply_effect_talents_stamina_crit_defense():
    u = _fresh_human()
    base_stam = u.max_stamina
    base_def = u.defense
    base_crit = u.crit_chance
    apply_talents(u, ["Tireless", "Iron Hide", "Eagle Eye"])
    assert u.max_stamina == base_stam + 20
    assert u.defense == base_def + 1
    assert abs(u.crit_chance - (base_crit + 0.04)) < 1e-9


def test_affinity_talent_multiplies_weapon_group():
    u = _fresh_human()
    before = u.weapon_affinities.get("sword", 1.0)
    apply_talents(u, ["Gifted: Sword"])
    assert abs(u.weapon_affinities["sword"] - before * AFFINITY_BONUS) < 1e-9


def test_damage_reduction_reduces_incoming_damage():
    tough = _fresh_human("Tough")
    plain = _fresh_human("Plain")
    apply_talents(tough, ["Thick Skin"])
    tough.defense = plain.defense = 0  # eristä pelkkä vähennys
    hp_t, hp_p = tough.current_hp, plain.current_hp
    tough.take_damage(100)
    plain.take_damage(100)
    assert (hp_t - tough.current_hp) < (hp_p - plain.current_hp)


def test_xp_mult_scales_add_xp():
    fast = _fresh_human("Fast")
    apply_talents(fast, ["Quick Learner"])
    slow = _fresh_human("Slow")
    apply_talents(slow, [], quirk="Slow Learner")
    fast.xp = slow.xp = 0
    fast.add_xp(100)
    slow.add_xp(100)
    assert fast.xp == 120
    assert slow.xp == 85


def test_speed_mult_talent_raises_walk_speed():
    quick = _fresh_human("Quick")
    base = quick.walk_speed
    apply_talents(quick, ["Fleet-Footed"])
    assert quick.walk_speed > base


def test_item_passive_stamina_bonus_not_overwritten():
    """Regressio: max_stamina lasketaan uudelleen calculate_final_statsissa,
    varusteiden stamina-passiivin pitää silti summautua mukaan."""
    u = _fresh_human()
    base = u.max_stamina

    class _Ring:
        name = "Test Ring"
        passive_bonuses = {"stamina": 30}
    u.equipment["off_hand"] = _Ring()
    u.calculate_final_stats()
    assert u.max_stamina == base + 30


def test_quirk_lowers_cost_and_talent_floor_cost():
    u = _fresh_human()
    mod = apply_talents(u, ["Strong"], quirk="Old Wound")
    assert mod == TALENTS["Strong"]["cost"] + QUIRKS["Old Wound"]["cost"]
    assert "Old Wound" in u.traits


def test_generate_recruits_are_unique_and_priced():
    import main  # noqa: F401  (asentaa runtime-laajennukset)
    from game_manager import GameManager
    m = GameManager()
    assert len(m.recruit_options) == 6
    for u in m.recruit_options:
        assert u.traits, "jokaisella rekryllä on vähintään yksi talentti"
        assert u.talent_details, "kuvaukset insight-näkymää varten"
        assert u.cost >= 15
        assert u.current_hp == u.max_hp


def test_info_card_draws_with_and_without_insight():
    u = _fresh_human()
    apply_talents(u, ["Strong", "Thick Skin"])
    surf = pygame.Surface((400, 500))
    u.draw_info_card(surf, 10, 10, 290, 360, show_talent_details=False)
    u.draw_info_card(surf, 10, 10, 290, 360, show_talent_details=True,
                     show_cost=True)


def test_commander_insight_skill_grants_insight():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    hero = m.player_character
    hero.unlocked_skills.add("insight_1")
    hero.calculate_final_stats()
    assert getattr(hero, "insight", 0) >= 1


def test_talents_survive_save_load(tmp_path, monkeypatch):
    import main  # noqa: F401
    from game_manager import GameManager
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE",
                        str(tmp_path / "talent_save.json"))
    m = GameManager()
    m.gold = 5000
    # Pakota tunnetut talentit ensimmäiselle rekrylle vertailua varten
    rec = m.recruit_options[0]
    rec.traits = []
    rec.talent_details = []
    rec.talent_effects = {}
    apply_talents(rec, ["Tireless", "Gifted: Axe"], quirk="Drunkard")
    assert m.hire_recruit(0)

    assert save_manager.save_game(m)

    m2 = GameManager()
    assert save_manager.load_game(m2)
    loaded = next(u for u in m2.my_team if u.name == rec.name)
    assert "Tireless" in loaded.traits
    assert "Gifted: Axe" in loaded.traits
    assert "Drunkard" in loaded.traits
    assert loaded.talent_effects.get("max_stamina") == 20 - 15
    assert any(d.startswith("Tireless:") for d in loaded.talent_details)
    assert abs(loaded.weapon_affinities.get("axe", 0)
               - rec.weapon_affinities["axe"]) < 1e-9
    assert loaded.max_stamina == rec.max_stamina
