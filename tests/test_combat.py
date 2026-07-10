# tests/test_combat.py
"""
Taistelu- ja AI-testit: yksiköt liikkuvat, hyökkäävät, tekevät vahinkoa
ja taistelu päättyy. Nämä ajavat oikeaa pelilogiikkaa headless-tilassa.
"""
from settings import PLAYER_TEAM, ENEMY_TEAM
from conftest import run_duel


def test_melee_duel_ends(manager):
    from units.human import Human
    from units.goblin import Goblin
    a = Human("Hero", 300, 500, PLAYER_TEAM)
    b = Goblin("Gob", 800, 500, ENEMY_TEAM)
    result = run_duel(manager, a, b)
    assert result["damaged"], "kumpikaan ei tehnyt vahinkoa"
    assert result["ended"], "taistelu ei paattynyt 60 sekunnissa"


def test_fists_hit_both_directions(manager):
    """Regressiotesti: oletus-swing-hitboxin pitää osua myös vasemmalle."""
    from units.human import Human
    a = Human("Oikea", 500, 500, PLAYER_TEAM)   # kohde vasemmalla
    b = Human("Vasen", 460, 500, ENEMY_TEAM)    # nyrkkien kantaman (45px) sisalla
    manager.match_in_progress = True
    manager.all_units.add(a, b)
    hp0 = b.current_hp

    hit = False
    for _ in range(300):
        a.attack_cooldown = 0
        a.current_stamina = a.max_stamina
        a.perform_attack(b, manager=manager)
        if b.current_hp < hp0:
            hit = True
            break
        b.current_hp = hp0
    assert hit, "hyokkays vasemmalle ei osunut (swing rect -regressio)"


def test_bow_deals_damage(manager):
    """Regressiotesti: legacy-jousi (create_arrow) ei saa kaatua."""
    from units.human import Human
    from units.orc import Orc
    from items.bows.rat_bow import RatPoisonBow
    a = Human("Archer", 300, 500, PLAYER_TEAM)
    a.equipment["main_hand"] = RatPoisonBow()
    a.calculate_final_stats()
    b = Orc("Foe", 800, 500, ENEMY_TEAM)
    result = run_duel(manager, a, b, max_frames=1800)
    assert result["damaged"], "jousi ei tehnyt vahinkoa"


def test_crossbow_fires(manager):
    """Regressiotesti: varsijousen lataus ei saa jaada ikuiseen looppiin."""
    from units.human import Human
    from units.orc import Orc
    from items.crossbows.weak_crossbow import WeakCrossbow
    a = Human("Xbow", 300, 500, PLAYER_TEAM)
    a.equipment["main_hand"] = WeakCrossbow()
    a.calculate_final_stats()
    b = Orc("Foe", 800, 500, ENEMY_TEAM)
    result = run_duel(manager, a, b, max_frames=3600)
    assert result["damaged"], "varsijousi ei ampunut"


def test_crow_attacks(manager):
    """Regressiotesti: BirdAI:n syoksy ei saa peruuntua joka frame."""
    from units.human import Human
    from units.corrupted_crow import CorruptedCrow
    a = Human("Hero", 300, 500, PLAYER_TEAM)
    b = CorruptedCrow("Crow", 800, 500, ENEMY_TEAM)
    result = run_duel(manager, a, b, max_frames=3600)
    assert result["damaged"], "varis ei tehnyt vahinkoa 60 sekunnissa"


def test_beam_spells_dont_crash(manager):
    """Regressiotesti: SunRay/LifeDrain VFX:n update(obstacles=...) toimii."""
    from units.human import Human
    from units.orc import Orc
    from spells.lvl_2.life_drain import LifeDrain
    a = Human("Mage", 300, 500, PLAYER_TEAM)
    a.spell_slots_unlocked = {1, 2, 3}
    a.max_spell_tier = 99
    a.equipment["spell1"] = LifeDrain()
    b = Orc("Foe", 600, 500, ENEMY_TEAM)

    manager.match_in_progress = True
    manager.all_units.add(a, b)
    cast = False
    for _ in range(900):
        a.current_mana = 500
        for u in (a, b):
            if not u.is_dead:
                u.run_combat_ai(manager.all_units, None, manager=manager)
                u.update(None, manager=manager)
        manager.vfx.update(obstacles=None)  # kaatui ennen korjausta
        if a.spell_cooldowns.get("spell1", 0) > 0:
            cast = True
        if b.is_dead:
            break
    assert cast, "loitsua ei koskaan castattu"


def test_stamina_never_negative(manager):
    from units.human import Human
    from units.orc import Orc
    a = Human("Hero", 300, 500, PLAYER_TEAM)
    b = Orc("Foe", 500, 500, ENEMY_TEAM)
    manager.match_in_progress = True
    manager.all_units.add(a, b)
    for _ in range(1200):
        for u in (a, b):
            if not u.is_dead:
                u.run_combat_ai(manager.all_units, None, manager=manager)
                u.update(None, manager=manager)
        manager.vfx.update(obstacles=None)
        assert a.current_stamina >= 0, "stamina meni negatiiviseksi"
        assert b.current_stamina >= 0, "stamina meni negatiiviseksi"
