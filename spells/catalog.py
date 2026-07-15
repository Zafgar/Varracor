# spells/catalog.py
"""Tier-loitsujen katalogi: pari loitsua per tier, jaettuna kouluihin.
Numerot johdetaan tier-perustasta (spell_scaling); tässä määritellään vain
identiteetti (nimi, koulu, arkkityyppi, vahinkotyyppi, kantama) ja flavor.

Ostettavat kaupasta kun koulu on auki (pure heti). Käyttö vaatii hahmolta
riittävän spell-tierin taitopuussa (tuleva kytkentä)."""

from spells.tiered_spell import TieredSpell

# id, name, tier, school, archetype, damage_type, [range/radius], flavor
CATALOG = [
    # --- Tier 1 ---
    {"id": "arcane_dart", "name": "Arcane Dart", "tier": 1, "school": "pure",
     "archetype": "nuke", "damage_type": "Arcane", "range": 380,
     "flavor": "The first bolt every apprentice learns: raw Weave, shaped "
               "into a dart and flung. Cheap, quick, reliable."},
    {"id": "ember", "name": "Ember", "tier": 1, "school": "pure",
     "archetype": "dot", "damage_type": "Fire", "range": 350,
     "flavor": "A pinch of coaxed flame that clings and smoulders. Weak on "
               "impact, but the burn does the real work."},

    # --- Tier 2 ---
    {"id": "frost_shard", "name": "Frost Shard", "tier": 2, "school": "pure",
     "archetype": "nuke", "damage_type": "Frost", "range": 400,
     "flavor": "A splinter of hard-frozen air. Bites deeper than a dart and "
               "leaves a cold ache in the wound."},
    {"id": "toxic_bloom", "name": "Toxic Bloom", "tier": 2, "school": "druidism",
     "archetype": "dot", "damage_type": "Poison", "range": 360,
     "flavor": "A bursting spore-pod from the deep marsh. The petals rot "
               "flesh long after they land."},

    # --- Tier 3 ---
    {"id": "flame_wave", "name": "Flame Wave", "tier": 3, "school": "pure",
     "archetype": "aoe", "damage_type": "Fire", "radius": 95,
     "flavor": "A rolling sheet of fire that breaks over a crowd. The first "
               "spell worth its mana against a pack."},
    {"id": "hallowed_bolt", "name": "Hallowed Bolt", "tier": 3, "school": "holy",
     "archetype": "nuke", "damage_type": "Holy", "range": 430,
     "flavor": "A lance of blessed light from the Radiant Synod. It sears "
               "the living and scours the undead."},
    {"id": "counterspell", "name": "Counterspell", "tier": 3, "school": "pure",
     "archetype": "counter", "damage_type": "Arcane", "range": 460,
     "flavor": "A sharp word of unmaking. Snuffs out an enemy spell mid-cast "
               "- the duelist's art of the Prism Collegium."},

    # --- Tier 4 ---
    {"id": "storm_call", "name": "Storm Call", "tier": 4, "school": "pure",
     "archetype": "aoe", "damage_type": "Lightning", "radius": 110,
     "flavor": "You call the sky down onto a point. Thunder answers, and "
               "everything nearby is thrown into the arc."},
    {"id": "grave_touch", "name": "Grave Touch", "tier": 4, "school": "necromancy",
     "archetype": "dot", "damage_type": "Necrotic", "range": 380,
     "flavor": "A finger of the grave's cold. What it marks begins to die "
               "slowly, from the inside out."},

    # --- Tier 5 ---
    {"id": "glacial_spike", "name": "Glacial Spike", "tier": 5, "school": "pure",
     "archetype": "nuke", "damage_type": "Frost", "range": 460,
     "flavor": "A spear of ancient ice, driven clean through a single foe. "
               "Heavy mana, heavier impact."},
    {"id": "wildgrowth", "name": "Wildgrowth", "tier": 5, "school": "druidism",
     "archetype": "dot", "damage_type": "Nature", "range": 420,
     "flavor": "Ravenous vines erupt from the target, feeding on it as they "
               "grow. Nature takes what it is owed."},

    # --- Tier 6 ---
    {"id": "void_bolt", "name": "Void Bolt", "tier": 6, "school": "pure",
     "archetype": "nuke", "damage_type": "Arcane", "range": 500,
     "flavor": "A dart of unmade space. It does not burn or freeze — it "
               "simply removes what it touches."},
    {"id": "dawnburst", "name": "Dawnburst", "tier": 6, "school": "holy",
     "archetype": "aoe", "damage_type": "Holy", "radius": 120,
     "flavor": "A sunrise in miniature. Radiant fire blooms outward, "
               "cleansing a whole knot of enemies at once."},

    # --- Tier 7 ---
    {"id": "cataclysm", "name": "Cataclysm", "tier": 7, "school": "pure",
     "archetype": "aoe", "damage_type": "Fire", "radius": 140,
     "flavor": "The sky splits and molten rock rains down. Few things stand "
               "in the crater it leaves behind."},
    {"id": "soul_harvest", "name": "Soul Harvest", "tier": 7, "school": "necromancy",
     "archetype": "nuke", "damage_type": "Necrotic", "range": 480,
     "flavor": "A scythe of pure death magic that reaps a single soul in one "
               "devastating stroke."},

    # --- Tier 8 ---
    {"id": "sun_flare", "name": "Sun Flare", "tier": 8, "school": "holy",
     "archetype": "aoe", "damage_type": "Holy", "radius": 150,
     "flavor": "A fragment of a true sun, called down by the Radiant Synod. "
               "It immolates everything in a blinding sphere of light."},
    {"id": "oblivion", "name": "Oblivion", "tier": 8, "school": "pure",
     "archetype": "nuke", "damage_type": "Arcane", "range": 560,
     "flavor": "The Prism Collegium's forbidden capstone: a single point of "
               "annihilation aimed at one unlucky target."},
]

_BY_ID = {s["id"]: s for s in CATALOG}


def all_catalog_spells():
    """Uudet TieredSpell-oliot koko katalogista."""
    return [TieredSpell(s) for s in CATALOG]


def catalog_spells_for_school(school):
    return [TieredSpell(s) for s in CATALOG if s.get("school") == school]


def make_catalog_spell(spell_id):
    spec = _BY_ID.get(spell_id)
    return TieredSpell(spec) if spec else None
