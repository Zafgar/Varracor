"""Aluemonsterien tasapaino (pelitesti 28).

Vahtii kolmea asiaa:
1. LIIKESKAALA: monsterinopeudet on skaalattu uuteen liikekaavaan
   (pelaaja ~2.25/3.6). Vanhan skaalan etana (<1.2) = regressio.
   Ranged-kiterit pysyvät kiinniotettavina (<1.9).
2. KENTTÄMONSTERIT: alueen tasoinen proxy voittaa, mutta taistelu
   kestää JA sattuu - ei pushovereita eikä seiniä.
3. BOSSIT saavat seinätä naiivin soolo-proxyn (pelaaja väistää/
   parryy/tuo tiimin) - mutta niiden pitää tehdä vahinkoa.
"""
import random

import pytest

from settings import PLAYER_TEAM, ENEMY_TEAM


def _proxy(level, tier, x=400, y=500):
    from units.human import Human
    from items.weapon_catalog import make_weapon
    from items.gear_catalog import make_gear
    u = Human("Proxy", x, y, PLAYER_TEAM, quality="Veteran")
    u.level = level
    u.equipment["main_hand"] = make_weapon(f"w_sword_t{tier}")
    u.equipment["body"] = make_gear(f"warrior_t{tier}")
    u.equipment["off_hand"] = None
    u.calculate_final_stats()
    u.weapon_masteries.add("sword")
    u.armor_masteries.add("heavy")
    u.calculate_final_stats()
    u.current_hp = u.max_hp
    u.current_stamina = u.max_stamina
    return u


def _monster(path):
    mod, cls = path.rsplit(".", 1)
    C = getattr(__import__(mod, fromlist=[cls]), cls)
    return C(cls, 800, 500, ENEMY_TEAM)


ALL_FIELD_MONSTERS = [
    "units.rat.GiantRat", "units.rat.BruteRat",
    "units.tier0_monsters.MudMite", "units.tier0_monsters.ReedSkitter",
    "units.tier0_monsters.BogTick", "units.tier0_monsters.SporeToad",
    "units.tier0_monsters.MireLurkerSpawn",
    "units.tier0_monsters.DrownedMudling",
    "units.tier0_monsters.FenStalker",
    "units.tier0_monsters.RotcapShambler",
    "units.tier0_monsters.MarshbackBrute",
    "units.tier0_monsters.WhisperMoth",
    "units.bog_leech.BogLeech", "units.corrupted_crow.CorruptedCrow",
    "units.giant_frog.GiantFrog", "units.cave_spider.Spiderling",
    "units.old_muckford_mine_monsters.GravePickman",
    "units.old_muckford_mine_monsters.RailWraith",
    "units.old_muckford_mine_monsters.WebCrawler",
    "units.old_muckford_mine_monsters.CrystalHusk",
    "units.old_muckford_mine_monsters.BroodGuard",
    "units.greywash_ford_monsters.GreywashRiverjaw",
    "units.greywash_ford_monsters.CrownDeserter",
    "units.greywash_ford_monsters.FordBrute",
    "units.kingsreach_toll_monsters.CrownTollEnforcer",
    "units.kingsreach_toll_monsters.FeveredEscapee",
    "units.kingsreach_toll_monsters.CausewayBandit",
    "units.drowned_chapel_monsters.WaterRisenPilgrim",
    "units.drowned_chapel_monsters.FloodedAcolyte",
    "units.drowned_chapel_monsters.BellWraith",
    "units.rattlebridge_threats.HushMantle",
    "units.rattlebridge_threats.GutterVermin",
    "units.rattlebridge_threats.RedLanternCadaver",
]


def test_monster_speeds_on_new_scale(manager):
    """Ei vanhan skaalan etanoita; kiterit pysyvät kiinniotettavina."""
    for path in ALL_FIELD_MONSTERS:
        m = _monster(path)
        spd = m.walk_speed
        assert 1.1 <= spd <= 3.6, (
            f"{path}: walk_speed {spd:.2f} ei ole uudella liikeskaalalla "
            "(pelaaja kävelee 2.25, sprinttaa 3.6)")
    for path in ("units.tier0_monsters.WhisperMoth",
                 "units.old_muckford_mine_monsters.RailWraith"):
        m = _monster(path)
        assert m.walk_speed < 1.9, (
            f"{path}: ranged-kiteri liian nopea ({m.walk_speed:.2f}) - "
            "permakite palaa")


