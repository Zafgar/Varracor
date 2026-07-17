# systems/map_document.py
"""Karttadokumentti: nimetyn kartan serialisointi, vienti ja tuonti.

TYÖNKULKU (pelitesti 29): tekijä rakentaa kartan pelin sisäisellä
editorilla (F8), nimeää sen (F7) ja vie sen F9:llä YHDEKSI kompaktiksi
JSON-riviksi (map_export.txt + konsoli). Sen rivin voi liittää chattiin,
ja se kovakoodataan peliin maps/custom_maps.py-rekisteriin, josta
editori ja pelitilat lataavat sen takaisin. Näin editorissa tehty
kartta kulkee tekstinä ilman tiedostonsiirtoa.

Sama moduuli hoitaa sekä editorin projektitallennuksen että pelin
karttalatauksen - EI kahta rinnakkaista serialisointia.

Formaatti (versio 1):
{
  "format": "VARRACOR-MAP", "version": 1,
  "name": "...", "width": 6000, "height": 4000,
  "floor_props": [ {class, x, y, ...}, ... ],
  "props":       [ ... ],
  "units":       [ {class, name, x, y, team_color, equipment, ...}, ... ]
}
"""
from __future__ import annotations

import importlib
import json
from typing import Dict, List, Optional

import pygame

from settings import RED, GREEN

FORMAT_KEY = "VARRACOR-MAP"
VERSION = 1

# Moduulit joiden luokat kelpaavat kartalle (propit + lattiat)
_PROP_MODULES = (
    "assets.tiles.house_objects",
    "assets.tiles.tavern_objects",
    "assets.tiles.muckford_objects",
    "assets.tiles.farm_objects",
    "assets.tiles.forest_objects",
    "assets.tiles.crypt_objects",
    "assets.tiles.crypt_walls",
    "assets.tiles.blacksmith_objects",
    "assets.tiles.bog_objects",
    "assets.tiles.editor_floors",
    "assets.tiles.effect_emitters",
    "systems.field_kit",
    "crafting.swamp.scrap_pile",
)

# NPC:t joita monster-rekisteri ei kata (nimi, rotu, väri) -konstruktorit
_SPECIAL_UNITS = {
    "Villager": ("units.villager", "Villager"),
    "Bard": ("units.bard", "Bard"),
    "MardaShant": ("units.marda_shant", "MardaShant"),
    "Human": ("units.human", "Human"),
    "Orc": ("units.orc", "Orc"),
    "Elf": ("units.elf", "Elf"),
    "Goblin": ("units.goblin", "Goblin"),
}

_prop_class_cache: Dict[str, type] = {}


def _prop_class(name: str) -> Optional[type]:
    """Hakee prop-luokan nimellä kaikista karttamoduuleista (laiska)."""
    if name in _prop_class_cache:
        return _prop_class_cache[name]
    for modname in _PROP_MODULES:
        try:
            module = importlib.import_module(modname)
        except Exception:
            continue
        cls = getattr(module, name, None)
        if isinstance(cls, type):
            _prop_class_cache[name] = cls
            return cls
    return None


def _monster_by_class_name(cls_name: str):
    """Monster-rekisterin kanoninen nimi luokan nimellä (esim. GiantRat)."""
    from units import monster_registry as reg
    for info in reg.MONSTERS:
        if info.cls == cls_name:
            return info
    return None


def _is_unit(obj) -> bool:
    from gladiator import Gladiator
    return isinstance(obj, Gladiator)


# ---------------------------------------------------------------- vienti
def serialize_object(p) -> dict:
    pos = getattr(p, "image_pos", None) or p.rect.topleft
    data = {"class": p.__class__.__name__, "x": int(pos[0]), "y": int(pos[1])}
    if hasattr(p, "serialize_extra"):
        data.update(p.serialize_extra())
    if hasattr(p, "variant"):
        data["variant"] = p.variant
    if getattr(p, "angle", 0):
        data["angle"] = p.angle
    if hasattr(p, "has_shadow") and p.has_shadow is False:
        data["has_shadow"] = False
    if getattr(p, "_shadow_shape", "ellipse") != "ellipse":
        data["shadow_shape"] = p._shadow_shape
    if getattr(p, "_editor_note", ""):
        data["note"] = p._editor_note
    if getattr(p, "_hitbox_modified", False):
        img_pos = getattr(p, "image_pos", p.rect.topleft)
        data["hitbox"] = [p.rect.x - img_pos[0], p.rect.y - img_pos[1],
                          p.rect.w, p.rect.h]
    return data


