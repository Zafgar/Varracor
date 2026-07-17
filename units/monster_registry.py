# units/monster_registry.py
"""Keskitetty monster-rekisteri: YKSI nimi -> luokka -järjestelmä.

KRIITTINEN suunnitteluperiaate (pelitesti 29): monsterit eivät saa olla
sidottuja mihinkään tiettyyn karttaan tai spawn-järjestelmään. Sama olento
toimii Vortex-repeämäinvaasiossa, kryptan aalloissa, avoimen maailman
aluespawneissa ja quest-käsikirjoituksissa - kaikki luovat yksiköt tämän
rekisterin kautta samoilla säännöillä.

Aiemmin nimi->luokka-tietoa oli neljässä rinnakkaisessa paikassa:
game_manager.create_enemy_by_name (if-ketju), rift_site_menu._unit_class
(oma dict), tier0_monster_ecology (laji-dict) ja missioiden suorat importit.
Uudet monsterit lisätään VAIN tähän tiedostoon.

Roolit (role) kuvaavat taistelukäyttäytymistä spawn-suunnittelua varten:
  swarm      - halpa laumapainostaja
  skirmisher - nopea kiertelijä / sivuiskija
  ambusher   - piilossa odottava väijyttäjä
  pouncer    - loikkaava välinkuroja
  ranged     - etähyökkääjä / kiteri
  support    - myrkky/debuff-alue
  tank       - hidas raskas uhka
  shock      - rynnäkköisku (charge)
  boss       - nimetty pomovastus
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from settings import ENEMY_TEAM


@dataclass(frozen=True)
class MonsterInfo:
    name: str            # kanoninen näyttönimi (rekisteriavain)
    module: str          # moduulipolku, esim. "units.rat"
    cls: str             # luokan nimi moduulissa
    role: str            # ks. roolilista yllä
    level: int           # uhkataso (vastaa THREAT_LEVEL-skaalaa)
    aliases: Tuple[str, ...] = ()


MONSTERS: Tuple[MonsterInfo, ...] = (
    # --- Tier 0: Muckford / Whisper Marsh (koodipiirretyt) ---
    MonsterInfo("Mud Mite", "units.tier0_monsters", "MudMite", "swarm", 1),
    MonsterInfo("Reed Skitter", "units.tier0_monsters", "ReedSkitter", "skirmisher", 1),
    MonsterInfo("Bog Tick", "units.tier0_monsters", "BogTick", "ambusher", 2),
    MonsterInfo("Spore Toad", "units.tier0_monsters", "SporeToad", "support", 2),
    MonsterInfo("Mire-Lurker Spawn", "units.tier0_monsters", "MireLurkerSpawn", "pouncer", 3),
    MonsterInfo("Drowned Mudling", "units.tier0_monsters", "DrownedMudling", "swarm", 3),
    MonsterInfo("Fen Stalker", "units.tier0_monsters", "FenStalker", "ambusher", 4),
    MonsterInfo("Rotcap Shambler", "units.tier0_monsters", "RotcapShambler", "support", 4),
    MonsterInfo("Marshback Brute", "units.tier0_monsters", "MarshbackBrute", "tank", 5),
    MonsterInfo("Whisper Moth", "units.tier0_monsters", "WhisperMoth", "ranged", 5),

    # --- Old Muckford Mine ---
    MonsterInfo("Grave Pickman", "units.old_muckford_mine_monsters", "GravePickman", "swarm", 3),
    MonsterInfo("Rail Wraith", "units.old_muckford_mine_monsters", "RailWraith", "ranged", 4),
    MonsterInfo("Web Crawler", "units.old_muckford_mine_monsters", "WebCrawler", "pouncer", 4),
    MonsterInfo("Crystal Husk", "units.old_muckford_mine_monsters", "CrystalHusk", "tank", 5),
    MonsterInfo("Brood Guard", "units.old_muckford_mine_monsters", "BroodGuard", "skirmisher", 6),
    MonsterInfo("Deep Cave Broodmother", "units.old_muckford_mine_monsters",
                "DeepCaveBroodmother", "boss", 7),

    # --- Greywash Ford ---
    MonsterInfo("Greywash Riverjaw", "units.greywash_ford_monsters", "GreywashRiverjaw", "pouncer", 5),
    MonsterInfo("Crown Deserter", "units.greywash_ford_monsters", "CrownDeserter", "skirmisher", 5),
    MonsterInfo("Ford Brute", "units.greywash_ford_monsters", "FordBrute", "tank", 6),
    MonsterInfo("Captain Garran Vale", "units.greywash_ford_monsters", "CaptainGarranVale", "boss", 7),

    # --- Kingsreach Toll ---
    MonsterInfo("Crown Toll Enforcer", "units.kingsreach_toll_monsters", "CrownTollEnforcer", "skirmisher", 6),
    MonsterInfo("Fevered Escapee", "units.kingsreach_toll_monsters", "FeveredEscapee", "support", 6),
    MonsterInfo("Causeway Bandit", "units.kingsreach_toll_monsters", "CausewayBandit", "ranged", 7),
    MonsterInfo("Tollmaster Hadrik Crowl", "units.kingsreach_toll_monsters",
                "TollmasterHadrikCrowl", "boss", 8),

    # --- Drowned Chapel ---
    MonsterInfo("Water-risen Pilgrim", "units.drowned_chapel_monsters", "WaterRisenPilgrim", "swarm", 3),
    MonsterInfo("Flooded Acolyte", "units.drowned_chapel_monsters", "FloodedAcolyte", "support", 4),
    MonsterInfo("Bell Wraith", "units.drowned_chapel_monsters", "BellWraith", "ranged", 5),
    MonsterInfo("Bell-Drowned Pilgrim", "units.drowned_chapel_monsters", "BellDrownedPilgrim", "tank", 5),

    # --- Whisper Pool ---
    MonsterInfo("Whisper Pool Maw", "units.whisper_pool_boss", "WhisperPoolMaw", "boss", 5),

    # --- Klassikot: rotat, peikot, hämähäkit ---
    MonsterInfo("Giant Rat", "units.rat", "GiantRat", "swarm", 2),
    MonsterInfo("Brute Rat", "units.rat", "BruteRat", "tank", 4),
    MonsterInfo("Rat Rider", "units.rat_rider", "RatRider", "shock", 4),
    MonsterInfo("Rat King", "units.rat_king", "RatKing", "boss", 5),
    MonsterInfo("Forest Troll", "units.troll", "Troll", "boss", 6, aliases=("Troll",)),
    MonsterInfo("Spiderling", "units.cave_spider", "Spiderling", "swarm", 2),
    MonsterInfo("Cave Broodmother", "units.cave_spider", "CaveBroodmother", "boss", 5,
                aliases=("Broodmother",)),

    # --- Epäkuolleet (krypta, hautausmaa-repeämä) ---
    MonsterInfo("Skeleton", "units.undead_skeleton", "UndeadSkeleton", "swarm", 2),
    MonsterInfo("Zombie", "units.undead_zombie", "UndeadZombie", "tank", 2),
    MonsterInfo("Skeleton Archer", "units.undead_skeleton_archer", "UndeadSkeletonArcher",
                "ranged", 2, aliases=("Archer",)),

    # --- Suo ja metsä ---
    MonsterInfo("Bog Leech", "units.bog_leech", "BogLeech", "ambusher", 2),
    MonsterInfo("Giant Frog", "units.giant_frog", "GiantFrog", "pouncer", 2),
    MonsterInfo("Corrupted Crow", "units.corrupted_crow", "CorruptedCrow", "skirmisher", 2,
                aliases=("Crow",)),

    # --- Rattlebridge ---
    MonsterInfo("Hush-Mantle", "units.rattlebridge_threats", "HushMantle", "ambusher", 4,
                aliases=("Hush Mantle",)),
    MonsterInfo("Gutter Vermin", "units.rattlebridge_threats", "GutterVermin", "swarm", 3),
    MonsterInfo("Red Lantern Cadaver", "units.rattlebridge_threats", "RedLanternCadaver", "tank", 5),

    # --- Erikoisbossit ---
    MonsterInfo("Mnemonic Devourer", "units.mnemonic_devourer", "MnemonicDevourer", "boss", 7),
)


def _norm(name: str) -> str:
    return str(name).strip().lower()


_BY_KEY: Dict[str, MonsterInfo] = {}
for _info in MONSTERS:
    _BY_KEY[_norm(_info.name)] = _info
    for _alias in _info.aliases:
        _BY_KEY[_norm(_alias)] = _info


def monster_info(name: str) -> Optional[MonsterInfo]:
    """Hae monsterin tiedot nimellä tai aliaksella (case-insensitive)."""
    return _BY_KEY.get(_norm(name))


def monster_class(name: str):
    """Palauttaa monster-luokan (laiska import, ei kehäriippuvuuksia)."""
    info = monster_info(name)
    if info is None:
        raise KeyError(f"Unknown monster: {name!r}")
    module = importlib.import_module(info.module)
    return getattr(module, info.cls)


def create_monster(name: str, x: int, y: int, team_color=ENEMY_TEAM, *,
                   display_name: Optional[str] = None):
    """Luo monsterin mihin tahansa karttaan/tilaan.

    Tasoittaa konstruktorierot: osa klassikoista ei ota team_color-
    parametria (esim. RatKing) - rekisterin käyttäjän ei tarvitse tietää.
    """
    info = monster_info(name)
    if info is None:
        raise KeyError(f"Unknown monster: {name!r}")
    cls = monster_class(name)
    label = display_name or info.name
    try:
        unit = cls(label, int(x), int(y), team_color)
    except TypeError:
        unit = cls(label, int(x), int(y))
        if team_color is not None:
            unit.team_color = team_color
    return unit


def monster_names() -> List[str]:
    return [info.name for info in MONSTERS]


def monsters_by_role(role: str) -> List[MonsterInfo]:
    return [info for info in MONSTERS if info.role == role]


def monsters_for_level(min_level: int, max_level: int) -> List[MonsterInfo]:
    return [info for info in MONSTERS if min_level <= info.level <= max_level]
