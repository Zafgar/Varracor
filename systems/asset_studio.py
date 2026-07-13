# systems/asset_studio.py
"""Asset Studio -datakerros: pelin sisäinen työkalu spritejen, äänten ja
hitboxien hallintaan kehitysvaiheessa.

Työnkulku:
1. Pudota kuvat/äänet asset_inbox/-kansioon (nimillä ei väliä).
2. Avaa studio pelissä (F10 cheat-tilassa), valitse asset-paikka
   (kaikki koodin viittaamat polut listataan automaattisesti) ja
   inbox-tiedosto -> ASSIGN kopioi sen oikeaan kansioon oikealla nimellä.
3. HITBOX-välilehdellä säädetään propin törmäyslaatikko visuaalisesti;
   tallennus assets/hitbox_overrides.json:iin, jonka Prop.__init__
   soveltaa automaattisesti.

Peli käyttää tiedostoja heti kun ne ovat paikoillaan (procedural
fallback väistyy) - koodia ei tarvitse muuttaa.
"""

from __future__ import annotations

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX_DIR = os.path.join(ROOT, "asset_inbox")
HITBOX_FILE = os.path.join(ROOT, "assets", "hitbox_overrides.json")

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
SOUND_EXTS = {".wav", ".ogg"}
MUSIC_EXTS = {".mp3"}

KIND_LABELS = {"kuva": "image", "ääni": "sound", "musiikki": "music"}


def _kind_for(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in SOUND_EXTS:
        return "sound"
    if ext in MUSIC_EXTS:
        return "music"
    return "other"


def build_catalog():
    """Kaikki koodin viittaamat asset-polut skannerista.

    Palauttaa listan {path, exists, kind, group, sources} aakkosissa.
    """
    from tools.asset_scan import scan
    static_refs, _missing, _dynamic, _present = scan()
    catalog = []
    for path, srcs in sorted(static_refs.items()):
        catalog.append({
            "path": path,
            "exists": os.path.exists(os.path.join(ROOT, path)),
            "kind": _kind_for(path),
            "group": "/".join(path.split("/")[:2]),
            "sources": sorted(srcs),
        })
    return catalog


def refresh_missing_report() -> None:
    """Päivittää MISSING_ASSETS.md:n (sama kuin tools/asset_scan.py -ajo)."""
    try:
        from tools.asset_scan import scan, write_report
        write_report(*scan())
    except Exception as exc:
        print(f"[AssetStudio] Report refresh failed: {exc}")


# ---------------------------------------------------------------- inbox

def ensure_inbox() -> str:
    os.makedirs(INBOX_DIR, exist_ok=True)
    return INBOX_DIR


def list_inbox():
    """Inboxin tiedostot {name, kind, size} nimen mukaan."""
    ensure_inbox()
    entries = []
    for name in sorted(os.listdir(INBOX_DIR)):
        full = os.path.join(INBOX_DIR, name)
        if not os.path.isfile(full):
            continue
        kind = _kind_for(name)
        if kind == "other":
            continue
        entries.append({"name": name, "kind": kind,
                        "size": os.path.getsize(full)})
    return entries


def assign_asset(inbox_name: str, target_rel_path: str):
    """Kopioi inbox-tiedoston kohdepolkuun oikealla nimellä.

    Palauttaa (ok, viesti). Estää väärän tyypin (esim. .png äänipaikkaan) -
    kohteen pääte määrää: kopio nimetään AINA kohteen mukaan.
    """
    src = os.path.join(INBOX_DIR, os.path.basename(inbox_name))
    if not os.path.isfile(src):
        return False, f"Inbox file not found: {inbox_name}"

    src_kind = _kind_for(src)
    dst_kind = _kind_for(target_rel_path)
    if src_kind != dst_kind:
        return False, f"Type mismatch: {src_kind} file into {dst_kind} slot"

    dst = os.path.join(ROOT, target_rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        shutil.copyfile(src, dst)
    except Exception as exc:
        return False, f"Copy failed: {exc}"
    refresh_missing_report()
    return True, f"Installed -> {target_rel_path}"


# ---------------------------------------------------------------- hitboxit

def load_hitbox_overrides() -> dict:
    try:
        with open(HITBOX_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_hitbox_override(class_name: str, dx: int, dy: int, w: int, h: int):
    data = load_hitbox_overrides()
    data[str(class_name)] = {"dx": int(dx), "dy": int(dy),
                             "w": max(1, int(w)), "h": max(1, int(h))}
    os.makedirs(os.path.dirname(HITBOX_FILE), exist_ok=True)
    with open(HITBOX_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    _reload_prop_overrides()


def clear_hitbox_override(class_name: str):
    data = load_hitbox_overrides()
    if str(class_name) in data:
        del data[str(class_name)]
        with open(HITBOX_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
    _reload_prop_overrides()


def _reload_prop_overrides():
    try:
        from assets.tiles import prop as prop_module
        prop_module.reload_hitbox_overrides()
    except Exception as exc:
        print(f"[AssetStudio] Override reload failed: {exc}")


def editable_prop_classes():
    """Propit joiden hitboxia voi säätää: (nimi, luokka) aakkosissa.

    Kerätään kartoilla käytetyistä moduuleista luokat jotka ovat Prop-
    aliluokkia ja rakentuvat pelkällä (x, y):llä.
    """
    from assets.tiles.prop import Prop

    modules = []
    try:
        from assets.tiles import muckford_objects
        modules.append(muckford_objects)
    except Exception:
        pass
    try:
        from assets.tiles import farm_objects
        modules.append(farm_objects)
    except Exception:
        pass
    try:
        from assets.tiles import forest_objects
        modules.append(forest_objects)
    except Exception:
        pass

    result = []
    seen = set()
    for mod in modules:
        for name in dir(mod):
            cls = getattr(mod, name)
            if not isinstance(cls, type) or not issubclass(cls, Prop):
                continue
            if cls is Prop or name in seen:
                continue
            try:
                cls(0, 0)  # rakentuuko (x, y):llä?
            except Exception:
                continue
            seen.add(name)
            result.append((name, cls))
    result.sort(key=lambda pair: pair[0])
    return result
