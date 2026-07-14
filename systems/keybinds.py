# systems/keybinds.py
"""Keskitetty näppäinasettelu (rebind-tuki).

Kaikki pelattavuuden näppäimet luetaan täältä nimellä ("interact",
"move_up"...), eivät kovakoodattuina pygame-vakioina. Asettelu
tallennetaan saves/options.json-tiedostoon "keybinds"-avaimen alle
(sama tiedosto kuin äänivoluumit), joten se säilyy pelikertojen yli.

Käyttö:
    from systems import keybinds
    if keys[keybinds.key("move_up")]: ...
    if keybinds.pressed(keys, "sprint"): ...   # tukee vara-näppäimiä
    keybinds.set_key("interact", pygame.K_f); keybinds.save()
"""

import json
import os

import pygame

OPTIONS_FILE = "saves/options.json"

# action -> lista näppäinkoodeja (ensimmäinen on "pää-näppäin", loput varoja)
DEFAULTS = {
    "move_up":        [pygame.K_w],
    "move_down":      [pygame.K_s],
    "move_left":      [pygame.K_a],
    "move_right":     [pygame.K_d],
    "sprint":         [pygame.K_LSHIFT, pygame.K_RSHIFT],
    "dash":           [pygame.K_SPACE],
    "racial_ability": [pygame.K_r],
    "interact":       [pygame.K_e],
    "map":            [pygame.K_m],
    "commander_menu": [pygame.K_c],
    "spell_1":        [pygame.K_1],
    "spell_2":        [pygame.K_2],
    "spell_3":        [pygame.K_3],
    "usable_1":       [pygame.K_4, pygame.K_7],
    "spell_5":        [pygame.K_5],
    "spell_6":        [pygame.K_6],
    "usable_2":       [pygame.K_8],
    # Commander shoutit (avataan COMMAND-taitopuusta)
    "shout_rally":    [pygame.K_g],
    "shout_charge":   [pygame.K_h],
}

# Näytettävät nimet Controls-valikkoon (järjestys = näyttöjärjestys)
LABELS = [
    ("move_up",        "Move Up"),
    ("move_down",      "Move Down"),
    ("move_left",      "Move Left"),
    ("move_right",     "Move Right"),
    ("sprint",         "Sprint"),
    ("dash",           "Dash"),
    ("racial_ability", "Racial Ability"),
    ("interact",       "Interact / Fish"),
    ("map",            "World Map"),
    ("commander_menu", "Commander Menu"),
    ("spell_1",        "Spell Slot 1"),
    ("spell_2",        "Spell Slot 2"),
    ("spell_3",        "Spell Slot 3"),
    ("spell_5",        "Spell Slot 5"),
    ("spell_6",        "Spell Slot 6"),
    ("shout_rally",    "Shout: Rally Cry"),
    ("shout_charge",   "Shout: Charge Order"),
    ("usable_1",       "Usable Item 1"),
    ("usable_2",       "Usable Item 2"),
]

# Kiinteät kontrollit (näytetään infona, ei voi sitoa uudelleen)
FIXED = [
    ("Attack / Cast", "Left Mouse"),
    ("Block",         "Right Mouse"),
    ("Menu / Back",   "ESC"),
]

_binds: dict[str, list[int]] = {}


def _ensure_loaded():
    if not _binds:
        reset_defaults(save_after=False)
        load()


def reset_defaults(save_after=True):
    _binds.clear()
    for action, codes in DEFAULTS.items():
        _binds[action] = list(codes)
    if save_after:
        save()


def key(action: str) -> int:
    """Toiminnon pää-näppäinkoodi."""
    _ensure_loaded()
    codes = _binds.get(action) or DEFAULTS.get(action) or [0]
    return codes[0]


def keys_for(action: str) -> list[int]:
    _ensure_loaded()
    return list(_binds.get(action) or DEFAULTS.get(action) or [])


def pressed(pressed_keys, action: str) -> bool:
    """True jos mikä tahansa toiminnon näppäimistä on pohjassa."""
    for code in keys_for(action):
        try:
            if pressed_keys[code]:
                return True
        except IndexError:
            pass
    return False


def matches(event_key: int, action: str) -> bool:
    """True jos KEYDOWN-eventin näppäin vastaa toimintoa."""
    return event_key in keys_for(action)


def set_key(action: str, code: int):
    """Sido toiminnon pää-näppäin uudelleen. Sama näppäin irrotetaan
    muista toiminnoista (ei kaksoissidontoja)."""
    _ensure_loaded()
    if action not in DEFAULTS:
        return
    for other, codes in _binds.items():
        if other != action and code in codes:
            codes.remove(code)
            if not codes:  # älä jätä toimintoa ilman näppäintä
                codes.extend(c for c in DEFAULTS[other] if c != code)
    existing = _binds.get(action, [])
    _binds[action] = [code] + [c for c in existing[1:] if c != code]


def key_name(action: str) -> str:
    names = [pygame.key.name(c).upper() for c in keys_for(action)]
    return " / ".join(n for n in names if n) or "-"


def save():
    _ensure_loaded()
    data = {}
    try:
        if os.path.exists(OPTIONS_FILE):
            with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
    except Exception:
        data = {}
    data["keybinds"] = {a: list(c) for a, c in _binds.items()}
    try:
        os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
        with open(OPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        print(f"[Keybinds] Save failed: {exc}")


def load():
    try:
        if not os.path.exists(OPTIONS_FILE):
            return
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        stored = data.get("keybinds") or {}
        for action, codes in stored.items():
            if action in DEFAULTS and isinstance(codes, list) and codes:
                _binds[action] = [int(c) for c in codes]
    except Exception as exc:
        print(f"[Keybinds] Load failed: {exc}")
