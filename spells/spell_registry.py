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

# --- REGISTRY LIST ---
# Tähän kerätään kaikki luokat, jotka ovat onnistuneesti latautuneet
ALL_SPELLS = []

if Fireball: ALL_SPELLS.append(Fireball)
if MinorHeal: ALL_SPELLS.append(MinorHeal)
if LightningBolt: ALL_SPELLS.append(LightningBolt)

# Lisätään uudet
if Pyroblast: ALL_SPELLS.append(Pyroblast)
if LifeDrain: ALL_SPELLS.append(LifeDrain)

if SunRay: ALL_SPELLS.append(SunRay)

# Commander Spells (Ei lisätä ALL_SPELLS listaan, koska niitä ei osteta kaupasta)
# Mutta ne pitää olla saatavilla pelin logiikalle
COMMANDER_SPELLS = []
if VortexWarp: COMMANDER_SPELLS.append(VortexWarp)
if SeamCut: COMMANDER_SPELLS.append(SeamCut)


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
        except: pass
    return None