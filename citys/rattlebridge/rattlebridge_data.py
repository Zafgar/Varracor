"""Canonical gameplay data for the Rattlebridge expansion."""

from __future__ import annotations

from collections import OrderedDict


RATTLEBRIDGE_LEVEL_RANGE = (6, 10)
WORLD_SIZE_MULTIPLIER = (4.5, 3.4)

DISTRICTS = OrderedDict({
    "west_tollgate": {
        "name": "West Tollgate",
        "rect_norm": (0.02, 0.30, 0.16, 0.34),
        "color": (94, 82, 68),
        "summary": "Crown customs, guarded caravan lanes and the western road from Muckford.",
        "services": ("customs", "caravan registry", "bridge permits"),
    },
    "union_market": {
        "name": "Ironspan Union Market",
        "rect_norm": (0.19, 0.10, 0.20, 0.37),
        "color": (111, 84, 57),
        "summary": "A dense freight market run by unions, factors and sponsor agents.",
        "services": ("market", "contracts", "sponsor stalls", "city storage"),
    },
    "span_ward": {
        "name": "Span Ward",
        "rect_norm": (0.42, 0.08, 0.16, 0.35),
        "color": (104, 72, 49),
        "summary": "Workers' housing, bridge taverns and Ironspan Union meeting rooms.",
        "services": ("The Span", "lodging", "recruitment rumors"),
    },
    "scrapring_district": {
        "name": "Scrapring District",
        "rect_norm": (0.62, 0.07, 0.25, 0.39),
        "color": (87, 75, 69),
        "summary": "Tier 1 arena offices, sponsor galleries and team preparation yards.",
        "services": ("The Scrapring", "Sera Quench", "team registration"),
    },
    "bridgeward": {
        "name": "Bridgeward",
        "rect_norm": (0.20, 0.61, 0.21, 0.28),
        "color": (87, 85, 77),
        "summary": "Chapel-hospital, guard barracks and injury recovery services.",
        "services": ("Bridgeward Hospital", "guard office", "injury treatment"),
    },
    "freight_deck": {
        "name": "Freight Deck",
        "rect_norm": (0.46, 0.59, 0.23, 0.30),
        "color": (83, 75, 64),
        "summary": "Cranes, warehouses and cargo transfer platforms above the canalworks.",
        "services": ("warehouse", "cargo contracts", "industrial suppliers"),
    },
    "canal_lift": {
        "name": "Canalworks Lift",
        "rect_norm": (0.73, 0.58, 0.14, 0.29),
        "color": (58, 70, 70),
        "summary": "Guarded access to the lower channels and Gutter Swarm patrol routes.",
        "services": ("Canalworks", "sewer patrols", "boss investigation"),
    },
    "east_checkpoint": {
        "name": "East Chain Gate",
        "rect_norm": (0.88, 0.30, 0.10, 0.34),
        "color": (89, 78, 67),
        "summary": "The chain-controlled road toward Rivet Row and the eastern bridge approaches.",
        "services": ("regional travel", "bridgeguard checkpoint"),
    },
})