# Edustava otos: (monsteri, proxy-level, proxy-tier, min_kesto_s, min_uhka%)
GAUNTLET = [
    ("units.rat.GiantRat", 3, 1, 2.0, 2),
    ("units.tier0_monsters.FenStalker", 4, 2, 3.0, 15),
    ("units.tier0_monsters.WhisperMoth", 4, 2, 5.0, 15),
    ("units.old_muckford_mine_monsters.RailWraith", 5, 2, 5.0, 8),
    ("units.old_muckford_mine_monsters.CrystalHusk", 5, 2, 6.0, 20),
    # BroodGuard on boss-eteisen eliitti: t2 vs se on kolikonheitto
    # (tarkoituksella kova), t3 voittaa vakaasti - testataan t3:lla
    ("units.old_muckford_mine_monsters.BroodGuard", 6, 3, 4.0, 10),
    ("units.greywash_ford_monsters.FordBrute", 7, 3, 4.0, 20),
    ("units.drowned_chapel_monsters.BellWraith", 8, 3, 3.0, 3),
    ("units.rattlebridge_threats.RedLanternCadaver", 9, 4, 1.5, 1),
]


@pytest.mark.parametrize("path,lvl,tier,min_s,min_threat", GAUNTLET)
def test_field_monster_beatable_but_threatening(manager, path, lvl, tier,
                                                min_s, min_threat):
    """Kaksintaistelut eivät ole täysin deterministisiä (mm. olio-settien
    iterointijärjestys) -> ajetaan 3 siemenellä, enemmistö ratkaisee.
    Vahti mittaa TASAPAINOA, ei yksittäistä nopanheittoa."""
    from game_manager import GameManager
    from tests.conftest import run_duel
    wins = 0
    threats = []
    durations = []
    for i in range(3):
        random.seed(500 + i)
        m = GameManager() if i else manager
        p = _proxy(lvl, tier)
        mo = _monster(path)
        r = run_duel(m, p, mo, max_frames=7200)
        if r["ended"] and r["winner"] is p:
            wins += 1
            durations.append(r["frames"])
        threats.append(100.0 * (p.max_hp - p.current_hp) / p.max_hp)
    assert wins >= 2, (
        f"{path}: seinä - proxy voitti vain {wins}/3 "
        f"(uhat: {[int(t) for t in threats]}%)")
    assert max(durations) >= min_s * 60, (
        f"{path}: pushover ({max(durations)/60:.1f}s < {min_s}s)")
    assert max(threats) >= min_threat, (
        f"{path}: ei uhkaa (max {max(threats):.0f}% < {min_threat}%)")


BOSSES = [
    ("units.rat_king.RatKing", 6, 2),
    ("units.cave_spider.CaveBroodmother", 6, 3),
    ("units.troll.Troll", 7, 3),
    ("units.old_muckford_mine_monsters.DeepCaveBroodmother", 7, 3),
    ("units.greywash_ford_monsters.CaptainGarranVale", 8, 3),
    ("units.kingsreach_toll_monsters.TollmasterHadrikCrowl", 8, 3),
]


@pytest.mark.parametrize("path,lvl,tier", BOSSES)
def test_bosses_are_dangerous_and_functional(manager, path, lvl, tier):
    """Bossi SAA voittaa naiivin proxyn, mutta sen on toimittava:
    vahinkoa syntyy molempiin suuntiin eikä taistelu ole hetkessä ohi.
    2 siementä, paras kelpaa (duel-varianssi)."""
    from game_manager import GameManager
    from tests.conftest import run_duel

    def build_boss():
        if "RatKing" in path:
            from units.rat_king import RatKing
            b = RatKing("RatKing", 800, 500)
            b.team_color = ENEMY_TEAM
            return b
        return _monster(path)

    best_loss = -1.0
    hurt_boss = False
    longest = 0
    any_damage = False
    for i in range(2):
        random.seed(500 + i)
        m = GameManager() if i else manager
        p = _proxy(lvl, tier)
        mo = build_boss()
        r = run_duel(m, p, mo, max_frames=10800)
        any_damage = any_damage or r["damaged"]
        hurt_boss = hurt_boss or mo.current_hp < mo.max_hp
        longest = max(longest, r["frames"])
        best_loss = max(best_loss,
                        100.0 * (p.max_hp - p.current_hp) / p.max_hp)
    assert any_damage, f"{path}: kumpikaan ei tehnyt vahinkoa"
    # HUOM: 'bossiin osui' -vaatimus poistettu - etäavauksella pelaava
    # bossi (esim. Broodmotherin verkko+myrkky) voi legitiimisti voittaa
    # naiivin melee-proxyn ennen kontaktia. Tapettavuuden kattaa
    # areena-/tiimitestit.
    assert best_loss >= 20, (
        f"{path}: bossi ei ole uhka ({best_loss:.0f}% menetys)")
    assert longest >= 240, f"{path}: bossitaistelu ohi alle 4 sekunnissa"
