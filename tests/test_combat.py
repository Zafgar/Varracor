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


def test_melee_hit_staggers_bow_draw(manager):
    """Melee-osuma keskeyttää jousen jännityksen: lataus nollautuu ja
    tulee pidempi horjahdus. Steady Draw -skill estää tämän."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow
    from items.swords.weak_sword import WeakSword

    archer = Human("Archer", 500, 500, ENEMY_TEAM)
    bow = WeakBow()
    archer.equipment["main_hand"] = bow
    archer.calculate_final_stats()

    attacker = Human("Bruiser", 460, 500, PLAYER_TEAM)
    attacker.equipment["main_hand"] = WeakSword()
    attacker.calculate_final_stats()
    manager.all_units.add(archer, attacker)

    # Jännitä jousta
    for _ in range(20):
        bow.update_charge(archer, manager)
    assert bow.charge_time > 0
    assert archer.is_charging

    # Melee-osuma -> stagger
    archer.stun_immunity = 0
    ok = attacker.perform_attack(archer, manager=manager)
    assert ok, "hyokkays ei osunut"
    assert bow.charge_time == 0, "lataus ei nollautunut"
    assert archer.stun_timer >= 25, "stagger-stun puuttuu"

    # Steady Draw estää
    archer.current_hp = archer.max_hp
    archer.is_dead = False
    archer.stun_timer = 0
    archer.has_steady_draw = True
    for _ in range(20):
        bow.update_charge(archer, manager)
    attacker.attack_cooldown = 0
    attacker.current_stamina = attacker.max_stamina
    archer.stun_immunity = 0
    attacker.perform_attack(archer, manager=manager)
    assert bow.charge_time > 0, "steady_draw ei suojannut latausta"


def test_bow_cannot_block(manager):
    """Blockaus ei onnistu jousi kädessä (vaatii melee-aseen tai kilven)."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow
    from items.swords.weak_sword import WeakSword

    u = Human("Archer", 0, 0, PLAYER_TEAM)
    u.equipment["main_hand"] = WeakBow()
    u.calculate_final_stats()
    u.set_blocking(True)
    assert u.is_blocking is False, "jousella ei saa voida blokata"

    u.equipment["main_hand"] = WeakSword()
    u.calculate_final_stats()
    u.set_blocking(True)
    assert u.is_blocking is True, "miekalla blockin pitaa toimia"


def test_bow_draw_drains_stamina(manager):
    """Jännitys kuluttaa staminaa selvästi; Steady Draw puolittaa."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow

    u = Human("Archer", 0, 0, PLAYER_TEAM)
    bow = WeakBow()
    u.equipment["main_hand"] = bow
    u.calculate_final_stats()

    s0 = u.current_stamina
    for _ in range(60):
        bow.update_charge(u, manager)
    normal_cost = s0 - u.current_stamina
    assert normal_cost > 20, f"jannitys liian halpaa: {normal_cost}"

    u.current_stamina = s0
    u.has_steady_draw = True
    bow.charge_time = 0
    for _ in range(60):
        bow.update_charge(u, manager)
    skilled_cost = s0 - u.current_stamina
    assert skilled_cost < normal_cost * 0.6, (skilled_cost, normal_cost)


def test_ai_bow_respects_stamina_gate(manager):
    """AI ei aloita jousen jännitystä ellei stamina riitä täyteen vetoon."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow

    a = Human("Archer", 300, 500, PLAYER_TEAM)
    bow = WeakBow()
    a.equipment["main_hand"] = bow
    a.calculate_final_stats()
    b = Human("Foe", 480, 500, ENEMY_TEAM)  # kantaman sisällä
    manager.match_in_progress = True
    manager.all_units.add(a, b)

    a.current_stamina = 5  # aivan liian vähän täyteen vetoon
    for _ in range(30):
        a.run_combat_ai(manager.all_units, None, manager=manager)
        # ei saa jäädä charging-tilaan
        assert a.ai_controller.charge_timer == 0, "aloitti vedon ilman staminaa"
        a.current_stamina = 5


def test_orc_rage(manager):
    """Orc raivostuu alle 40% HP:lla: +STR, ei pakene."""
    from units.orc import Orc
    from units.human import Human

    orc = Orc("Grok", 300, 500, ENEMY_TEAM)
    foe = Human("Hero", 400, 500, PLAYER_TEAM)
    manager.match_in_progress = True
    manager.all_units.add(orc, foe)

    str0 = orc.strength
    orc.current_hp = orc.max_hp * 0.3
    orc.run_combat_ai(manager.all_units, None, manager=manager)
    assert orc.ai_controller.enraged is True
    assert orc.strength == str0 + 4
    assert orc.ai_controller.no_retreat is True


def test_ranged_keeps_backline_distance(manager):
    """Jousimies peruuttaa kun kohde tulee liian lähelle (backline)."""
    from units.human import Human
    from items.bows.weak_bow import WeakBow

    a = Human("Archer", 500, 500, PLAYER_TEAM)
    a.equipment["main_hand"] = WeakBow()
    a.calculate_final_stats()
    b = Human("Melee", 590, 500, ENEMY_TEAM)  # 90px: alle 40% kantamasta, yli panic-rajan
    manager.match_in_progress = True
    manager.all_units.add(a, b)

    x0 = a.rect.centerx
    for _ in range(40):
        a.run_combat_ai(manager.all_units, None, manager=manager)
        a.update(None, manager=manager)
        b.rect.centerx = a.rect.centerx + 90  # pysy iholla
    assert a.rect.centerx < x0, "jousimies ei peraantynyt"
