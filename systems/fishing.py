# systems/fishing.py
"""Kalastus: odota nykäisyä, iske E oikealla hetkellä.

Kalat ovat materiaaleja (myydään markkinoilla, keitetään keittiössä).
Commander-puun Angler-taidot lyhentävät odotusta ja pidentävät
tartuntaikkunaa / parantavat harvinaisten kalojen mahdollisuutta.
"""

from __future__ import annotations

import random

# Kalat tiereittäin: vavan tier avaa uudet kalat, paino = yleisyys
# arvonnassa, price -> MARKET_PRICES sell, xp -> kalastusskillin nousu
FISH_SPECIES = (
    {"name": "Mudfin", "tier": 1, "weight": 46, "price": 3, "xp": 4},
    {"name": "Bog Perch", "tier": 1, "weight": 28, "price": 5, "xp": 6},
    {"name": "Rat-tail Eel", "tier": 2, "weight": 16, "price": 9, "xp": 10},
    {"name": "Whisker Catfish", "tier": 2, "weight": 8, "price": 14, "xp": 14},
    {"name": "Bronze Bream", "tier": 3, "weight": 7, "price": 20, "xp": 18},
    {"name": "Marsh Pike", "tier": 3, "weight": 4, "price": 26, "xp": 24},
    {"name": "Duskgill", "tier": 4, "weight": 4, "price": 42, "xp": 32},
    {"name": "Silver Eelmother", "tier": 4, "weight": 2, "price": 60, "xp": 44},
    {"name": "Vortex Koi", "tier": 5, "weight": 2, "price": 120, "xp": 70},
    {"name": "Blind Abyss Sturgeon", "tier": 5, "weight": 1, "price": 150,
     "xp": 90},
)

MAX_LEVEL = 30

WAIT_MIN, WAIT_MAX = 140, 380      # framea nykäisyyn
BITE_WINDOW = 42                   # framea aikaa iskeä
SKILL_WAIT_CUT = 0.15              # -15 % odotus / tehopiste
SKILL_WINDOW_BONUS = 14            # +framea ikkunaan / tehopiste
SKILL_RARE_SHIFT = 0.35            # harvinaispainojen kerroin / tehopiste

# Muut saaliit: pieni mahdollisuus että koukkuun tarttuu jotain muuta.
# Sharp Hook -milestone (Path of the Line 10) tuplaa aarremahdollisuuden.
TREASURE_CHANCE = 0.08
TREASURES = (
    {"name": "Waterlogged Boot", "weight": 40, "price": 1, "xp": 3,
     "treasure": True},
    {"name": "Snagged Scrap", "weight": 26, "price": 2, "xp": 3,
     "treasure": True},
    {"name": "Old Message Bottle", "weight": 18, "price": 6, "xp": 8,
     "treasure": True},
    {"name": "Rusted Ring", "weight": 12, "price": 12, "xp": 10,
     "treasure": True},
    {"name": "Abyssal Droplet", "weight": 4, "price": 40, "xp": 20,
     "treasure": True},
)


# --------------------------------------------------------------- progressio
# Kalastustaso elää Commander Paths -järjestelmässä (Path of the Line):
# sama {level, xp} -dict, tallentuu saveen, milestone-perkit sieltä.

def get_progress(manager) -> dict:
    from systems import commander_progression as prog
    return prog.get_path(manager, "fishing")


def grant_catch_xp(manager, fish: dict) -> bool:
    """Lisää saaliin XP:n Path of the Lineen. True jos taso nousi."""
    from systems import commander_progression as prog
    if prog.get_path(manager, "fishing")["level"] >= MAX_LEVEL:
        return False
    return prog.grant_xp(manager, "fishing", int(fish.get("xp", 4)))


def treasure_chance(manager) -> float:
    from systems import commander_progression as prog
    chance = TREASURE_CHANCE
    if prog.has_perk(manager, "fishing", "sharp_hook"):
        chance *= 2
    return chance


def double_catch(manager) -> bool:
    from systems import commander_progression as prog
    return prog.has_perk(manager, "fishing", "double_catch")


def roll_treasure(rng: random.Random) -> dict:
    bag = []
    for t in TREASURES:
        bag.extend([t] * t["weight"])
    return rng.choice(bag)


def fishing_skill(unit) -> int:
    """Commander-puun Angler-tasot (bonus opitun tason päälle)."""
    return int(getattr(unit, "fishing", 0))


def skill_power(manager) -> float:
    """Yhdistetty teho: Angler-taidot + opittu taso (1-30).
    Tasolla 30 + Angler 2: teho ~4.3 -> odotus pohjilla, leveä ikkuna."""
    hero = getattr(manager, "player_character", None)
    angler = fishing_skill(hero) if hero is not None else 0
    level = get_progress(manager)["level"]
    return angler + (level - 1) * 0.08


# --------------------------------------------------------------- vavat

def _iter_rods(manager):
    hero = getattr(manager, "player_character", None)
    if hero is not None:
        main = getattr(hero, "equipment", {}).get("main_hand")
        if str(getattr(main, "tool_type", "")) == "fishing":
            yield main
    for item in getattr(manager, "equipment_bag", []):
        if str(getattr(item, "tool_type", "")) == "fishing":
            yield item


