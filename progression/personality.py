# progression/personality.py
"""
Gladiaattorien luonne- ja taustajärjestelmä.

Jokainen rekrytoitava yksikkö saa:
  - personality: arkkityyppi (vaikuttaa dialogiin ja äänensävyyn)
  - origin: mistä hän tuli Muckfordiin (taustatarina)

Dialogi muuttuu kolmen akselin mukaan:
  - relationship: suhde pelaajaan (npc_state[...]["relationship"])
  - deeds: gladiaattorin urotyöt (killit, taistelut, taso)
  - progression: pelaajan maine ja tier

Käytä get_line(personality, category, rel_tier) rivien hakuun.
"""
import random

# =========================================================
# LUONNEARKKITYYPIT
# =========================================================
PERSONALITIES = {
    "grizzled": {
        "name": "Grizzled",
        "desc": "Vanha veteraani; vähäpuheinen, ei hätkähdä mistään.",
        "tone": "gruff",
    },
    "hothead": {
        "name": "Hothead",
        "desc": "Äkkipikainen ja aggressiivinen; haluaa taistella heti.",
        "tone": "aggressive",
    },
    "timid": {
        "name": "Timid",
        "desc": "Arka ja epävarma; tarvitsee rohkaisua.",
        "tone": "meek",
    },
    "arrogant": {
        "name": "Arrogant",
        "desc": "Ylimielinen; pitää itseään parhaana.",
        "tone": "proud",
    },
    "loyal": {
        "name": "Loyal",
        "desc": "Uskollinen ja luotettava; seisoo tiiminsä takana.",
        "tone": "warm",
    },
    "greedy": {
        "name": "Greedy",
        "desc": "Rahanahne; kaikki on kauppaa.",
        "tone": "greedy",
    },
}

# Rotukohtaiset painotukset luonteen arvontaan
RACE_WEIGHTS = {
    "Orc":    {"hothead": 3, "grizzled": 2, "loyal": 1},
    "Goblin": {"greedy": 3, "timid": 2, "hothead": 1},
    "Elf":    {"arrogant": 3, "grizzled": 1, "loyal": 1},
    "Dwarf":  {"grizzled": 3, "loyal": 2, "greedy": 1},
    "Human":  {"loyal": 2, "hothead": 1, "arrogant": 1, "greedy": 1, "grizzled": 1},
}

# Taustatarinat (mistä gladiaattori tuli)
ORIGINS = [
    "Debtor",        # velkavankeudesta areenalle
    "Deserter",      # karannut sotilas
    "Farmhand",      # maatilalta, nälän ajamana
    "Orphan",        # kadun kasvatti
    "Exile",         # karkotettu kotoaan
    "Sellsword",     # entinen palkkasoturi
    "Pit-born",      # syntynyt areenan liepeillä
]

ORIGIN_DESC = {
    "Debtor": "Velkavankeus toi areenalle - taistelee vapautensa puolesta.",
    "Deserter": "Karkasi rivistä; areena on parempi kuin hirsipuu.",
    "Farmhand": "Nälkä ajoi mullalta miekan varteen.",
    "Orphan": "Kadun kasvatti, jolla ei ole muuta kuin nyrkit.",
    "Exile": "Karkotettu kotoaan; ei tietä takaisin.",
    "Sellsword": "Entinen palkkasoturi, joka etsii vakaampaa palkkaa.",
    "Pit-born": "Syntyi areenan varjossa; ei tunne muuta elämää.",
}


def assign_personality(race_name, rng=random):
    """Arpoo rodulle sopivan luonteen ja taustan."""
    weights = RACE_WEIGHTS.get(race_name, {p: 1 for p in PERSONALITIES})
    ids = list(weights.keys())
    w = list(weights.values())
    personality = rng.choices(ids, weights=w, k=1)[0]
    origin = rng.choice(ORIGINS)
    return personality, origin


def relationship_tier(rel):
    """Muuntaa numeerisen suhteen tasoksi: cold/neutral/warm/devoted."""
    if rel < -20:
        return "cold"
    if rel < 20:
        return "neutral"
    if rel < 60:
        return "warm"
    return "devoted"


