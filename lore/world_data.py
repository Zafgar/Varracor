# lore/world_data.py
"""
Varracorin maailman kanoninen data pelikoodille.

Ihmisluettava versio: docs/LORE.md — pidä molemmat synkassa!
Käyttö esim.:
    from lore.world_data import ARENA_TIERS, get_tier_name
    ARENA_TIERS[0]["keeper"]  -> 'Bram "Mudhand" Carrow'
"""

# =========================================================
# VALTAKUNNAT
# =========================================================
KINGDOMS = {
    "crown_dominion": {
        "name": "The Crown Dominion",
        "race": "Human",
        "ruler": "King Alaric Vane",
        "capital": "Crownhold",
        "region": "West/Northwest",
        "themes": ["byrokratia", "verot ja tullit", "propaganda",
                   "resurssijahti Wyrdwoodissa"],
        "magic": ["Holy", "Manipulation"],
        "ruler_personality": ("Laskelmoiva ja petollinen; näkee Vortexin "
                              "mahdollisuutena keskittää valtaa."),
    },
    "horned_throne": {
        "name": "The Horned Throne of Kharak",
        "race": "Minotaur",
        "ruler": "King Tauron Stonehorn",
        "capital": "Kharak-Tor",
        "region": "South (The Sunscar Expanse)",
        "themes": ["kestävyys", "velvollisuus", "aavikkoreitit ja vesivarat"],
        "magic": ["Necromancy (valvottu)"],
        "ruler_personality": ("Temperamenttinen mutta kurinalainen veteraani; "
                              "suora puhe, pragmaattinen."),
    },
    "lupine_wardens": {
        "name": "The Lupine Wardens",
        "race": "Werewolf",
        "ruler": "King Fenric Greyfang",
        "capital": "Moonwatch",
        "region": "East/Northeast (The Wyrdwood)",
        "themes": ["metsän tasapaino", "Taint-korruption torjunta",
                   "resurssijahdin vastustus"],
        "magic": ["Druidism"],
        "ruler_personality": "Järkevä mutta armoton metsän suojelija.",
    },
    "highstone_sanctum": {
        "name": "Highstone Sanctum",
        "race": "Neutral",
        "ruler": "The Sanctified Titan, Arkon",
        "capital": "Highstone Sanctum",
        "region": "North (The Aegis Peaks)",
        "themes": ["areenajärjestelmän valvonta", "Mercy Charter",
                   "neutraali rintama Vortexia vastaan"],
        "magic": [],
        "ruler_personality": ("Ikivanha vuorenkokoinen titaani; ohjaa "
                              "sääntöjen ja protokollien kautta, ei käskien."),
    },
}

# =========================================================
# AREENATIERIT (0-5)
# HUOM: LeagueEnginen sisäinen tier alkaa 1:stä -> lore-tier = game_tier - 1
# =========================================================
ARENA_TIERS = {
    0: {
        "name": "The Rookie Dust Circuit",
        "keeper": 'Bram "Mudhand" Carrow',
        "keeper_race": "Dwarf",
        "hub": "Muckford",
        "arena": "Shanty Yard",
        "character": "Muta, velat ja epätoivoiset aloittelijat; halpa raha.",
    },
    1: {
        "name": "The Scrapring Circuit",
        "keeper": "Sera Quench",
        "keeper_race": "Human",
        "hub": "Rattlebridge",
        "arena": "The Scrapring",
        "character": ("Gladiaattoreista tehdään brändejä; ensimmäiset "
                      "sponsorisopimukset."),
    },
    2: {
        "name": "The Iron Circle Circuit",
        "keeper": 'Vessik "Coincroak" Lurrow',
        "keeper_race": "Frogfolk",
        "hub": "Giltgate",
        "arena": "The Iron Circle",
        "character": "Liike-elämän ja vedonlyönnin sydän; sopimuspaperit.",
    },
    3: {
        "name": "The Steel Arena Circuit",
        "keeper": "Lord Caelith Vaelor",
        "keeper_race": "High Elf",
        "hub": "Spirewatch",
        "arena": "The Steel Arena",
        "character": "Eliitin näyttämö: taito, eleganssi, strateginen kontrolli.",
    },
    4: {
        "name": "The Silver League Circuit",
        "keeper": "Hessa Ironhorn",
        "keeper_race": "Minotaur",
        "hub": "Kharak-Tor",
        "arena": "The Silver League",
        "character": ("Todellinen kestävyys ja kunnia sotaa varten; "
                      "viimeinen portti ennen huippua."),
    },
    5: {
        "name": "The Golden League",
        "keeper": "Seneschal Maelor Vale",
        "keeper_race": "Human",
        "hub": "Highstone Sanctum",
        "arena": "The Golden League",
        "character": ("Yksi myyttinen areena; valmistautuminen Vortexin "
                      "syvimpiin tehtäviin. Arkonin alaisuudessa."),
    },
}

