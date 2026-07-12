# magic/progression.py
"""
Magian eteneminen: mitka koulukunnat ovat pelaajalle auki.

Perusmagia (Pure) aukeaa heti. Muut koulut ovat omia quest-linjojaan: pelaajan
on paastava kyseiseen kohteeseen (magiaa harjoitetaan siella) ja ansaittava
paasy koulun pitajalta - yleensa maineella (Realm Reputation) ja
materiaalikomponenteilla. Cheat mode avaa kaikki testausta varten.

Abyssal Weave (heron Vortex-taika) ei kuulu naihin kouluihin: se aukeaa lore-
tapahtumista (Tia Muira -opit), ei koulun kautta.
"""

# Koulun avaamisen vaatimukset. resource = (materiaali, maara).
# rep_faction viittaa reputation/-jarjestelman fraktioon. keeper/location ovat
# lore-vihjeita quest-linjalle.
SCHOOL_UNLOCK = {
    "pure": {
        "default": True,
        "keeper": "Grand Magister Lysandra Voss",
        "location": "Prismhall (Highstone)",
        "resource": None,
        "rep_faction": None,
    },
    "necromancy": {
        "default": False,
        "keeper": "Grand Mortarch Zharok the Quiet",
        "location": "Bonewind Necropolis (Kharak)",
        "resource": ("Spirit Essence", 5),
        "rep_faction": "ashen",
    },
    "holy": {
        "default": False,
        "keeper": "High Hierophant Caldor Aurelian",
        "location": "Crownhold",
        "resource": ("Blessed Incense", 5),
        "rep_faction": "radiant",
    },
    "druidism": {
        "default": False,
        "keeper": "Grand Druid Maelis Rootspeaker",
        "location": "Wyrdwood",
        "resource": ("Wyrdwood Sap", 5),
        "rep_faction": "lupine",
    },
    "manipulation": {
        "default": False,
        "keeper": "Veilmaster Cassian Merrow",
        "location": "Mirror Court",
        "resource": ("Silvered Mirror", 3),
        "rep_faction": "veil",
    },
}

# Abyssal Weave -taitopuut (aukeavat lore-tapahtumista, ks. Vortex-mentor).
ABYSSAL_TREES = ("anchoring", "severing", "echoing", "warping", "taint")

# UI-idien mappays kanonisiin koulukunta-avaimiin (magic_school_menu kayttaa lyhyita).
MENU_ID_TO_SCHOOL = {
    "pure": "pure", "holy": "holy", "necro": "necromancy",
    "druid": "druidism", "manip": "manipulation",
}


def default_schools():
    return [k for k, v in SCHOOL_UNLOCK.items() if v.get("default")]


def unlock_requirement_text(school):
    req = SCHOOL_UNLOCK.get(school, {})
    parts = []
    res = req.get("resource")
    if res:
        parts.append(f"{res[1]}x {res[0]}")
    if req.get("rep_faction"):
        parts.append(f"{req['rep_faction']} standing")
    return " + ".join(parts) if parts else "Open to all"
