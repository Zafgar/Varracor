# systems/ui_prefs.py
"""Kevyet UI-asetukset jotka säilyvät pelikertojen yli (saves/options.json).
Tällä hetkellä: questiseurannan (HUD-tracker) sijainti ruudulla, jonka
pelaaja voi raahata haluamaansa kohtaan."""
import json
import os

OPTIONS_FILE = "saves/options.json"


def _read():
    try:
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write(data):
    try:
        os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
        with open(OPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_quest_tracker_pos():
    """Palauttaa (x, y) tai None jos pelaaja ei ole siirtänyt trackeria."""
    ui = _read().get("ui", {})
    pos = ui.get("quest_tracker_pos")
    if isinstance(pos, (list, tuple)) and len(pos) == 2:
        try:
            return (int(pos[0]), int(pos[1]))
        except Exception:
            return None
    return None


def set_quest_tracker_pos(pos):
    data = _read()
    ui = data.setdefault("ui", {})
    if pos is None:
        ui.pop("quest_tracker_pos", None)
    else:
        ui["quest_tracker_pos"] = [int(pos[0]), int(pos[1])]
    _write(data)
