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


# --------------------------------------------------------------- progressio

def xp_needed(level: int) -> int:
    """XP joka vaaditaan tasolta seuraavalle (1->2: 30 ... 29->30: 366)."""
    return 18 + level * 12


def get_progress(manager) -> dict:
    """Pysyvä kalastustaso {level, xp} (npc_state -> tallentuu saveen)."""
    state = manager.npc_state.setdefault("fishing", {})
    state.setdefault("level", 1)
    state.setdefault("xp", 0)
    return state


def grant_catch_xp(manager, fish: dict) -> bool:
    """Lisää saaliin XP:n. Palauttaa True jos taso nousi."""
    state = get_progress(manager)
    if state["level"] >= MAX_LEVEL:
        return False
    state["xp"] += int(fish.get("xp", 4))
    leveled = False
    while state["level"] < MAX_LEVEL and \
            state["xp"] >= xp_needed(state["level"]):
        state["xp"] -= xp_needed(state["level"])
        state["level"] += 1
        leveled = True
    return leveled


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
    """Tilakone: WAITING -> BITE -> (hook) CAUGHT / (myöhässä) WAITING.

    skill = yhdistetty teho (skill_power), rod_tier rajaa kalapoolin.
    """

    def __init__(self, skill: float = 0, rng: random.Random | None = None,
                 rod_tier: int = 1):
        self.rng = rng or random.Random()
        self.skill = float(skill)
        self.rod_tier = int(rod_tier)
        self.state = "WAITING"
        self.escapes = 0
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
        """E-isku. Palauttaa kalan dictin jos tartunta onnistui, muuten None
        (liian aikaisin isketty -> kala säikähtää ja odotus alkaa alusta)."""
        if self.state == "BITE":
            fish = roll_fish(self.rng, self.skill, self.rod_tier)
            self._start_wait()
            return fish
        # Liian aikainen isku säikäyttää
        self._start_wait()
        return None
