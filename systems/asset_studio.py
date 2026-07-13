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


# Yksiköiden spritesarjat: polkukaava + animaatiotilat. Studio näyttää
# jokaisen tilan statuksen ja asentaa inbox-tiedostot suoraan oikeaan
# polkuun. Death piirretään pelissä kaatamalla idle-kuva (ei omaa slottia).
_RACE_ACTS = ("idle", "run", "attack", "hurt", "cast")
UNIT_SPRITE_SETS = {
    "Human": ("assets/races/human/human_{act}_1.png", _RACE_ACTS),
    "Orc": ("assets/races/orc/orc_{act}_1.png", _RACE_ACTS),
    "Elf": ("assets/races/elf/elf_{act}_1.png", _RACE_ACTS),
    "Goblin": ("assets/races/goblin/goblin_{act}_1.png", _RACE_ACTS),
    "Dwarf": ("assets/races/dwarf/dwarf_{act}_1.png", _RACE_ACTS),
    "Gnome": ("assets/races/gnome/gnome_{act}_1.png", _RACE_ACTS),
    "Werewolf": ("assets/races/werewolf/werewolf_{act}_1.png", _RACE_ACTS),
    "Tortle": ("assets/races/tortle/tortle_{act}_1.png", _RACE_ACTS),
    "Troll": ("assets/races/forest/troll/troll_{act}_1.png", _RACE_ACTS),
    "Villager": ("assets/races/human/human_{act}_1.png", _RACE_ACTS),
    "UndeadSkeleton": ("assets/races/undead/skeleton/skeleton_{act}.png",
                       ("idle", "run", "attack", "hit")),
    "UndeadZombie": ("assets/races/undead/zombie/zombie_{act}.png",
                     ("idle", "run", "attack", "hit")),
    "GiantRat": ("assets/races/rat/giant_rat_{act}.png",
                 ("run", "attack", "hurt")),
    "RatKing": ("assets/races/rat/rat_king_{act}.png",
                ("idle", "run", "attack", "hurt", "rage", "spit")),
    "Cow": ("assets/races/animals/cow_1_{act}.png",
            ("idle", "walk", "eat", "moo")),
    "Chicken": ("assets/races/animals/chicken_{act}.png",
                ("idle", "walk")),
}


def unit_sprite_set(label):
    """Yksikön animaatiotilat: [{action, path, exists}] tai []."""
    entry = UNIT_SPRITE_SETS.get(label)
    if not entry:
        return []
    pattern, acts = entry
    rows = []
    for act in acts:
        path = pattern.format(act=act)
        rows.append({"action": act, "path": path,
                     "exists": os.path.exists(os.path.join(ROOT, path))})
    return rows


def preview_unit_factories():
    """Studion UNITS-penkin yksiköt: (nimi, factory(x, y)) aakkosissa.

    Factory luo tuoreen yksikön annettuun kohtaan. Vain rakentuvat
    luokat listataan (koeponnistus konstruktorilla).
    """
    from settings import GREEN

    candidates = []

    def race(mod_name, cls_name):
        def make(x, y):
            mod = __import__(f"units.{mod_name}", fromlist=[cls_name])
            return getattr(mod, cls_name)("Preview", x, y, GREEN)
        return make

    for mod_name, cls_name in (
            ("human", "Human"), ("orc", "Orc"), ("elf", "Elf"),
            ("goblin", "Goblin"), ("dwarf", "Dwarf"), ("gnome", "Gnome"),
            ("rat", "GiantRat"),
            ("undead_skeleton", "UndeadSkeleton"),
            ("undead_zombie", "UndeadZombie"),
            ("werewolf", "Werewolf"), ("troll", "Troll"),
            ("tortle", "Tortle")):
        candidates.append((cls_name, race(mod_name, cls_name)))

    def rat_king(x, y):
        from units.rat_king import RatKing
        return RatKing("Rat King", x, y)
    candidates.append(("RatKing", rat_king))

    def villager(x, y):
        from units.villager import Villager
        return Villager("Preview", "Human", x, y, team_color=GREEN)
    candidates.append(("Villager", villager))

    def cow(x, y):
        from units.farm_animals import Cow
        return Cow(x, y)
    candidates.append(("Cow", cow))

    def chicken(x, y):
        from units.farm_animals import Chicken
        return Chicken(x, y)
    candidates.append(("Chicken", chicken))

    result = []
    for label, factory in candidates:
        try:
            unit = factory(0, 0)
            if not hasattr(unit, "draw_on_screen"):
                continue
        except Exception:
            continue
        result.append((label, factory))
    result.sort(key=lambda pair: pair[0])
    return result


def equipable_items():
    """Varusteet sloteittain studion pukemispenkkiin.

    Palauttaa {"main_hand": [nimet], "off_hand": [...], "head": [...],
    "body": [...]} - nimet kelpaavat create_itemille.
    """
    from items.item_registry import get_available_item_classes

    slots = {"main_hand": [], "off_hand": [], "head": [], "body": []}
    for cls in get_available_item_classes():
        try:
            item = cls()
        except Exception:
            continue
        slot = str(getattr(item, "slot_type", "")).lower()
        itype = str(getattr(item, "type", "")).lower()
        name = getattr(item, "name", cls.__name__)
        if str(name).lower() in ("fists", "no armor"):
            continue  # tarkoituksella näkymättömät perusarvot
        if slot in ("head", "body"):
            slots[slot].append(name)
        elif slot == "off_hand" or itype == "shield":
            slots["off_hand"].append(name)
        elif slot == "main_hand" or itype in ("melee", "ranged"):
            slots["main_hand"].append(name)
    for names in slots.values():
        names.sort()
    return slots


def vfx_catalog():
    """Studion VFX-penkin efektit: (nimi, laukaisin(vfx, x, y)).

    Laukaisin kutsuu VFXManagerin create-metodia ankkuripisteeseen;
    suuntaefektit (salama, tulipallo) ammutaan viistosti pisteeseen.
    """
    def simple(method):
        def fire(vfx, x, y):
            getattr(vfx, method)(x, y)
        return fire

    def beam(method, ox=-120, oy=-90):
        def fire(vfx, x, y):
            getattr(vfx, method)((x + ox, y + oy), (x, y))
        return fire

    return [
        ("Smoke", simple("create_smoke")),
        ("Steam", simple("create_steam")),
        ("Flies", simple("create_flies")),
        ("Impact Sparks", simple("create_impact_sparks")),
        ("Blood", simple("create_blood")),
        ("Explosion", simple("create_explosion")),
        ("Fireburst", simple("create_fireburst")),
        ("Heal", simple("create_heal_effect")),
        ("Falling Leaves", simple("create_falling_leaves")),
        ("Mud Bubble", simple("create_mud_bubble")),
        ("Musical Note", simple("create_musical_note")),
        ("Shockwave", simple("create_shockwave")),
        ("Tavern Dust", simple("create_tavern_dust")),
        ("Void Particles", simple("create_void_particles")),
        ("Power Shot Impact", simple("create_power_shot_impact")),
        ("Seam Cut", simple("create_seam_cut")),
        ("Lightning", beam("create_lightning")),
        ("Arrow", beam("create_arrow")),
        ("Power Arrow", beam("create_power_arrow")),
        ("Warp Seam", beam("create_warp_seam", ox=-90, oy=0)),
    ]


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