def serialize_unit(u) -> dict:
    data = serialize_object(u)
    data["name"] = getattr(u, "name", data["class"])
    col = getattr(u, "team_color", None)
    if isinstance(col, (tuple, list)):
        data["team_color"] = list(col[:3])
    if hasattr(u, "facing_right") and not u.facing_right:
        data["facing_right"] = False
    equipment = {}
    for slot, item in getattr(u, "equipment", {}).items():
        if item and getattr(item, "name", "") not in ("Fists", "No Armor"):
            equipment[slot] = item.name
    if equipment:
        data["equipment"] = equipment
    return data


def serialize_map(arena, name: Optional[str] = None) -> dict:
    """Kokoaa areenan sisällön karttadokumentiksi."""
    doc = {
        "format": FORMAT_KEY,
        "version": VERSION,
        "name": str(name or getattr(arena, "map_name", "") or "Unnamed Map"),
        "width": int(getattr(arena, "width", 5760)),
        "height": int(getattr(arena, "height", 3240)),
        "floor_props": [],
        "props": [],
        "units": [],
    }
    for p in getattr(arena, "floor_props", []):
        doc["floor_props"].append(serialize_object(p))
    for p in getattr(arena, "props", []):
        if _is_unit(p):
            doc["units"].append(serialize_unit(p))
        else:
            doc["props"].append(serialize_object(p))
    return doc


def export_blob(doc: dict) -> str:
    """Kompakti yksirivinen JSON - liitettäväksi chattiin."""
    return json.dumps(doc, separators=(",", ":"), sort_keys=True)


def import_blob(text: str) -> dict:
    """Lukee viedyn kartan (siedä ympäröivät välilyönnit/rivinvaihdot)."""
    doc = json.loads(text.strip())
    if doc.get("format") != FORMAT_KEY:
        raise ValueError(f"Ei {FORMAT_KEY}-dokumentti")
    return doc


# ---------------------------------------------------------------- tuonti
def _construct_unit(entry: dict):
    from settings import ENEMY_TEAM
    cls_name = entry["class"]
    x, y = int(entry["x"]), int(entry["y"])
    col = entry.get("team_color")
    col = tuple(col) if col else None

    info = _monster_by_class_name(cls_name)
    if info is not None:
        from units.monster_registry import create_monster
        unit = create_monster(info.name, x, y, col or ENEMY_TEAM,
                              display_name=entry.get("name"))
        return unit

    special = _SPECIAL_UNITS.get(cls_name)
    if special is None:
        return None
    module = importlib.import_module(special[0])
    cls = getattr(module, special[1])
    label = entry.get("name") or cls_name
    if cls_name == "Villager":
        return cls(label, "Human", x, y, col or GREEN)
    if cls_name == "Bard":
        return cls(label, "Elf", x, y, col or GREEN)
    if cls_name == "MardaShant":
        return cls(x, y)
    if cls_name == "Human":
        return cls(label, x, y, col or RED, "Common")
    return cls(label, x, y, col or RED)


def _construct_prop(entry: dict):
    from assets.tiles.water import FishingJetty, WaterBody
    cls_name = entry["class"]
    x, y = int(entry["x"]), int(entry["y"])
    if cls_name == "WaterBody":
        return WaterBody(x, y, entry.get("w", 400), entry.get("h", 300),
                         seed=entry.get("seed", 7),
                         name=entry.get("name", "water"),
                         style=entry.get("style", "auto"))
    if cls_name == "FishingJetty":
        return FishingJetty(x, y, entry.get("w", 170), entry.get("h", 64),
                            seed=entry.get("seed", 3))
    # Kenttäpakin luokat: konstruktorit ottavat lisäargumentteja
    if cls_name == "GateZone":
        from systems.field_kit import GateZone
        return GateZone(x, y, entry.get("w", 140), entry.get("h", 90),
                        kind=entry.get("kind", "arch"),
                        label=entry.get("label", "EXIT"),
                        facing=entry.get("facing", "down"))
    if cls_name == "WallSegment":
        from systems.field_kit import WallSegment
        return WallSegment(x, y, entry.get("w", 40), entry.get("h", 40),
                           style=entry.get("style", "crypt"))
    if cls_name == "FloorPatch":
        from systems.field_kit import FloorPatch
        return FloorPatch(x, y, entry.get("w", 200), entry.get("h", 200),
                          style=entry.get("style", "crypt"))
    if cls_name == "FieldResourceNode":
        from systems.field_kit import FieldResourceNode
        return FieldResourceNode(entry.get("node_id", ""), x, y,
                                 entry.get("resource", "Herb"),
                                 entry.get("style", "herb"),
                                 tuple(entry.get("amount", (1, 2))))
    cls = _prop_class(cls_name)
    if cls is None:
        return None
    try:
        return cls(x, y, variant=entry.get("variant", 1))
    except TypeError:
        return cls(x, y)


