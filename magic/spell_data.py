# magic/spell_data.py
"""
SPELL_LIBRARY - data-driven loitsukirjasto. Yksi generinen LibrarySpell-luokka
lukee nama (ks. magic/library_spell.py), joten satoja loitsuja ei tarvitse
kirjoittaa erillisina luokkina.

Kentat:
  school   : "pure"/"holy"/"necromancy"/"druidism"/"manipulation"/"abyssal"
  tier     : 1-8 (Apprentice..Grand)
  cast     : "instant"/"channel"/"ritual"
  kind     : "damage" | "heal" | "debuff" (debuff = vahinko + status)
  mana     : manakustannus
  strain   : arcane strain (fyysinen/henkinen kuormitus)
  cooldown : framea
  range    : kantama px
  power    : vahinko tai parannus
  scaling  : {"INT": kerroin}
  status   : (type, duration, dmg) - debuffille
  desc     : kuvaus
"""

# --- Tasapainokaavat (kaytetaan authoritaessa / defaultteina) ---
def dmg_for(t):   return int(10 * (t ** 1.4))      # T1~10 T3~46 T5~95 T8~228
def heal_for(t):  return int(24 * (t ** 1.15))     # T1~24 T3~83 T6~185
def mana_for(t):  return 6 + t * 5
def strain_for(t):return 3 + t * 4                 # korkeat tasot uuvuttavat
def cd_for(t):    return 70 + t * 18
def rng_for(t):   return 280 + t * 12


def _dmg(name, school, tier, status=None, cast="instant", power=None, desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast, "kind": "damage",
        "mana": mana_for(tier), "strain": strain_for(tier), "cooldown": cd_for(tier),
        "range": rng_for(tier), "power": power or dmg_for(tier),
        "scaling": {"INT": 1.0 + 0.1 * tier}, "status": status, "desc": desc,
        "rarity": "Common" if tier <= 2 else ("Rare" if tier <= 5 else "Epic"),
        "cost": 40 * tier,
    })


def _heal(name, school, tier, cast="instant", power=None, desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast, "kind": "heal",
        "mana": mana_for(tier) + 4, "strain": strain_for(tier), "cooldown": cd_for(tier) + 40,
        "range": rng_for(tier) - 40, "power": power or heal_for(tier),
        "scaling": {"INT": 0.8 + 0.1 * tier}, "desc": desc,
        "rarity": "Common" if tier <= 2 else ("Rare" if tier <= 5 else "Epic"),
        "cost": 45 * tier,
    })


# =====================================================================
# KIRJASTO
# =====================================================================
SPELL_LIBRARY = dict([

    # --- PURE MAGIC (The Prism Collegium) - neutraali runko ---
    _dmg("Spark Bolt", "pure", 1, desc="A simple bolt of raw mana. Cheap and reliable."),
    _dmg("Arcane Dart", "pure", 2, desc="A focused dart of force."),
    _dmg("Force Pulse", "pure", 3, status=("Slow", 90, 0), desc="A concussive wave that staggers."),
    _dmg("Mana Lance", "pure", 4, desc="A lance of condensed mana."),
    _dmg("Arcane Nova", "pure", 5, desc="A burst of pure arcane energy."),
    _dmg("Nullfield", "pure", 6, status=("Silence", 150, 0), desc="Collapses a foe's ability to channel."),
    _dmg("Starfall", "pure", 7, desc="Calls down a shard of the firmament."),
    _dmg("Prime Equation", "pure", 8, cast="ritual",
         desc="Briefly rewrites the local rules of magic. Priceless and perilous."),

    # --- HOLY MAGIC (The Radiant Synod) - valo ja parannus ---
    _heal("Light Mend", "holy", 1, desc="A basic mending light."),
    _dmg("Smite", "holy", 2, desc="A shaft of judging light."),
    _heal("Purify", "holy", 2, desc="Cleansing radiance that knits and cleanses."),
    _heal("Bless", "holy", 3, desc="A deeper healing benediction."),
    _dmg("Consecrate", "holy", 4, status=("Burn", 120, 6), desc="Holy fire that lingers."),
    _heal("Sanctify", "holy", 5, desc="A veteran's field-healing prayer."),
    _heal("Resurrection Seal", "holy", 6, cast="ritual",
          desc="An immensely costly rite that drags life back from the edge."),
    _dmg("Dawnbreak", "holy", 7, desc="The first light of a new dawn, weaponized."),
    _dmg("Judgment", "holy", 8, cast="ritual",
         desc="The Synod's final word: an area-scouring pillar of light."),
])
