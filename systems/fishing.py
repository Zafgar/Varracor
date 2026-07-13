# systems/fishing.py
"""Kalastus: odota nykäisyä, iske E oikealla hetkellä.

Kalat ovat materiaaleja (myydään markkinoilla, keitetään keittiössä).
Commander-puun Angler-taidot lyhentävät odotusta ja pidentävät
tartuntaikkunaa / parantavat harvinaisten kalojen mahdollisuutta.
"""

from __future__ import annotations

import random

# Suokalat: paino = yleisyys arvonnassa, price -> MARKET_PRICES sell
FISH_SPECIES = (
    {"name": "Mudfin", "weight": 46, "price": 3},
    {"name": "Bog Perch", "weight": 28, "price": 5},
    {"name": "Rat-tail Eel", "weight": 16, "price": 9},
    {"name": "Whisker Catfish", "weight": 8, "price": 14},
    {"name": "Marsh Pike", "weight": 2, "price": 26},
)

WAIT_MIN, WAIT_MAX = 140, 380      # framea nykäisyyn
BITE_WINDOW = 42                   # framea aikaa iskeä
SKILL_WAIT_CUT = 0.15              # -15 % odotus / Angler-taso
SKILL_WINDOW_BONUS = 14            # +framea ikkunaan / taso
SKILL_RARE_SHIFT = 0.35            # harvinaispainojen kerroin / taso


def fishing_skill(unit) -> int:
    return int(getattr(unit, "fishing", 0))


def has_rod(manager) -> bool:
    """Vapa kädessä TAI repussa riittää."""
    hero = getattr(manager, "player_character", None)
    if hero is not None:
        main = getattr(hero, "equipment", {}).get("main_hand")
        if str(getattr(main, "tool_type", "")) == "fishing":
            return True
    for item in getattr(manager, "equipment_bag", []):
        if str(getattr(item, "tool_type", "")) == "fishing":
            return True
    return False


def roll_fish(rng: random.Random, skill: int = 0) -> dict:
    """Arpoo saaliin; Angler kasvattaa harvinaisten painoa."""
    bag = []
    for i, fish in enumerate(FISH_SPECIES):
        weight = fish["weight"]
        if skill > 0 and i >= 2:
            weight = int(round(weight * (1.0 + SKILL_RARE_SHIFT * skill)))
        bag.extend([fish] * max(1, weight))
    return rng.choice(bag)


class FishingSession:
    """Tilakone: WAITING -> BITE -> (hook) CAUGHT / (myöhässä) WAITING."""

    def __init__(self, skill: int = 0, rng: random.Random | None = None):
        self.rng = rng or random.Random()
        self.skill = int(skill)
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
            self.timer = BITE_WINDOW + SKILL_WINDOW_BONUS * self.skill
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
            fish = roll_fish(self.rng, self.skill)
            self._start_wait()
            return fish
        # Liian aikainen isku säikäyttää
        self._start_wait()
        return None