LANDMARKS = OrderedDict({
    "world_gate": {
        "name": "Western Caravan Gate",
        "district": "west_tollgate",
        "position_norm": (0.075, 0.48),
        "size": (260, 190),
        "kind": "world_map",
        "target_state": "world_map",
        "prompt": "E: Open the Varrakor map",
    },
    "customs_office": {
        "name": "Crown Customs Office",
        "district": "west_tollgate",
        "position_norm": (0.125, 0.36),
        "size": (350, 220),
        "kind": "customs",
        "prompt": "E: Review tolls and permits",
    },
    "union_market": {
        "name": "Ironspan Union Market",
        "district": "union_market",
        "position_norm": (0.285, 0.27),
        "size": (520, 280),
        "kind": "market",
        "target_state": "market",
        "prompt": "E: Enter the union market",
    },
    "contract_board": {
        "name": "Bridge Contract Board",
        "district": "union_market",
        "position_norm": (0.365, 0.39),
        "size": (90, 110),
        "kind": "contract_board",
        "target_state": "rattlebridge_contracts",
        "prompt": "E: Read bridge contracts",
    },
    "the_span": {
        "name": "Boil-Cider House ‘The Span’",
        "district": "span_ward",
        "position_norm": (0.495, 0.25),
        "size": (560, 310),
        "kind": "interior",
        "target_state": "rattlebridge_span",
        "prompt": "E: Enter The Span",
    },
    "scrapring_gate": {
        "name": "The Scrapring",
        "district": "scrapring_district",
        "position_norm": (0.745, 0.25),
        "size": (760, 390),
        "kind": "arena",
        "target_state": "rattlebridge_scrapring",
        "prompt": "E: Enter the Scrapring district",
    },
    "sera_office": {
        "name": "Sera Quench’s Sponsor Office",
        "district": "scrapring_district",
        "position_norm": (0.635, 0.40),
        "size": (300, 200),
        "kind": "sera",
        "prompt": "E: Speak with Sera Quench",
    },
    "bridgeward_hospital": {
        "name": "Bridgeward Chapel-Hospital",
        "district": "bridgeward",
        "position_norm": (0.305, 0.73),
        "size": (650, 360),
        "kind": "hospital",
        "target_state": "rattlebridge_hospital",
        "prompt": "E: Enter Bridgeward Hospital",
    },
    "guard_barracks": {
        "name": "Bridgeguard Barracks",
        "district": "bridgeward",
        "position_norm": (0.205, 0.82),
        "size": (350, 210),
        "kind": "guard",
        "prompt": "E: Speak to the bridgeguard",
    },
    "freight_warehouse": {
        "name": "Ironspan Freight Warehouse",
        "district": "freight_deck",
        "position_norm": (0.565, 0.73),
        "size": (720, 330),
        "kind": "storage",
        "target_state": "city_storage",
        "prompt": "E: Open city storage",
    },
    "canalworks_lift": {
        "name": "Canalworks Lift",
        "district": "canal_lift",
        "position_norm": (0.795, 0.75),
        "size": (420, 300),
        "kind": "dungeon",
        "target_state": "rattlebridge_canalworks",
        "prompt": "E: Descend into the Canalworks",
    },
    "east_gate": {
        "name": "East Chain Gate",
        "district": "east_checkpoint",
        "position_norm": (0.935, 0.48),
        "size": (250, 190),
        "kind": "travel",
        "target_state": "world_map",
        "prompt": "E: Open eastern travel routes",
    },
})

