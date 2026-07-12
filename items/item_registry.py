import random
import inspect
import pkgutil
import importlib

# -------------------------
# RARITY CONFIG
# -------------------------
RARITY_ORDER = ["Common", "Rare", "Epic", "Legendary", "Artifact"]

# Huonoin yleisin -> artifact harvinaisin
RARITY_WEIGHTS_DEFAULT = {
    "Common": 8,
    "Rare": 6,
    "Epic": 4,
    "Legendary": 2,
    "Artifact": 1,
}

# -------------------------
# BASE ITEM IMPORT (robust)
# -------------------------
_ItemBase = None
_WeaponBase = None
_ArmorBase = None
_NewItemBase = None

try:
    from items.base_item import Item as _ItemBase
    from items.base_item import Weapon as _WeaponBase
    from items.base_item import Armor as _ArmorBase
except Exception:
    pass

try:
    from items.item import Item as _NewItemBase
except Exception:
    pass

try:
    from items.swords.vortex_blade import VortexBlade
except Exception:
    pass

# -------------------------
# DISCOVERY CACHE
# -------------------------
_DISCOVERED = None            # list of classes
_META_CACHE = {}              # class -> dict(type, rarity, name)


def _normalize_rarity(r):
    if not r:
        return None
    r = str(r).strip()
    if not r:
        return None
    return r[:1].upper() + r[1:].lower()


def _is_item_class(cls):
    # pitää olla luokka
    if not inspect.isclass(cls):
        return False

    # 1. BASE CLASS FILTER (TÄRKEÄ KORJAUS)
    # Estetään keskeneräisten base-luokkien päätyminen kauppaan
    ignored_bases = {
        "Item", "Weapon", "Armor", "BaseItem", 
        "Shield", "Helmet", "Potion", "Relic", "Usable"
    }
    if cls.__name__ in ignored_bases:
        return False

    # jos meillä on Item base, käytä issubclass
    if _ItemBase is not None:
        try:
            if issubclass(cls, _ItemBase) and cls is not _ItemBase:
                return True
        except Exception:
            pass

    # Tarkistetaan myös uusi Item-base
    if _NewItemBase is not None:
        try:
            if issubclass(cls, _NewItemBase) and cls is not _NewItemBase:
                return True
        except Exception:
            pass

    # fallback: heuristiikka
    try:
        inst = cls()
        return hasattr(inst, "name") and hasattr(inst, "cost")
    except Exception:
        return False


def _discover_item_classes(force=False):
    global _DISCOVERED
    if _DISCOVERED is not None and not force:
        return _DISCOVERED

    discovered = []
    seen = set()

    try:
        import items  # items package
        for modinfo in pkgutil.walk_packages(items.__path__, items.__name__ + "."):
            modname = modinfo.name
            if modname.endswith(".item_registry"):
                continue

            try:
                module = importlib.import_module(modname)
            except Exception:
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if getattr(obj, "__module__", "") != module.__name__:
                    continue
                if not _is_item_class(obj):
                    continue

                key = (obj.__module__, obj.__name__)
                if key in seen:
                    continue
                seen.add(key)
                discovered.append(obj)
    except Exception:
        discovered = []

    _DISCOVERED = discovered
    return _DISCOVERED


def get_available_item_classes():
    """Palauttaa listan kaikista löydetyistä item-luokista (auto-discovery)."""
    return _discover_item_classes(force=False)


def clear_registry_cache():
    """Jos lisäät uusia itemeitä ajon aikana ja haluat refreshata discovery/metat."""
    global _DISCOVERED
    _DISCOVERED = None
    _META_CACHE.clear()