# HUOM: Tier 0:n alkiot ovat (nimi, manageri, kuvaus) -kolmikoita;
# muut tierit toistaiseksi (nimi, kuvaus) -pareja. get_tier_teams()
# normalisoi molemmat dict-muotoon.
ARENA_TEAMS = {
    0: [
        ("Shanty Yard Saints", "Mara Pikestring",
         "Muckfordin työjuhta ja katsomon suosikki; aina paikalla, ottaa "
         "kaikki pikkukeikat. Epäillään väärien boss-havaintojen myymisestä."),
        ("Muckford Ratcatchers", "Old Rinna 'Net'",
         "Rottaongelmien erikoistiimi; Hamon vahvistuspartio viemäreissä. "
         "Epäillään rottamyrkyn laittomasta myynnistä siviileille."),
        ("The Unclaimed Five", "'No-Name' Pell",
         "Tuntemattomista taustoista; tekee vain riskikeikkoja. Bram inhoaa "
         "heitä - sotkevat järjestystä, epäillään rötöksistä."),
        ("The Ragged Lanterns", "Toma Vale",
         "Heartlandsin pelastuskeikat; Saint Lumen Field Hospice tukee, "
         "koska tuovat kadonneita elossa takaisin."),
        ("Croak & Dagger", "-",
         "Sammakko-humanoidien tiimi: ansojen purku, tiedustelu ja "
         "tiedonmyynti. Laittoman tarkkoja Vortex-karttoja."),
        ("The Siltbound", "-",
         "Suo- ja mutabossien jäljittäjät; jatkuvat temppelilaskut "
         "loistartunnoista ja infektioista."),
    ],
    1: [
        ("Rattlebridge Runners", "Kurinalainen ja puhdas; helppo markkinoida"),
        ("Bolt Cage Bruisers", "Raaka häkkitappelijan voima"),
        ("Timbercross Wardens", "Metsän rajaturva"),
    ],
    2: [
        ("Giltgate Goldclaws", "Tehokas show-tiimi; rahanpesuepäilyt"),
        ("Ledgerford Litigators", "Voittaa sääntökikkailulla"),
        ("Coinharbor Corsairs", "Satamien meribossit"),
    ],
    3: [
        ("Spirewatch Blades", "Kirurginen tarkkuus; pidetään ylimielisenä"),
        ("Moonwatch Shadowpack", "Ihmissudet ja druidit; Taint-puhdistus"),
    ],
    4: [
        ("Kharak-Tor Hammerguard", "Minotaurien murskaava etulinja"),
        ("Crownhold Lionhearts", "Kuninkaan propagandakasvo"),
        ("Bonewind Reclaimers", "Kuolemanrajan operaatiot"),
    ],
    5: [
        ("The Sanctum Five", "Highstonen erikoisjoukko S-tason uhkia vastaan"),
        ("Stoneblood Paragon", "Kharakin kirkkain kärki"),
        ("Moonbloom Sovereigns", "Puhdistusmestarien eliitti"),
    ],
}

# =========================================================
# MAGIAKOULUT
# =========================================================
MAGIC_SCHOOLS = {
    "pure": {
        "name": "The Prism Collegium",
        "magic": "Pure Magic",
        "leader": "Grand Magister Lysandra Voss",
        "character": "Neutraali perusmagian koulu.",
    },
    "holy": {
        "name": "The Radiant Synod",
        "magic": "Holy Magic",
        "leader": "High Hierophant Caldor Aurelian",
        "character": "Ihmisten puhtautta ja moraalilakia ajava; fanaattinen.",
    },
    "necromancy": {
        "name": "The Ashen Ossuary",
        "magic": "Necromancy",
        "leader": "Grand Mortarch Zharok the Quiet",
        "character": "Kuoleman mekaniikka; minotaurien suosima.",
    },
    "druidism": {
        "name": "The Verdant Covenant",
        "magic": "Druidism",
        "leader": "Grand Druid Maelis Rootspeaker",
        "character": "Luonnon tasapaino; ihmissusien sopimusverkosto.",
    },
    "manipulation": {
        "name": "The Argent Veil",
        "magic": "Manipulation",
        "leader": "Veilmaster Cassian Merrow",
        "character": 'Mielenhallinta ja diplomatia; ihmisten "hiljainen ase".',
    },
}