NAMED_NPCS = OrderedDict({
    "sera_quench": {
        "name": "Sera Quench",
        "race": "Human",
        "role": "Tier 1 Circuit Manager",
        "district": "scrapring_district",
        "position_norm": (0.655, 0.44),
        "color": (180, 80, 72),
        "dialogue": (
            "Muckford proves a team can survive. Rattlebridge proves whether anyone will pay to watch.",
            "Sponsors remember colors, victories and scandals. Give them the first two and deny them the third.",
            "The Scrapring gears do not care how famous you are. Learn the timing before they learn your bones.",
            "I do not sell fighters. I sell stories with a fighter attached. Give me a good one.",
            "New posters every week, yes. It is called visibility. The Union calls it something ruder.",
            "Win clean and I can market you. Win ugly and I can still market you - for more. Just do not lose boring.",
            "The Runners are my showcase: Corwin Hale keeps them tidy, and tidy sells to the Crown's money.",
            "Bridgeguard Five? Dull as a toll ledger. Reliable, though. Sponsors hate them, gamblers love them.",
            "Steam bursts blind the crowd's favorites for a heartbeat. A heartbeat is enough to change the odds.",
            "Everyone blames my banners for the taxes. The taxes were here before my banners. I just made them worth it.",
        ),
    },
    "hendrik_ironspan": {
        "name": "Hendrik Ironspan",
        "race": "Human",
        "role": "Keeper of The Span",
        "district": "span_ward",
        "position_norm": (0.475, 0.39),
        "color": (166, 119, 67),
        "dialogue": (
            "Warm cider, dry boots and no fighting without cause. Those are the rules of The Span.",
            "The Ironspan Union hears every bridge rumor before the Crown writes it down.",
            "Workers respect teams that take sewer patrols. They respect teams that return even more.",
            "Boil-cider's the only thing in this city the Crown hasn't found a way to tax twice. Drink up.",
            "You want the truth about Rattlebridge? It's held together by rivets, debt and the Union. In that order.",
            "The fog's been coming earlier. When The Span goes quiet mid-song, you leave by the land door. Fast.",
            "Hush-Mantle takes the sound before it takes the man. No scream, no boots, no last prayer.",
            "Someone's greasing a toll-man to run Vortex-waste through the underway. Union'll find him before the Crown pretends to.",
            "Sera sells shine. Prior Jannik sells mercy by the coin. Me, I sell a warm seat and a fair word. Rarer than both.",
            "King Alaric keeps the roads open and the purse tight. Strong hand, heavy hand. Depends whose neck it's on.",
        ),
    },
    "prior_jannik_voss": {
        "name": "Prior Jannik Voss",
        "race": "Human",
        "role": "Prior of Bridgeward Hospital",
        "district": "bridgeward",
        "position_norm": (0.325, 0.84),
        "color": (201, 190, 145),
        "dialogue": (
            "Healing is sacred. Specialist treatment, however, is expensive. Both truths, at once.",
            "The Scrapring breaks bones in remarkably predictable ways. I price accordingly.",
            "Charity keeps the chapel warm. Coin keeps the surgeons sober. I keep the ledgers.",
            "The holy lamps are not cheap, the good surgeons less so, and pain, my friend, is a seller's market.",
            "A cracked skull from the gears? Standard rate. A blade envenomed by some gutter alchemist? Now we negotiate.",
            "The Red Lantern fever fills my beds and empties my stores. The Crown sends prayers. I would prefer silver.",
            "I do not overcharge. I charge exactly what a desperate man will pay. The Synod calls that a sin. I call it arithmetic.",
            "Bring your wounded early and pay in full. Bring them late and pay in full, and grief. The price is the same.",
            "You judge me. Good. Judge me from a bed you did not have to mortgage your team to lie in.",
        ),
    },
    "captain_mara_chain": {
        "name": "Captain Mara Chain",
        "race": "Human",
        "role": "Bridgeguard Captain",
        "district": "bridgeward",
        "position_norm": (0.225, 0.78),
        "color": (82, 130, 170),
        "dialogue": (
            "Hold the line, keep the lane clear, and never stand under a cargo bell.",
            "The Gutter Swarm is not just rats. Something in the runoff teaches them to move together.",
            "Hush-Mantle sightings always begin with people complaining the city has gone too quiet.",
            "When the fog eats your own footsteps, you are already inside it. Walk to light. Do not run.",
            "Red Lantern Cadavers carry the fever with them. Put them down at range, then burn the rags. No trophies.",
            "Half my guards are chasing bridge gangs the tolls created. The other half are chasing the fog. Wonderful.",
            "Bridgeguard Five drills with us. If the Swarm ever breaches the underway, they are the plug in the dam.",
            "You want to help this city? Take a sewer contract. The pay is bad and the smell is worse. That is how you know it's real work.",
        ),
    },
    "factor_ellis_vane": {
        "name": "Factor Ellis Vane",
        "race": "Human",
        "role": "Crown Toll Assessor",
        "district": "west_tollgate",
        "position_norm": (0.105, 0.44),
        "color": (145, 125, 105),
        "dialogue": (
            "Every wheel, hoof and blade crossing this span has a declared value. Undeclared value has a fine.",
            "Arena exemptions are not tax exemptions. Sera knows the difference, even when she pretends otherwise.",
            "King Alaric Vane funds his roads and his walls with these tolls. Grumble to me; salute to him.",
            "Yes, the taxes rise. So does the Vortex, the fever and the fog. Coin is the only wall that answers all three.",
            "Do I take a little on the side? I assess honestly and I sleep poorly. Draw your own ledger.",
            "Whoever is running Vortex-waste through my gate is smarter than my seal and richer than my salary. For now.",
        ),
    },
})

