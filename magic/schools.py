# magic/schools.py
"""
Varrakorin magiajarjestelma - koulukunnat ja tasot.

Taikuus on yleisesti tunnettu, mutta sen hallinta on harvinaista: se vaatii
kuria, harjoitusta ja kestavyytta. Loitsiminen ei ole ilmaista - se aiheuttaa
"arcane strainia" (fyysista ja henkista kuormitusta). Loitsut jakautuvat
kahdeksaan voimatasoon ja viiteen viralliseen koulukuntaan; kuudes muoto
(Abyssal Weave) on vain paahenkilon Vortex-taika.

Tasot 1-3 opetellaan neutraalissa Pure Magic -koulussa; tason 3 yli eteneminen
erikoiskouluun vaatii Realm Reputationia kyseista koulua tukevassa valtakunnassa.
"""

# --- LOITSUTASOT (Spell Tiers 1-8) ---
SPELL_TIERS = {
    1: "Apprentice",   # Perusselviytyminen: kipinat, pieni parannus
    2: "Adept",        # Taistelukelpoinen perustaso
    3: "Disciple",     # Kouluspesifi, vaatii erikoistumisen
    4: "Specialist",   # Ammattisoturin voimataso
    5: "Veteran",      # Sankaritaso, voimakkaita ja resurssivaativia
    6: "Elite",        # Valtakunnan tason resurssi, poliittisesti kontrolloitu
    7: "Master",       # Legendaarisia taitoja (laajat alueelliset rituaalit)
    8: "Grand",        # Maailmaa muuttavia, usein kiellettyja "endgame"-rituaaleja
}

# --- LOITSINTATAVAT ---
CAST_TYPES = ("instant", "channel", "ritual")

# --- KOULUKUNNAT ---
# color = koulun VFX-perusvari (koodipiirretyt efektit)
SCHOOLS = {
    "pure": {
        "name": "Pure Magic",
        "org": "The Prism Collegium",
        "leader": "Grand Magister Lysandra Voss",
        "seat": "Prismhall (Highstone)",
        "faction": None,
        "character": "Raakaa perusfysiikkaa: manan muoto, kanavointi ja vakaus "
                     "ilman poliittista ideologiaa.",
        "color": (120, 160, 255),   # kirkas sininen
        "free_tiers": (1, 2, 3),    # kaikille avoin tasoille 1-3
    },
    "holy": {
        "name": "Holy Magic",
        "org": "The Radiant Synod",
        "leader": "High Hierophant Caldor Aurelian",
        "seat": "Crownhold",
        "faction": "crown_dominion",
        "character": "Valoon, moraalilakiin ja puhdistukseen sidottu; magia "
                     "ilman kuria synnyttaa hirvioita.",
        "color": (255, 232, 150),   # kultainen valo
    },
    "necromancy": {
        "name": "Necromancy",
        "org": "The Ashen Ossuary",
        "leader": "Grand Mortarch Zharok the Quiet",
        "seat": "Bonewind Necropolis (Kharak)",
        "faction": "horned_throne",
        "character": "Kuoleman mekaniikan ymmartamista: sielusidoksia ja "
                     "levottomien hallintaa. Ei suoraan pahaa - rajatiede.",
        "color": (150, 90, 190),    # kalmanvioletti
    },
    "druidism": {
        "name": "Druidism",
        "org": "The Verdant Covenant",
        "leader": "Grand Druid Maelis Rootspeaker",
        "seat": "Wyrdwood",
        "faction": "lupine_wardens",
        "character": "Sopimuksia elavan maan, petojen ja vuodenaikojen kanssa - "
                     "ei pelkkaa taikuutta.",
        "color": (110, 200, 110),   # metsanvihrea
    },
    "manipulation": {
        "name": "Manipulation",
        "org": "The Argent Veil",
        "leader": "Veilmaster Cassian Merrow",
        "seat": "Mirror Court",
        "faction": "crown_dominion",
        "character": "Mielen, tunteiden ja havaintojen ohjaus seka illuusiot - "
                     "diplomatian ja vastatiedustelun hiljainen ase.",
        "color": (210, 170, 235),   # elohopeanvioletti
    },
    # --- KUUDES MUOTO: vain paahenkilo (Commander) ---
    "abyssal": {
        "name": "Abyssal Weave",
        "org": "(Vortexin oma logiikka)",
        "leader": "The Commander",
        "seat": "-",
        "faction": None,
        "character": "Ei perinteisia elementteja vaan tilan, siteiden, ajan ja "
                     "korruption manipulointia. Paahenkilo on elava ankkuri.",
        "color": (150, 60, 220),    # vortex-purppura
        "hero_only": True,
        "trees": {
            "anchoring": "Vakauttaa: estaa vihollisten liikkeet ja teleportit.",
            "severing": "Katkaisee Vortexin siteet: purkaa kilpia, poistaa kutsutut.",
            "echoing": "Aika ja varjot: toistaa iskuja tai kelaa aikaa taaksepain.",
            "warping": "Vaantaa tilaa ja liikeratoja ilman teleportaatiota.",
            "taint": "Siirtaa, puhdistaa ja muuttaa Vortex-korruptiota voimaksi.",
        },
    },
}


def school_color(school_key, default=(140, 150, 220)):
    return SCHOOLS.get(school_key, {}).get("color", default)


def tier_name(tier):
    return SPELL_TIERS.get(int(tier), f"Tier {tier}")


def is_hero_only(school_key):
    return bool(SCHOOLS.get(school_key, {}).get("hero_only", False))