def has_rod(manager) -> bool:
    """Vapa kädessä TAI repussa riittää."""
    return next(_iter_rods(manager), None) is not None


def best_rod(manager):
    """Paras vapa jonka kalastustaso riittää (fishing_level_required).
    Palauttaa (rod, tier) tai (None, 0). Liian vaativa vapa ei auta -
    mutta tier 1 -toimii aina jos jokin vapa löytyy."""
    level = get_progress(manager)["level"]
    usable = [r for r in _iter_rods(manager)
              if int(getattr(r, "fishing_level_required", 1)) <= level]
    if not usable:
        return None, 0
    rod = max(usable, key=lambda r: int(getattr(r, "tool_tier", 1)))
    return rod, int(getattr(rod, "tool_tier", 1))


def roll_fish(rng: random.Random, skill: float = 0, rod_tier: int = 5) -> dict:
    """Arpoo saaliin vavan tierin avaamasta poolista; taito kasvattaa
    harvinaisten (tier >= 2) painoa."""
    pool = [f for f in FISH_SPECIES if f["tier"] <= max(1, rod_tier)]
    bag = []
    for fish in pool:
        weight = fish["weight"]
        if skill > 0 and fish["tier"] >= 2:
            weight = int(round(weight * (1.0 + SKILL_RARE_SHIFT * skill)))
        bag.extend([fish] * max(1, weight))
    return rng.choice(bag)


class FishingSession:
    """Tilakone: WAITING -> BITE -> (hook) REELING -> caught/snapped.

    Väsytysvaihe (REELING): pidä E pohjassa kelataksesi - progress nousee
    mutta siima kiristyy; hellitä ja kireys laskee mutta kala karkaa
    hiljalleen. Kala tempoilee satunnaisesti (isommat rajummin). Jos
    kireys lyö kattoon, siima katkeaa. skill (Path-taso + Angler) nopeuttaa
    kelausta ja Quick Wrists -perkki pehmentää kiristymistä.
    """

    def __init__(self, skill: float = 0, rng: random.Random | None = None,
                 rod_tier: int = 1, quick_wrists: bool = False):
        self.rng = rng or random.Random()
        self.skill = float(skill)
        self.rod_tier = int(rod_tier)
        self.quick_wrists = bool(quick_wrists)
        self.state = "WAITING"
        self.escapes = 0
        self.pending_fish = None
        self.tension = 0.0     # 0-100, 100 = siima poikki
        self.progress = 0.0    # 0-100, 100 = saalis ylös
        self._start_wait()

    def _start_wait(self):
        wait = self.rng.randint(WAIT_MIN, WAIT_MAX)
        wait = int(wait * max(0.4, 1.0 - SKILL_WAIT_CUT * self.skill))
        self.timer = wait
        self.state = "WAITING"

    def update(self):
        """Kutsutaan joka frame. Palauttaa tapahtuman tai None:
        'bite' kun nykäisee, 'escaped' kun ikkuna meni ohi."""
        self.timer -= 1
        if self.state == "WAITING" and self.timer <= 0:
            self.state = "BITE"
            self.timer = int(BITE_WINDOW + SKILL_WINDOW_BONUS * self.skill)
            return "bite"
        if self.state == "BITE" and self.timer <= 0:
            self.escapes += 1
            self._start_wait()
            return "escaped"
        return None

    def hook(self):
        """E-isku nykäisyn aikana -> väsytys alkaa. Palauttaa True jos
        tartunta onnistui (REELING alkoi); None jos isku oli liian
        aikainen (kala säikähtää, odotus alkaa alusta)."""
        if self.state == "BITE":
            self.pending_fish = roll_fish(self.rng, self.skill, self.rod_tier)
            self.state = "REELING"
            self.tension = 30.0
            self.progress = 12.0
            return True
        # Liian aikainen isku säikäyttää
        self._start_wait()
        return None

    def reel(self, reeling: bool):
        """Väsytysframe. reeling=True kun E pohjassa. Palauttaa
        'caught' (saalis ylös), 'snapped' (siima poikki) tai None."""
        if self.state != "REELING":
            return None
        fish = self.pending_fish or FISH_SPECIES[0]
        fight = fish.get("tier", 1)

        if reeling:
            self.progress += 0.55 + self.skill * 0.06
            rise = 0.80 + fight * 0.25
            if self.quick_wrists:
                rise *= 0.8
            self.tension += rise
        else:
            self.tension -= 2.2
            self.progress -= 0.18

        # Kala tempoo: isommat useammin ja rajummin
        if self.rng.random() < 0.012 + fight * 0.006:
            self.tension += 6 + fight * 3 + self.rng.random() * 6

        self.tension = max(0.0, self.tension)
        self.progress = max(0.0, self.progress)

        if self.tension >= 100.0:
            self.escapes += 1
            self.pending_fish = None
            self._start_wait()
            return "snapped"
        if self.progress >= 100.0:
            fish = self.pending_fish
            self.pending_fish = None
            self._start_wait()
            self.caught = fish
            return "caught"
        return None