# =========================================================
# TEMPPELIVERKOSTOT (Mercy Charter)
# =========================================================
TEMPLE_NETWORKS = {
    "sunbound": {"name": "Sunbound Hospices", "faction": "crown_dominion",
                 "example": "Sunspire Infirmary", "style": "uskonnollinen"},
    "stoneblood": {"name": "Stoneblood Hospices", "faction": "horned_throne",
                   "style": "raadollinen ja kirurginen"},
    "moonbloom": {"name": "Moonbloom Sanctuaries", "faction": "lupine_wardens",
                  "style": "luontoon nojaava"},
}

# =========================================================
# RESURSSIT HARVINAISUUKSITTAIN
# Valuutat: SP (hopea) -> GP (kulta) -> PL (platina) -> HC (Highstone Crown)
# =========================================================
CURRENCIES = ["SP", "GP", "PL", "HC"]

RESOURCE_TIERS = {
    "Common": {
        "tiers": (0, 1), "currency": "SP",
        "resources": {
            "Scrap Iron": "Romurauta perusaseisiin",
            "Iron Ore": "Rautamalmi perusaseisiin",
            "Oakwood": "Tammi jousiin ja kilpiin",
            "Bitterleaf": "Yksinkertaiset parannusjuomat",
        },
    },
    "Uncommon": {
        "tiers": (1, 2), "currency": "GP",
        "resources": {
            "Blacksteel Ore": "Kestävä mustateräs",
            "Ironbark": "Panssarimainen puu Wyrdwoodista",
            "Direhide": "Nahka vaarallisimmilta pedoilta",
        },
    },
    "Rare": {
        "tiers": (3, 4), "currency": "GP",
        "resources": {
            "Stormsilver": "Resonoi taikuuden kanssa",
            "Moonwillow": "Kuutamossa kerättävä puu druidisauvoihin",
            "Trollbone Plating": "Regeneroivia ominaisuuksia haarniskoihin",
        },
    },
    "Very Rare": {
        "tiers": (4, 5), "currency": "PL",
        "resources": {
            "Void-Iron": "Louhitaan Vortexin reunoilta; torjuu Abyss-voimia",
            "Sun-Gold": "Kruunun kontrolloima pyhä metalli",
            "Drake Scale": "Antaa tulenkestävyyttä",
            "Abyssal Chitin": "Taint-korruptiota sietävä kuori",
            "Vortex Residue": "Riskialttiit taikajuomat",
        },
    },
    "Mythic": {
        "tiers": (5, 5), "currency": "HC",
        "resources": {
            "Heartcore Adamant": "Maailman kestävin materiaali; Vortexin ydin",
            "Echo Heart": "Suurbossien sydän; artefaktien ydin",
        },
    },
}

