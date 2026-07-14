# systems/conditions.py
"""Gladiaattorien sairaudet ja vammat (pelitesti 18).

Soturit (EI Commander - hänellä pitää pystyä pelaamaan aina) voivat
saada tiloja: flunssa, ruokamyrkytys, murtuma, väsymys, vakava haava.
- Kesto pelipäivinä; hupenee päivän vaihtuessa (tick_new_day).
- Taistelussa isot miinukset (vahinko/nopeus/stamina) - katso EFFECTS.
- Vakavimmissa tiloissa on KUOLEMANRISKI jos soturi laitetaan areenalle.
- Paraneminen: rohdot Saggan teltasta (Muckford), lepo barracksissa
  (väsymys paranee heti, muut -1 pv) tai aika.
- Uusia tiloja tulee taisteluista: kaatuminen tai pahat osumat voivat
  jättää jälkiä; arki tuo joskus flunssan/ruokamyrkytyksen.

Yksikölle: unit.conditions = [{"id": str, "days_left": int}, ...]
"""
import random

CONDITIONS = {
    "flu": {
        "name": "Flu",
        "desc": "Feverish and weak.",
        "days": 3,
        "effects": {"damage_mult": 0.85, "speed_mult": 0.90},
        "death_risk": 0.0,
        "cure": "Feverfew Tonic",
        "color": (150, 200, 120),
        "icon": "F",
    },
    "food_poisoning": {
        "name": "Food Poisoning",
        "desc": "Stomach in knots; tires fast.",
        "days": 2,
        "effects": {"damage_mult": 0.90, "stamina_mult": 0.60},
        "death_risk": 0.0,
        "cure": "Charleaf Brew",
        "color": (170, 180, 90),
        "icon": "P",
    },
    "fatigue": {
        "name": "Fatigue",
        "desc": "Exhausted from back-to-back bouts.",
        "days": 1,
        "effects": {"damage_mult": 0.92, "stamina_mult": 0.70},
        "death_risk": 0.0,
        "cure": None,   # paranee levolla
        "color": (150, 150, 170),
        "icon": "Z",
    },
    "fracture": {
        "name": "Fracture",
        "desc": "A cracked bone that needs time.",
        "days": 6,
        "effects": {"damage_mult": 0.80, "speed_mult": 0.70},
        "death_risk": 0.05,
        "cure": "Bonesetter's Splint",
        "color": (220, 170, 100),
        "icon": "X",
    },
    "severe_wound": {
        "name": "Severe Wound",
        "desc": "A deep gash that could reopen.",
        "days": 5,
        "effects": {"damage_mult": 0.85, "hp_mult": 0.70},
        "death_risk": 0.12,
        "cure": "Sagga's Poultice",
        "color": (220, 100, 90),
        "icon": "W",
    },
}

# Rohtojen hinnat Saggan teltassa (SP)
REMEDY_PRICES = {
    "flu": 15,
    "food_poisoning": 12,
    "fracture": 45,
    "severe_wound": 35,
}


def get_conditions(unit):
    if not hasattr(unit, "conditions") or unit.conditions is None:
        unit.conditions = []
    return unit.conditions


def has_condition(unit, cond_id):
    return any(c.get("id") == cond_id for c in get_conditions(unit))


def add_condition(unit, cond_id, manager=None):
    """Lisää tilan yksikölle. Commander on immuuni (pelattavuus)."""
    if cond_id not in CONDITIONS:
        return False
    if manager is not None and unit is getattr(manager,
                                               "player_character", None):
        return False
    if getattr(unit, "is_player_character", False):
        return False
    if has_condition(unit, cond_id):
        return False
    data = CONDITIONS[cond_id]
    get_conditions(unit).append({"id": cond_id, "days_left": data["days"]})
    if manager is not None:
        try:
            manager.vfx.show_damage(unit.rect.centerx, unit.rect.top - 30,
                                    f"{unit.name}: {data['name']}!",
                                    color=data["color"])
        except Exception:
            pass
    return True


