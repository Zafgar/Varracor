import random

# --- IMPORT SPELLS ---
# Käytetään try-exceptiä, jotta peli ei kaadu, jos jokin tiedosto puuttuu.

try:
    from spells.lvl_1.fireball import Fireball
except ImportError:
    Fireball = None

try:
    from spells.lvl_1.heal import MinorHeal
except ImportError:
    # print("MinorHeal not found yet") 
    MinorHeal = None

try:
    from spells.lvl_1.lightning import LightningBolt
except ImportError:
    LightningBolt = None

# --- LEVEL 2 SPELLS ---
try:
    from spells.lvl_2.pyroblast import Pyroblast
except ImportError:
    Pyroblast = None

try:
    from spells.lvl_2.life_drain import LifeDrain
except ImportError:
    LifeDrain = None

# --- LEVEL 8 SPELLS ---
try:
    from spells.lvl_8.sun_ray import SunRay
except ImportError:
    SunRay = None

# --- COMMANDER SPELLS ---
try:
    from spells.commander.vortex_warp import VortexWarp
except ImportError:
    VortexWarp = None

try:
    from spells.commander.seam_cut import SeamCut
except ImportError:
    SeamCut = None

# --- SCHOOL SPELLS (Necromancy / Holy / Druidism) ---
# Erikoiskoulujen loitsut: eivät kuulu Prismin (Pure) satunnaispooliin, vaan
# ostetaan kyseisen koulun kautta kun Commander on avannut sen. Käyttö vaatii
# hahmolta oikean suunnan taitopuussa (tuleva kytkentä).
try:
    from spells.necro.raise_skeleton import RaiseSkeleton
except ImportError:
    RaiseSkeleton = None

try:
    from spells.holy.smite import Smite
except ImportError:
    Smite = None

try:
    from spells.druid.regrowth import Regrowth
except ImportError:
    Regrowth = None

# --- REGISTRY LIST ---
# Tähän kerätään kaikki luokat, jotka ovat onnistuneesti latautuneet
ALL_SPELLS = []

if Fireball: ALL_SPELLS.append(Fireball)
if MinorHeal: ALL_SPELLS.append(MinorHeal)
if LightningBolt: ALL_SPELLS.append(LightningBolt)

# Lisätään uudet
if Pyroblast: ALL_SPELLS.append(Pyroblast)
if LifeDrain: ALL_SPELLS.append(LifeDrain)

# HUOM: Sun Ray EI enää Prismin (Pure) poolissa - aurinko/valo on Holy-teema.
# Se tarjotaan Radiant Synodin (holy) kautta, ks. get_catalog_school_spells.

# Commander Spells (Ei lisätä ALL_SPELLS listaan, koska niitä ei osteta kaupasta)
# Mutta ne pitää olla saatavilla pelin logiikalle
COMMANDER_SPELLS = []
if VortexWarp: COMMANDER_SPELLS.append(VortexWarp)
if SeamCut: COMMANDER_SPELLS.append(SeamCut)

# Koulukohtaiset loitsut (ostetaan koulusta, ei Prismin satunnaispoolista)
SCHOOL_SPELLS = {"necromancy": [], "holy": [], "druidism": []}
if RaiseSkeleton: SCHOOL_SPELLS["necromancy"].append(RaiseSkeleton)
if Smite: SCHOOL_SPELLS["holy"].append(Smite)
if Regrowth: SCHOOL_SPELLS["druidism"].append(Regrowth)


def get_school_spells(school):
    """Palauttaa koulun entry-loitsuluokat (uudet instanssit luodaan
    tarvittaessa)."""
    return list(SCHOOL_SPELLS.get(school, []))


# --- TIER-KATALOGI (data-vetoiset loitsut, pari per tier) ---
def get_catalog_spells():
    """Kaikki tier-katalogin loitsut uusina TieredSpell-olioina."""
    try:
        from spells.catalog import all_catalog_spells
        return all_catalog_spells()
    except Exception:
        return []


def get_catalog_school_spells(school):
    """Katalogin loitsut annetulle koululle (esim. 'holy'). Sun Ray
    (channel) liitetään Holyyn tässä."""
    try:
        from spells.catalog import catalog_spells_for_school
        out = catalog_spells_for_school(school)
    except Exception:
        out = []
    if school == "holy" and SunRay is not None:
        out.append(SunRay())
    return out


def get_pure_catalog_spells():
    """Prismin (Pure) katalogiloitsut - ostettavissa heti magic shopista."""
    return [s for s in get_catalog_spells() if getattr(s, "school", "") == "pure"]


def get_spell_shop_items(count=3):
    """
    Palauttaa listan satunnaisia loitsuja kauppaan.
    Luo uudet instanssit (eli uudet oliot) joka kerta.
    """
    shop_list = []
    
    # Jos yhtään loitsua ei ole ladattu, palautetaan tyhjä lista
    if not ALL_SPELLS: 
        return []

    for _ in range(count):
        # 1. Valitaan satunnainen loitsuluokka
        SpellClass = random.choice(ALL_SPELLS)
        
        # 2. Luodaan siitä olio (kutsuu __init__:iä)
        new_spell = SpellClass()
        
        # 3. Lisätään listaan
        shop_list.append(new_spell)
        
    return shop_list

def get_all_spells_for_shop():
    """Palauttaa yhden kappaleen jokaista loitsua kauppaan (Magic Menu)."""
    shop_list = []
    for SpellClass in ALL_SPELLS:
        shop_list.append(SpellClass())
    return shop_list

def get_spell_by_name(name):
    # Yksinkertainen haku luokan nimellä
    all_known = ALL_SPELLS + COMMANDER_SPELLS
    for spell_cls in all_known:
        try:
            if spell_cls.__name__ == name:
                return spell_cls
        except Exception: pass
    return None