def _meta(ItemClass):
    """
    Cachetaan instanssi-metat (type/rarity/name) ettei instansoida joka kerta turhaan.
    """
    if ItemClass in _META_CACHE:
        return _META_CACHE[ItemClass]

    m = {"type": None, "rarity": None, "name": None}
    try:
        it = ItemClass()

        # 1) Ensisijainen: päättele shop-kategoria luokan perusteella
        if _WeaponBase is not None and isinstance(it, _WeaponBase):
            m["type"] = "Weapon"
        elif _ArmorBase is not None and isinstance(it, _ArmorBase):
            m["type"] = "Armor"
        else:
            m["type"] = getattr(it, "type", None)

        # 2) Fallback: jos type on melee/ranged/weapon -> Weapon
        t = (str(m["type"]).strip().lower() if m["type"] is not None else "")
        
        if t in ("melee", "ranged", "weapon", "weapons"):
            m["type"] = "Weapon"
        elif t in ("armor", "armour", "shield", "helmet"): # KORJAUS: Helmet ja Shield ovat Armoria
            m["type"] = "Armor"
        elif "usable" in t or "consum" in t or "potion" in t:
            m["type"] = "Usable"
        elif "relic" in t:
            m["type"] = "Weapon" # Tai Armor, riippuen kumpaan haluat Off-hand Relicit (yleensä Weapon/Offhand slot)

        m["rarity"] = _normalize_rarity(getattr(it, "rarity", None))
        m["name"] = getattr(it, "name", None)
    except Exception:
        pass

    _META_CACHE[ItemClass] = m
    return m


def roll_rarity(weights=None):
    weights = weights or RARITY_WEIGHTS_DEFAULT
    bag = []
    for r in RARITY_ORDER:
        w = int(weights.get(r, 0))
        if w > 0:
            bag.extend([r] * w)
    return random.choice(bag) if bag else "Common"


def create_item(name):
    """
    Luo itemin nimen tai class-nimen perusteella.
    Käytetään save/load/crafting.
    """
    name = str(name).strip()

    # Data-driven loitsukirjasto (magic/spell_data.py) ennen luokkaskannausta
    try:
        from magic.library_spell import create_library_spell
        _sp = create_library_spell(name)
        if _sp is not None:
            return _sp
    except Exception:
        pass

    for C in get_available_item_classes():
        try:
            if C.__name__ == name:
                return C()
            m = _meta(C)
            if m.get("name") == name:
                return C()
        except Exception:
            continue

    print(f"WARNING: create_item: item '{name}' not found in registry.")
    return None


def create_fists():
    """
    Palauttaa Fists-weaponin instanssin.
    Gladiator importtaa tätä.
    """
    # Suora importti (luokka asuu tiedostossa 'fists.py')
    try:
        from items.misc.fists import Fists
        return Fists()
    except Exception:
        pass

    # Etsitään rekisteristä
    for C in get_available_item_classes():
        if C.__name__ == "Fists":
            try:
                return C()
            except Exception:
                pass
        try:
            m = _meta(C)
            if m.get("name") == "Fists":
                return C()
        except Exception:
            pass

    return None


def get_random_shop_items(count=5, category=None, rarity_mode="ROLL", rarity_weights=None, include_fists=False):
    """
    Backward-compatible: get_random_shop_items(5) toimii.
    category: "Weapon" | "Armor" | "Usable" | None
    rarity_mode: "ROLL" tai "Common/Rare/Epic/Legendary/Artifact"
    """
    pool = get_available_item_classes()

    # poista nyrkit shopista oletuksena
    if not include_fists:
        pool = [C for C in pool if C.__name__ != "Fists"]

    # category filtteri (nyt toimii myös melee/ranged aseille, koska _meta mapittaa)
    if category:
        pool = [C for C in pool if _meta(C).get("type") == category]

    if not pool:
        return []

    rarity_weights = rarity_weights or RARITY_WEIGHTS_DEFAULT

    results = []
    for _ in range(count):
        desired = roll_rarity(rarity_weights) if rarity_mode == "ROLL" else _normalize_rarity(rarity_mode)

        rarity_pool = [C for C in pool if _meta(C).get("rarity") == desired]
        use_pool = rarity_pool if rarity_pool else pool

        try:
            results.append(random.choice(use_pool)())
        except Exception:
            continue

    return results