def _apply_common(obj, entry: dict):
    if "angle" in entry and hasattr(obj, "rotate"):
        try:
            obj.rotate(entry["angle"])
        except Exception:
            pass
    if "facing_right" in entry and hasattr(obj, "facing_right"):
        obj.facing_right = entry["facing_right"]
    if entry.get("has_shadow") is False:
        obj.has_shadow = False
    if "shadow_shape" in entry:
        obj._shadow_shape = entry["shadow_shape"]
    if "note" in entry:
        obj._editor_note = entry["note"]
        obj._editor_created = True
    if "hitbox" in entry:
        rel_x, rel_y, w, h = entry["hitbox"]
        img_pos = getattr(obj, "image_pos", obj.rect.topleft)
        obj.rect = pygame.Rect(img_pos[0] + rel_x, img_pos[1] + rel_y, w, h)
        obj._hitbox_modified = True
    if "equipment" in entry and hasattr(obj, "equip_item"):
        from items.item_registry import create_item
        for _slot, item_name in entry["equipment"].items():
            item = create_item(item_name)
            if item:
                obj.equip_item(item)


def apply_to_arena(doc: dict, arena, manager=None) -> List[object]:
    """Lataa dokumentin sisällön OLEMASSA OLEVAAN areenaan (tyhjentää
    vanhat propit). Palauttaa luodut yksiköt. Ruudut pitävät areena-
    viittauksensa, joten sisältö vaihdetaan paikallaan."""
    from assets.tiles.water import rebuild_water_blockers
    from gladiator import Gladiator

    arena.map_name = doc.get("name", "Unnamed Map")
    new_w, new_h = int(doc.get("width", 0)), int(doc.get("height", 0))
    if new_w > 0 and new_h > 0:
        resize_arena(arena, new_w, new_h)

    arena.props.clear()
    arena.obstacles.clear()
    if hasattr(arena, "floor_props"):
        arena.floor_props.clear()

    for entry in doc.get("floor_props", []):
        obj = _construct_prop(entry)
        if obj is None:
            print(f"[map] tuntematon lattialuokka: {entry['class']}")
            continue
        _apply_common(obj, entry)
        arena.floor_props.append(obj)

    for entry in doc.get("props", []):
        obj = _construct_prop(entry)
        if obj is None:
            print(f"[map] tuntematon prop-luokka: {entry['class']}")
            continue
        _apply_common(obj, entry)
        arena.props.append(obj)
        if obj.rect.w > 0 and obj.rect.h > 0 and \
                not getattr(obj, "is_floor", False) and \
                not getattr(obj, "is_effect", False):
            arena.obstacles.append(obj)

    units: List[object] = []
    for entry in doc.get("units", []):
        unit = _construct_unit(entry)
        if unit is None:
            print(f"[map] tuntematon yksikkö: {entry['class']}")
            continue
        _apply_common(unit, entry)
        arena.props.append(unit)
        units.append(unit)

    rebuild_water_blockers(arena)

    # Reitinhaku uusiksi uusille esteille
    if manager is not None and getattr(manager, "pathfinder", None) is not None:
        try:
            from ai.pathfinding import NavigationGrid
            manager.pathfinder = NavigationGrid(arena)
        except Exception:
            pass
    return units


def resize_arena(arena, width: int, height: int):
    """Muuttaa areenan koon (VALTAVAT kartat ok - lattia rakennetaan
    uudelleen samalla luokalla jos mahdollista)."""
    arena.width = int(width)
    arena.height = int(height)
    floor = getattr(arena, "floor", None)
    if floor is not None:
        try:
            arena.floor = type(floor)(arena.width, arena.height)
        except Exception:
            pass