# =========================================================
# KAUPUNGIT
# =========================================================
CITIES = {
    "muckford": {
        "name": "Muckford", "region": "The Sundered Heartlands",
        "faction": None, "tier": 0,
        "role": ("Mudan, velan ja aloittelijoiden kaupunki; Shanty Yardin "
                 "koti ja pelin aloituspaikka."),
    },
    "crownhold": {
        "name": "Crownhold", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": None,
        "role": "Pääkaupunki; byrokratia ja propaganda.",
    },
    "rattlebridge": {
        "name": "Rattlebridge", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": 1,
        "role": "Siltakaupunki, logistiikkasolmu; The Scrapring.",
    },
    "rivet_row": {
        "name": "Rivet Row", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": 1,
        "role": "Teollisuuskaupunki (metallit); Bolt Cage -häkkimatsit.",
    },
    "giltgate": {
        "name": "Giltgate", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": 2,
        "role": "Kaupan ja vedonlyönnin keskus.",
    },
    "ledgerford": {
        "name": "Ledgerford", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": 2,
        "role": "Kirjanpitäjien, lakimiesten ja tullien kaupunki.",
    },
    "coinharbor": {
        "name": "Coinharbor", "region": "The Crown Dominion",
        "faction": "crown_dominion", "tier": 2,
        "role": "Satamakaupunki; merestä nousevien Vortex-uhkien torjunta.",
    },
    "kharak_tor": {
        "name": "Kharak-Tor", "region": "The Sunscar Expanse",
        "faction": "horned_throne", "tier": 4,
        "role": "Minotaurien pääkaupunki kalliotasangolla; sodan keskus.",
    },
    "saffron_oasis": {
        "name": "Saffron Oasis", "region": "The Sunscar Expanse",
        "faction": "horned_throne", "tier": 0,
        "role": "Keidas ja karavaanipysäkki; kestävyys ja vesi.",
    },
    "hornfall": {
        "name": "Hornfall", "region": "The Sunscar Expanse",
        "faction": "horned_throne", "tier": None,
        "role": "Kalliolinnoitus karavaanireitillä.",
    },
    "stonegrit": {
        "name": "Stonegrit", "region": "The Sunscar Expanse",
        "faction": "horned_throne", "tier": None,
        "role": "Kivilouhoskaupunki.",
    },
    "kestrel_way": {
        "name": "Caravanserai Kestrel-Way", "region": "The Sunscar Expanse",
        "faction": "horned_throne", "tier": None,
        "role": "Karavaanireittien pysähdyspaikka.",
    },
    "moonwatch": {
        "name": "Moonwatch", "region": "The Wyrdwood",
        "faction": "lupine_wardens", "tier": None,
        "role": "Ihmissusien pääkaupunki; druidien keskus.",
    },
    "vinehollow": {
        "name": "Vinehollow", "region": "The Wyrdwood",
        "faction": "lupine_wardens", "tier": 0,
        "role": "Viidakon ja suon raja; myrkyt ja vastalääkkeet.",
    },
    "timbercross": {
        "name": "Timbercross", "region": "The Wyrdwood",
        "faction": "lupine_wardens", "tier": 1,
        "role": "Puunhakkuukaupunki Wyrdwoodin rajalla.",
    },
    "elderroot_grove": {
        "name": "Elderroot Grove", "region": "The Wyrdwood",
        "faction": "lupine_wardens", "tier": None,
        "role": "Luonnon pyhin paikka; druidien päämaja.",
    },
    "highstone_sanctum": {
        "name": "Highstone Sanctum", "region": "The Aegis Peaks",
        "faction": "highstone_sanctum", "tier": 5,
        "role": "Neutraali katto; Golden League, Arkon, paras sairaanhoito.",
    },
    "spirewatch": {
        "name": "Spirewatch", "region": "The Aegis Peaks",
        "faction": "highstone_sanctum", "tier": 3,
        "role": "Duellihallit ja kristalliareenat.",
    },
    "windstep": {
        "name": "Windstep", "region": "The Aegis Peaks",
        "faction": "highstone_sanctum", "tier": 3,
        "role": "Tier 3 -areena-alueen kaupunki.",
    },
    "gleamhold": {
        "name": "Gleamhold", "region": "The Aegis Peaks",
        "faction": "highstone_sanctum", "tier": 3,
        "role": "Tier 3 -areena-alueen kaupunki.",
    },
    "ironwind_pass": {
        "name": "Ironwind Pass", "region": "The Aegis Peaks",
        "faction": "highstone_sanctum", "tier": 3,
        "role": "Vuoristosola; Tier 3 -areenaketjua.",
    },
}

# =========================================================
# AVAIN-NPC:T
# =========================================================
KEY_NPCS = {
    "hamo": {
        "name": "Hamo", "race": "Goblin", "role": "Bounty Broker",
        "description": ("Jakaa areenatiimeille palkkiotehtäviä Vortex-bossien "
                        "ja swarmien metsästämisestä. Tietokauppias: yhdistää "
                        "temppelien vammatiedot ja scouttien havainnot."),
    },
    "arkon": {
        "name": "The Sanctified Titan, Arkon", "race": "Titan",
        "role": "Areenajärjestelmän ja Mercy Charterin luoja",
        "description": "Highstone Sanctumin valvoja.",
    },
}

# =========================================================
# VORTEX
# =========================================================
VORTEX = {
    "name": "The Abyssal Vortex",
    "location": "The Sundered Heartlands (kartan keskus)",
    "opened": "3 vuotta sitten",
    "rings": ["Outer Shatterbelt", "...", "The Eye"],
    "spawns": ["Swarms (hirviöparvet)", "Abyssal Echoes (voimakkaat yksilöt)"],
    "corruption": "Taint",
    "effect": "Vääristää tilaa, aikaa ja mieltä.",
}


# =========================================================
# APUFUNKTIOT
# =========================================================
def get_tier_info(lore_tier):
    """Palauttaa areenatierin tiedot (0-5)."""
    return ARENA_TIERS.get(int(lore_tier))


