# systems/display_settings.py
"""Näyttöasetukset: ikkunatila ja resoluutio.

Peli renderöi AINA loogiseen 1920x1080-pintaan (pygame.SCALED) - SDL
skaalaa kuvan ikkunan/näytön kokoon. Resoluutiovalinta vaikuttaa siis
ikkunan kokoon (windowed) - borderless ja fullscreen käyttävät työpöydän
kokoa. Asetukset tallennetaan saves/options.json "display"-avaimen alle.

Tilat:
- windowed:   tavallinen ikkuna, koko valittavissa (AUTO = työpöytä)
- borderless: reunaton ikkuna työpöydän koossa (0,0)
- fullscreen: SDL:n desktop-fullscreen (ei näyttötilan vaihtoa)
"""
import json
import os

import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT

OPTIONS_FILE = "saves/options.json"

MODES = ("windowed", "borderless", "fullscreen")
MODE_LABELS = {
    "windowed": "WINDOWED",
    "borderless": "BORDERLESS",
    "fullscreen": "FULLSCREEN",
}

# Yleiset 16:9-koot; suodatetaan työpöydälle mahtuviin
_PRESETS = [(3840, 2160), (2560, 1440), (1920, 1080),
            (1600, 900), (1366, 768), (1280, 720)]

_state = {"mode": "windowed", "resolution": None}  # None = AUTO


def detect_desktop_size():
    """Työpöydän resoluutio, tai looginen koko jos ei saatavilla."""
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes:
            return tuple(sizes[0])
    except Exception:
        pass
    try:
        info = pygame.display.Info()
        if info.current_w > 0 and info.current_h > 0:
            return (info.current_w, info.current_h)
    except Exception:
        pass
    return (SCREEN_WIDTH, SCREEN_HEIGHT)


def available_resolutions():
    """[(label, koko-tuple tai None)] - AUTO (tunnistettu työpöytä) ensin."""
    desk = detect_desktop_size()
    out = [(f"AUTO ({desk[0]}x{desk[1]})", None)]
    for w, h in _PRESETS:
        if w <= desk[0] and h <= desk[1] and (w, h) != desk:
            out.append((f"{w}x{h}", (w, h)))
    if len(out) == 1:
        out.append((f"{desk[0]}x{desk[1]}", desk))
    return out


def get_mode():
    return _state["mode"]


def get_resolution():
    return _state["resolution"]


def resolution_label():
    for label, size in available_resolutions():
        if size == _state["resolution"]:
            return label
    if _state["resolution"]:
        return f"{_state['resolution'][0]}x{_state['resolution'][1]}"
    return available_resolutions()[0][0]


def _set_window(size, position=None):
    """Muuttaa ikkunan koon SDL2-Window-rajapinnalla (pygame-ce)."""
    try:
        win = pygame.Window.from_display_module()
        win.size = size
        if position is not None:
            win.position = position
        else:
            win.position = pygame.WINDOWPOS_CENTERED
    except Exception as exc:
        print(f"[Display] Window resize skipped: {exc}")


def apply(mode=None, resolution="keep"):
    """Soveltaa näyttötilan heti. resolution: tuple, None (=AUTO) tai
    "keep" (älä muuta). Palauttaa True onnistuessa."""
    if mode in MODES:
        _state["mode"] = mode
    if resolution != "keep":
        _state["resolution"] = tuple(resolution) if resolution else None

    active = _state["mode"]
    try:
        if active == "fullscreen":
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SCALED | pygame.FULLSCREEN)
        elif active == "borderless":
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SCALED | pygame.NOFRAME)
            _set_window(detect_desktop_size(), position=(0, 0))
        else:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SCALED)
            if _state["resolution"]:
                _set_window(_state["resolution"])
        return True
    except Exception as exc:
        print(f"[Display] Could not apply mode '{active}': {exc}")
        try:
            pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                    pygame.SCALED)
        except Exception:
            pass
        return False


def save():
    """Tallentaa display-asetukset options.jsoniin muita avaimia säilyttäen."""
    data = {}
    try:
        if os.path.exists(OPTIONS_FILE):
            with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
    except Exception:
        data = {}
    data["display"] = {
        "mode": _state["mode"],
        "resolution": list(_state["resolution"]) if _state["resolution"] else None,
    }
    try:
        os.makedirs(os.path.dirname(OPTIONS_FILE), exist_ok=True)
        with open(OPTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as exc:
        print(f"[Display] Save failed: {exc}")


def load():
    try:
        if not os.path.exists(OPTIONS_FILE):
            return
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        stored = data.get("display") or {}
        if stored.get("mode") in MODES:
            _state["mode"] = stored["mode"]
        res = stored.get("resolution")
        if isinstance(res, (list, tuple)) and len(res) == 2:
            _state["resolution"] = (int(res[0]), int(res[1]))
        else:
            _state["resolution"] = None
    except Exception as exc:
        print(f"[Display] Load failed: {exc}")


def load_and_apply():
    """Käynnistyksessä: lue tallennetut asetukset ja sovella. Windowed +
    AUTO ei koske ikkunaan (set_mode on jo tehty main.py:ssä)."""
    load()
    if _state["mode"] != "windowed" or _state["resolution"]:
        apply()