def remove_condition(unit, cond_id):
    conds = get_conditions(unit)
    unit.conditions = [c for c in conds if c.get("id") != cond_id]
    return len(unit.conditions) != len(conds)


def clear_all(unit):
    unit.conditions = []


def modifiers(unit):
    """Yhdistetyt kertoimet yksikön tiloista."""
    mods = {"damage_mult": 1.0, "speed_mult": 1.0, "stamina_mult": 1.0,
            "hp_mult": 1.0}
    for c in get_conditions(unit):
        eff = CONDITIONS.get(c.get("id"), {}).get("effects", {})
        for k, v in eff.items():
            mods[k] = mods.get(k, 1.0) * v
    return mods


def death_risk(unit) -> float:
    """Kuolemanriski JOS yksikkö laitetaan areenalle tässä kunnossa."""
    risk = 0.0
    for c in get_conditions(unit):
        risk += CONDITIONS.get(c.get("id"), {}).get("death_risk", 0.0)
    return min(0.5, risk)


def describe(unit):
    """[(nimi, kuvaus, efektiteksti, väri, ikoni)] tooltippejä varten."""
    out = []
    for c in get_conditions(unit):
        data = CONDITIONS.get(c.get("id"))
        if not data:
            continue
        eff = data["effects"]
        parts = []
        if eff.get("damage_mult", 1.0) < 1.0:
            parts.append(f"-{round((1 - eff['damage_mult']) * 100)}% damage")
        if eff.get("speed_mult", 1.0) < 1.0:
            parts.append(f"-{round((1 - eff['speed_mult']) * 100)}% speed")
        if eff.get("stamina_mult", 1.0) < 1.0:
            parts.append(f"-{round((1 - eff['stamina_mult']) * 100)}% stamina")
        if eff.get("hp_mult", 1.0) < 1.0:
            parts.append(f"-{round((1 - eff['hp_mult']) * 100)}% max HP")
        if data.get("death_risk"):
            parts.append(f"{round(data['death_risk'] * 100)}% DEATH RISK "
                         "if fielded")
        eff_txt = ", ".join(parts)
        out.append((f"{data['name']} ({c.get('days_left', '?')}d)",
                    data["desc"], eff_txt, data["color"], data["icon"]))
    return out


# ----------------------------------------------------------------------
# Elinkaari
# ----------------------------------------------------------------------

def tick_new_day(manager, days=1):
    """Päivän vaihtuessa tilat hupenevat. Kutsu kerran per uusi päivä."""
    for u in _roster(manager):
        conds = get_conditions(u)
        if not conds:
            continue
        for c in conds:
            c["days_left"] = int(c.get("days_left", 1)) - int(days)
        healed = [c for c in conds if c["days_left"] <= 0]
        u.conditions = [c for c in conds if c["days_left"] > 0]
        for c in healed:
            data = CONDITIONS.get(c["id"], {})
            try:
                manager.vfx.show_damage(u.rect.centerx, u.rect.top - 30,
                                        f"{u.name} recovered from "
                                        f"{data.get('name', c['id'])}",
                                        color=(150, 230, 160))
            except Exception:
                pass


def check_day_rollover(manager):
    """Seuraa pelipäivää ja tikittää tilat kun päivä vaihtuu. Lisäksi
    pieni arkinen sairastumisriski (flunssa/ruokamyrkytys)."""
    clock = getattr(manager, "world_clock", None)
    if clock is None:
        return
    from world_clock import DAYS_PER_YEAR
    abs_day = int(clock.year) * DAYS_PER_YEAR + int(clock.day)
    last = getattr(manager, "_conditions_day", None)
    if last is None:
        manager._conditions_day = abs_day
        return
    if abs_day == last:
        return
    delta = max(1, abs_day - last)
    manager._conditions_day = abs_day
    tick_new_day(manager, days=delta)
    # Arjen riesat: pieni riski sairastua uuteen päivään
    for u in _roster(manager):
        if get_conditions(u):
            continue
        roll = random.random()
        if roll < 0.02:
            add_condition(u, "flu", manager)
        elif roll < 0.035:
            add_condition(u, "food_poisoning", manager)