def get_tier_name(lore_tier):
    info = get_tier_info(lore_tier)
    return info["name"] if info else f"Tier {lore_tier}"


def get_tier_keeper(lore_tier):
    info = get_tier_info(lore_tier)
    return info["keeper"] if info else "Unknown"


def game_tier_to_lore(game_tier):
    """LeagueEnginen tier alkaa 1:stä; loren tier 0:sta."""
    return max(0, min(5, int(game_tier) - 1))


# =========================================================
# MUCKFORDIN MARKKINAHINNAT (Tier 0, hopeatalous)
# =========================================================
MARKET_PRICES = {
    # Mitä kauppias maksaa pelaajan tavaroista
    "sell": {
        "Milk": 4, "Egg": 2, "Apple": 2, "Manure": 1,
        "Swamp Wood": 3, "Scrap Iron": 3, "Scrap": 2,
        "Rat Tail": 2, "Spirit Essence": 8, "Iron Ore": 3,
        "Coal": 2, "Iron Bar": 8, "Chipped Ruby": 40, "Stone": 1,
    },
    # Mitä pelaaja voi ostaa kojulta
    "buy": {
        "Empty Bucket": {"price": 5, "kind": "item", "class": "BucketEmpty"},
        "Weak Pickaxe": {"price": 12, "kind": "item", "class": "WeakPickaxe"},
        "Weak Health Potion": {"price": 30, "kind": "item", "class": "WeakHealthPotion"},
        "Apple": {"price": 4, "kind": "material"},
        "Egg": {"price": 4, "kind": "material"},
    },
}


# =========================================================
# TALOUS
# =========================================================
ECONOMY = {
    "currencies": {
        "SP": {"name": "Silver Piece", "value_in_sp": 1,
               "use": "Arki: ruoka, majoitus, halvat korjaukset (Tier 0-1)"},
        "GP": {"name": "Gold Piece", "value_in_sp": 100,
               "use": "Ammattilaistaso: terasvarusteet, taikajuomat, sepat"},
        "PL": {"name": "Platinum Piece", "value_in_sp": 10000,
               "use": "Eliitti: harvinaiset materiaalit, temppelioperaatiot"},
        "HC": {"name": "Highstone Crown", "value_in_sp": 1000000,
               "use": "Endgame: artefaktit, poliittinen valta"},
    },
    "cost_of_living": {
        "muckford_night": (8, 15, "SP"),
        "muckford_stew": (2, 8, "SP"),
        "giltgate_night": (1, 3, "GP"),
        "giltgate_meal": (1, 2, "GP"),
        "healing_potion": (25, 60, "SP"),
        "mana_draught": (1, 4, "GP"),
        "antidote": (1, 4, "GP"),
        "crude_sharpening": (5, 15, "SP"),
        "steel_armor_repair": (3, 10, "GP"),
        "stormsilver_work": (20, 60, "GP"),
        "temple_major_treatment": (0.2, 1.5, "PL"),
    },
    "regional_exports": {
        "crown_dominion": ["Iron", "Steel", "Parchment", "Archive Ink",
                           "Contracts (Ledgerford)"],
        "lupine_wardens": ["Ironbark", "Moonwillow", "Living Fiber",
                           "Herbs", "Moondew (mana)"],
        "horned_throne": ["Direhide", "Trollbone Plating", "Drake Scale",
                          "Water (Saffron Oasis)"],
        "highstone_sanctum": ["Official Seals", "Protocol Documents",
                              "Stormsilver", "Focus Crystal"],
        "vortex": ["Void-Iron", "Abyssal Chitin", "Vortex Residue"],
    },
    "engines": {
        "arena_business": ("Tier 0: rekisterointimaksut ja ruokakojut; "
                           "Tier 1-3: vedonlyonti, liput, sponsorit. "
                           "Sponsorit maksavat stipendia, voitto- ja "
                           "tavoitebonuksia; saavat mainosta ja valtaa."),
        "monster_economy": ("Hamo valittaa palkkioita: rottaparvi 1-4 GP, "
                            "iso bossi 0.1-0.4 PL, Vortex-kohde HC-tasoa. "
                            "Echo Shards/Hearts artefaktimateriaaleina."),
        "oath_of_debt": ("Velka ja palvelukset epavirallisena valuuttana. "
                         "Majatalonpitajat myyvat velkakirjoja eteenpain; "
                         "temppelit sitovat pelastetut Oath of Debt "
                         "-kirjoihin. Pelissa: Mardan 25 kullan alkuvelka."),
    },
    "bounty_ranges": {
        "swarm_cleanup": (1, 4, "GP"),
        "major_boss": (0.1, 0.4, "PL"),
        "vortex_target": (1, 10, "HC"),
    },
}