LOCAL_TEAMS = OrderedDict({
    "rattlebridge_runners": {
        "name": "Rattlebridge Runners",
        "manager": "Corwin Hale",
        "style": "Disciplined mobility and clean sponsor presentation",
        "relation": "Sera Quench’s preferred showcase team",
        "reputation": 42,
        "members": (
            "Jax Merrin",       # captain
            "Sila Vorn",
            "Brenna Kest",
            "Olek Ironside",    # Dwarf
            "Miri Vale",        # Pure Magic novice
        ),
    },
    "bridgeguard_five": {
        "name": "Bridgeguard Five",
        "manager": "Halden Pike",   # retired captain
        "style": "Shield line, zone denial and defensive objectives",
        "relation": "Trusted by Rattlebridge guards and freight unions",
        "reputation": 38,
        "members": (
            "Yara Pike",
            "Toma Crest",
            "Bruk",             # Orc
            "Sel Copper",       # Dwarf
            "Enna Reed",        # magic novice
        ),
    },
})

SCRAPRING_HAZARDS = OrderedDict({
    "crushing_gears": {
        "name": "Crushing Gear Tracks",
        "telegraph_frames": 150,
        "active_frames": 90,
        "damage": 24,
        "description": "Slow moving gear carriages crush fighters who stay in marked lanes.",
    },
    "steam_bursts": {
        "name": "Blinding Steam Vents",
        "telegraph_frames": 75,
        "active_frames": 45,
        "damage": 8,
        "description": "Steam deals light damage and briefly reduces accuracy and vision.",
    },
    "magnet_plates": {
        "name": "Magnet Plates",
        "telegraph_frames": 30,
        "active_frames": 180,
        "damage": 0,
        "description": "Metal-armored fighters are slowed and pulled toward active plates.",
    },
})

RATTLEBRIDGE_CONTRACTS = [
    {
        "id": "rattlebridge_toll_manifest",
        "title": "Missing Toll Manifest",
        "giver": "Factor Ellis Vane",
        "summary": "Recover a stolen customs manifest from the lower freight deck.",
        "recommended_level": (6, 8),
        "reward": {"gold": 75, "reputation": 8, "xp": 30},
        "district": "west_tollgate",
        "objective": "survey_freight_deck",
        "lore": "The manifest lists cargo the Crown officially claims never crossed the bridge.",
    },
    {
        "id": "rattlebridge_gutter_patrol",
        "title": "Gutter Swarm Patrol",
        "giver": "Captain Mara Chain",
        "summary": "Clear infected nests beneath three Canalworks grates.",
        "recommended_level": (7, 10),
        "reward": {"gold": 110, "reputation": 12, "xp": 45,
                   "materials": {"Tanned Hide": 2, "Nightcap Fungus": 2}},
        "district": "canal_lift",
        "objective": "gutter_swarm_patrol",
        "lore": "The swarm combines rats, industrial slime and something that coordinates both.",
    },
    {
        "id": "rattlebridge_sponsor_trial",
        "title": "Sponsor Trial Card",
        "giver": "Sera Quench",
        "summary": "Win a Scrapring match while completing a rotating sponsor objective.",
        "recommended_level": (6, 10),
        "reward": {"gold": 140, "reputation": 15, "xp": 55},
        "district": "scrapring_district",
        "objective": "scrapring_sponsor_trial",
        "lore": "Sera measures teams by whether a victory can be turned into a story sponsors can sell.",
    },
    {
        "id": "rattlebridge_silent_fog",
        "title": "When the Bridge Goes Silent",
        "giver": "Hendrik Ironspan",
        "summary": "Investigate three Hush-Mantle sightings without entering the silent fog alone.",
        "recommended_level": (9, 12),
        "reward": {"gold": 180, "reputation": 18, "xp": 70,
                   "materials": {"Mirror Dust": 1}},
        "district": "span_ward",
        "objective": "hush_mantle_rumors",
        "lore": "Every witness remembers the silence more clearly than the shape inside it.",
    },
]

AMBIENT_LINES = (
    "Toll doubled again. Alaric calls it road security.",
    "Scrapring card starts at dusk. Steam vents are running hot.",
    "Union says no night shift below Deck Seven.",
    "Bridgeguard Five held the east lane for six minutes straight.",
    "The fog swallowed a cargo bell last night. No sound at all.",
    "Warm cider at The Span if your shift token is clean.",
    "Sera wants cleaner banners before the sponsor gallery opens.",
    "Gutter rats are carrying metal filings in their teeth now.",
)