def apply_battle_aftermath(manager, fighters, win):
    """Matsin jälkeen: kaatuneet/kolhitut voivat saada vammoja ja
    väsymystä; vakavassa kunnossa kentälle laitetut voivat KUOLLA."""
    messages = []
    for u in fighters:
        if u is None or u is getattr(manager, "player_character", None):
            continue
        # 1. Kuolemanriski realisoituu (tila oli jo ennen matsia)
        risk = getattr(u, "_prebattle_death_risk", 0.0)
        u._prebattle_death_risk = 0.0
        if risk > 0 and random.random() < risk:
            u.is_dead = True
            try:
                manager.my_team.remove(u)
            except Exception:
                pass
            messages.append(f"{u.name} succumbed to their wounds. "
                            f"The Yard falls silent.")
            continue
        # 2. Uudet vammat matsin jäljiltä
        hp_pct = u.current_hp / max(1, u.max_hp)
        if getattr(u, "is_dead", False) or hp_pct <= 0.05:
            if random.random() < 0.30:
                cid = random.choice(("severe_wound", "fracture"))
                if add_condition(u, cid, manager):
                    messages.append(f"{u.name} suffered a "
                                    f"{CONDITIONS[cid]['name'].lower()}.")
        elif hp_pct < 0.30 and random.random() < 0.18:
            if add_condition(u, "severe_wound", manager):
                messages.append(f"{u.name} suffered a severe wound.")
        # 3. Väsymys tappiosta
        if not win and random.random() < 0.25:
            add_condition(u, "fatigue", manager)
    return messages


def mark_prebattle_risks(manager, fighters):
    """Kutsutaan matsin alussa: lukitsee kuolemanriskin niille jotka
    lähtivät areenalle sairaana/vammautuneena."""
    for u in fighters:
        if u is None:
            continue
        u._prebattle_death_risk = death_risk(u)


def rest_heal(manager):
    """Yölepo barracksissa: väsymys paranee heti, muut tilat -1 pv."""
    for u in _roster(manager):
        remove_condition(u, "fatigue")
    tick_new_day(manager, days=0)  # ei ylimääräistä tikkiä; vain siivous


def treat_condition(manager, unit, cond_id):
    """Saggan hoito: maksaa REMEDY_PRICES-hinnan, poistaa tilan."""
    price = REMEDY_PRICES.get(cond_id)
    if price is None:
        return False, "That only heals with rest."
    if int(getattr(manager, "gold", 0)) < price:
        return False, "Not enough coin."
    if not remove_condition(unit, cond_id):
        return False, "No such ailment."
    manager.gold -= price
    return True, (f"{unit.name} treated for "
                  f"{CONDITIONS[cond_id]['name'].lower()} "
                  f"({price} SP).")


def treat_all(manager):
    """Hoitaa koko rosterin kaikki hoidettavat tilat. Palauttaa viestit."""
    messages = []
    for u in _roster(manager):
        for c in list(get_conditions(u)):
            cid = c.get("id")
            if cid in REMEDY_PRICES:
                ok, msg = treat_condition(manager, u, cid)
                messages.append(msg)
                if not ok:
                    return messages
    if not messages:
        messages.append("Nobody needs treatment.")
    return messages


def total_treatment_cost(manager) -> int:
    cost = 0
    for u in _roster(manager):
        for c in get_conditions(u):
            cost += REMEDY_PRICES.get(c.get("id"), 0)
    return cost


def _roster(manager):
    out = []
    try:
        out = [u for u in manager.my_team if u is not None]
    except Exception:
        pass
    return out


# ----------------------------------------------------------------------
# Persistenssi (save_manager kutsuu)
# ----------------------------------------------------------------------

def to_list(unit):
    return [dict(c) for c in get_conditions(unit)]


def from_list(unit, data):
    unit.conditions = [dict(c) for c in (data or [])
                       if isinstance(c, dict) and c.get("id") in CONDITIONS]
