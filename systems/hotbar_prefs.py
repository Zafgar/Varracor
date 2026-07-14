# systems/hotbar_prefs.py
"""Hotbarin asetukset (pelitesti 17): per-slotti instant cast ja
lukitus. Tallentuu saves/options.json "hotbar"-avaimeen samaan tapaan
kuin keybindit - säilyy pelikertojen yli.

- instant cast: näppäimen painallus castaa HETI kursorin suuntaan
  (ei valinta + klikkaus). Asetetaan per slotti (spell1..usable2)
  options-valikon CONTROLS-osiosta.
- locked: kun lukko on kiinni, hotbarin järjestystä ei voi raahata.
"""
import json
import os

OPTIONS_FILE = "saves/options.json"

SLOT_ORDER = ["spell1", "spell2", "spell3", "spell4", "spell5", "spell6",
              "usable", "usable2"]

_state = {
    "instant": {},          # slot -> bool
    "locked": True,
}
_loaded = False


def _load():
    global _loaded
    _loaded = True
    try:
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        hb = data.get("hotbar", {})
        inst = hb.get("instant", {})
        _state["instant"] = {k: bool(v) for k, v in inst.items()}
        _state["locked"] = bool(hb.get("locked", True))
    except Exception:
        pass


def save():
    data = {}
    try:
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    data["hotbar"] = {"instant": dict(_state["instant"]),
                      "locked": bool(_state["locked"])}
    try:
        os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
        with open(OPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def is_instant(slot: str) -> bool:
    if not _loaded:
        _load()
    return bool(_state["instant"].get(slot, False))


def set_instant(slot: str, value: bool):
    if not _loaded:
        _load()
    _state["instant"][slot] = bool(value)
    save()


def toggle_instant(slot: str) -> bool:
    set_instant(slot, not is_instant(slot))
    return is_instant(slot)


def is_locked() -> bool:
    if not _loaded:
        _load()
    return bool(_state["locked"])


def set_locked(value: bool):
    if not _loaded:
        _load()
    _state["locked"] = bool(value)
    save()


def toggle_locked() -> bool:
    set_locked(not is_locked())
    return is_locked()
