# systems/faction_reputation.py
"""Paikkakohtainen maine ja sen vaikutus hintoihin.

Maine on ERI eri paikkojen/kiltojen kanssa (manager.reputations[faction],
tallentuu saveen). Kanta-asiakkuus laskee hintoja: tuntemattomalta
peritään pieni muukalaislisä, ja vakioasiakas saa alennusta.

    rep <= 0    -> x1.15  (muukalaislisä)
    rep 30      -> x1.00  (tuttu naama)
    rep >= 70   -> x0.80  (kanta-asiakas, katto)
"""

from __future__ import annotations

STRANGER_MULT = 1.15
FLOOR_MULT = 0.80
REP_SLOPE = 0.005  # -0.5 % per mainepiste
REP_PER_PURCHASE = 1


def get_faction_rep(manager, faction: str) -> int:
    getter = getattr(manager, "get_faction_rep", None)
    if callable(getter):
        return int(getter(faction))
    return int(getattr(manager, "reputations", {}).get(faction, 0))


def price_multiplier(rep: int) -> float:
    # Pyöristys 4 desimaaliin: 1.15 - 0.005*30 olisi muuten 0.9999999...
    mult = STRANGER_MULT - REP_SLOPE * int(rep)
    return round(max(FLOOR_MULT, min(STRANGER_MULT, mult)), 4)


def shop_price(base_price: int, rep: int) -> int:
    """Lopullinen hinta maineella - aina vähintään 1."""
    return max(1, int(round(int(base_price) * price_multiplier(rep))))


def discount_percent(rep: int) -> int:
    """UI:lle: +15 = muukalaislisä, -20 = kanta-asiakasalennus."""
    return int(round((price_multiplier(rep) - 1.0) * 100))


def on_purchase(manager, faction: str) -> None:
    """Jokainen ostos kasvattaa mainetta TÄMÄN liikkeen faktion kanssa."""
    modify = getattr(manager, "modify_faction_rep", None)
    if callable(modify):
        modify(faction, REP_PER_PURCHASE)
    else:
        reps = getattr(manager, "reputations", None)
        if isinstance(reps, dict):
            reps[faction] = int(reps.get(faction, 0)) + REP_PER_PURCHASE