def get_tier_teams(lore_tier):
    """Palauttaa tierin tiimit normalisoituina dictteinä:
    {"name", "manager", "desc"}. Tukee sekä (nimi, kuvaus)- että
    (nimi, manageri, kuvaus) -muotoja."""
    out = []
    for entry in ARENA_TEAMS.get(int(lore_tier), []):
        if len(entry) == 3:
            name, manager, desc = entry
        else:
            name, desc = entry
            manager = None
        out.append({"name": name, "manager": manager, "desc": desc})
    return out


# =========================================================
# TIER 0 / MUCKFORD - PAIKALLISKAANON
# =========================================================
TIER0_CHARACTERS = {
    "bram_mudhand": {
        "name": 'Bram "Mudhand" Carrow', "race": "Dwarf",
        "role": ("Koko Tier 0 -verkoston manageri. Käytännöllinen selviytyjä: "
                 "likaiset arpiset kädet, nahkaesiliina. Pyörittää järjestelmän "
                 "sisääntuloporttia - rekisteröintimaksut ja velkakontrolli."),
    },
    "marda_shant": {
        "name": "Marda Shant", "race": "Human",
        "role": ("The Sunk Caskin pitäjä ja Shanty Consortiumin epävirallinen "
                 "velkakirjuri. Äkäinen, laskelmoiva; pieni nuija 'rauhoitteluun'. "
                 "Velkakirjat kassakaapissa - voisi kiristää puolta kaupunkia."),
    },
    "rhea_ashford": {
        "name": "Sister-Medic Rhea Ashford", "race": "Human",
        "role": ("Saint Lumen Field Hospicen johtaja Muckfordin laitamilla. "
                 "Hoitaa areena- ja kenttäloukkaantuneet; tiukka "
                 "Vortex-altistuneiden eristämisessä tautien takia."),
    },
    "hamo": {
        "name": "Hamo", "race": "Goblin",
        "role": ("Bounty broker - tietoa ja palkkiotehtäviä areenojen "
                 "liepeillä. Muckfordissa maksaa rottien hännistä ja "
                 "varhaisista boss-havainnoista."),
    },
}

TIER0_PLACES = {
    "shanty_yard": {
        "name": "Shanty Yard",
        "desc": ("Muckfordin mutainen piha-areena; katsomot romusta ja "
                 "tynnyreistä."),
        "hazards": ["Slick Mud Lanes (liukkaat mutakaistat)",
                    "Rot Planks (lahot, pettävät laudat)",
                    "Katsomo heittelee satunnaisesti romua kentälle"],
    },
    "sunk_cask": {
        "name": "The Sunk Cask",
        "motto": "Täällä allekirjoitat sopimuksen, tai sinut allekirjoitetaan.",
        "menu": ["Mud-Stew (halpa juuresmuhennos)",
                 "Sour Ale (laimea olut)",
                 "Ratpot Pie (sisällöstä vitsaillaan synkästi)"],
        "desc": "Kaupungin tärkein majatalo ja värväyskeskus.",
    },
    "saint_lumen": {
        "name": "Saint Lumen Field Hospice",
        "desc": ("Hätätemppeli Muckfordin laitamilla; areenahaavat, "
                 "kenttäevakuoinnit ja Vortex-altistuneiden karanteeni."),
    },
}

TIER0_THREATS = {
    "rat_armies": {
        "name": "Muckford Rat-Armies", "threat_class": "S2",
        "desc": ("Viemäreistä nousevat loputtomat rottaswarmit: taudit ja "
                 "ruokavarastojen tyhjennys. Silmät hohtavat nykyään "
                 "violetteina - syövät Vortex-jätettä ja muuttuvat "
                 "vaarallisemmiksi."),
    },
    "rat_king": {
        "name": "The Rat King of Muckford", "rank": "C",
        "type": "Abyssal Echo",
        "desc": "Rottalaumojen johtaja; Muckfordin suurin jatkuva kriisi.",
    },
}

# Hamon ostohinnat (parempi kuin markkinat - siksi hänet kannattaa etsiä)
HAMO_BOUNTIES = {
    "Rat Tail": 4,   # markkinahinta 2
}