# =========================================================
# DIALOGIRIVIT: personality -> category -> rel_tier -> [rivit]
# category: greeting | banter | on_hire | pep_talk
# =========================================================
LINES = {
    "grizzled": {
        "greeting": {
            "cold": ["Hmph. Still here, are you?"],
            "neutral": ["What is it, Commander? Say it plain."],
            "warm": ["Commander. Good to see you upright."],
            "devoted": ["I've followed worse into worse places. You'll do."],
        },
        "banter": {
            "neutral": ["Been fighting since before you could walk. It never gets easier.",
                        "Sharpen your blade, count your coin, don't trust the crowd."],
            "warm": ["We've bled in the same mud. That means something.",
                     "You've got a steady hand. Rare in this pit."],
        },
    },
    "hothead": {
        "greeting": {
            "cold": ["You again? Put me in a fight or leave me be."],
            "neutral": ["When do we fight? I'm rotting standing here."],
            "warm": ["Commander! Point me at something and I'll wreck it."],
            "devoted": ["For you? I'd charge the Rat King bare-handed."],
        },
        "banter": {
            "neutral": ["Talk is cheap. Blood is the only currency I trust.",
                        "Every day without a fight is a day wasted."],
            "warm": ["Stick with me and we'll carve our names into this circuit.",
                     "You get it. Hit first, hit hard, hit again."],
        },
    },
    "timid": {
        "greeting": {
            "cold": ["Please... don't send me out there today. Not today."],
            "neutral": ["Oh - Commander. Do you... need something from me?"],
            "warm": ["Commander! I - I've been practicing, like you said."],
            "devoted": ["I was nothing before you found me. I won't let you down."],
        },
        "banter": {
            "neutral": ["The crowd scares me more than the blades, honestly.",
                        "Do you think I'm getting better? Be honest."],
            "warm": ["I actually landed a hit last match. Did you see?",
                     "With you watching my back, maybe I can do this."],
        },
    },
    "arrogant": {
        "greeting": {
            "cold": ["I carry this team. Try to remember that."],
            "neutral": ["Yes? Make it worth my time."],
            "warm": ["Ah, my Commander. Wise of you to consult the best."],
            "devoted": ["Together we are unmatched. Naturally, I do the heavy lifting."],
        },
        "banter": {
            "neutral": ["The others are adequate. I am exceptional.",
                        "When they cheer, they cheer for me. Never forget it."],
            "warm": ["You have taste, Commander. You built the team around me.",
                     "Let the rabble swing wildly. I fight with precision."],
        },
    },
    "loyal": {
        "greeting": {
            "cold": ["I'm still with you. But the others are talking."],
            "neutral": ["At your service, Commander. What's the plan?"],
            "warm": ["Good to see you. The squad's holding together."],
            "devoted": ["Wherever you lead, I follow. To the Vortex if it comes to it."],
        },
        "banter": {
            "neutral": ["A team is only as strong as its trust. I trust you.",
                        "I keep an eye on the rookies. Somebody has to."],
            "warm": ["We're more than fighters now. We're a crew.",
                     "You brought us this far. I won't forget it."],
        },
    },
    "greedy": {
        "greeting": {
            "cold": ["My cut's been light lately, Commander. Fix that."],
            "neutral": ["Commander. Let's talk numbers, shall we?"],
            "warm": ["Business is good! Keep the purses full and I'm yours."],
            "devoted": ["You pay fair and you pay on time. That's loyalty enough for me."],
        },
        "banter": {
            "neutral": ["Every scar's got a price. Mine are expensive.",
                        "Glory doesn't buy ale. Gold does."],
            "warm": ["We win, we get paid, everyone's happy. Simple.",
                     "Stick with me and we'll both retire rich - if we survive."],
        },
    },
}


def get_line(personality, category, rel_tier, rng=random):
    """Palauttaa satunnaisen dialogirivin. Fallback neutraaliin tasoon."""
    pdata = LINES.get(personality, LINES["grizzled"])
    cat = pdata.get(category, {})
    lines = cat.get(rel_tier) or cat.get("neutral") or ["..."]
    return rng.choice(lines)


def deeds_summary(unit):
    """Lyhyt kuvaus gladiaattorin urotöistä statsien perusteella."""
    kills = int(unit.stats.get("kills", 0)) if hasattr(unit, "stats") else 0
    level = getattr(unit, "level", 1)
    if level >= 8 or kills >= 30:
        return "a hardened veteran of the sands"
    if level >= 4 or kills >= 10:
        return "a proven fighter with real kills to their name"
    if kills >= 1:
        return "blooded, but still hungry"
    return "green - not a single arena kill yet"
