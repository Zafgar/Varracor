# skills/vortex_tree_data.py
"""Commanderin VORTEX-välilehti (pelitesti 19): Abyss-magian puu.

Intro antoi kolme Vortex-kykyä ja olento vei ne - tämä puu on tie
niiden takaisin saamiseen ja syventämiseen. Kolme reittiä:
  - Path of the Blade (SeamCut: viiltävä repeämä)
  - Path of the Step  (VortexWarp: siirtymä)
  - Path of the Pulse (RiftPulse: "antakaa tilaa" -työntö)

Noodit maksavat skill pointien LISÄKSI Vortex-kristalleja, joita saa
sinetöimällä karttojen rift-eventtejä (repeämä aukeaa Muckfordiin
aika ajoin - sinetöinti antaa kristalleja).
"""

CRYSTAL_ITEM = "Vortex Crystal"

VORTEX_TREE = {
    "riftbound": {
        "name": "Riftbound",
        "desc": "Open yourself to the Abyss: +15 max mana. The first "
                "step down a road that does not end.",
        "pos": (0, 60),
        "cost": 1,
        "crystals": 1,
        "min_level": 2,
        "requires": [],
        "effects": {"max_mana": 15}
    },

    # --- PATH OF THE BLADE (vasen) ---
    "vortex_blade_1": {
        "name": "Seam Cut",
        "desc": "Reclaim the rending seam: unlocks the Seam Cut spell.",
        "pos": (-190, -40),
        "cost": 2,
        "crystals": 2,
        "min_level": 3,
        "requires": ["riftbound"],
        "effects": {},
        "grant_spell": "SeamCut"
    },
    "vortex_blade_2": {
        "name": "Deeper Wounds",
        "desc": "The seam bites deeper: +15% Vortex spell power.",
        "pos": (-190, -150),
        "cost": 2,
        "crystals": 2,
        "min_level": 6,
        "requires": ["vortex_blade_1"],
        "effects": {"vortex_power": 0.15}
    },

    # --- PATH OF THE STEP (keski) ---
    "vortex_step_1": {
        "name": "Vortex Warp",
        "desc": "Reclaim the sidestep through the rift: unlocks Vortex "
                "Warp.",
        "pos": (0, -80),
        "cost": 2,
        "crystals": 2,
        "min_level": 4,
        "requires": ["riftbound"],
        "effects": {},
        "grant_spell": "VortexWarp"
    },
    "vortex_step_2": {
        "name": "Slipstream",
        "desc": "The rift knows your shape: -20% Vortex spell cooldowns.",
        "pos": (0, -190),
        "cost": 2,
        "crystals": 2,
        "min_level": 7,
        "requires": ["vortex_step_1"],
        "effects": {"vortex_cdr": 0.20}
    },

    # --- PATH OF THE PULSE (oikea) ---
    "vortex_pulse_1": {
        "name": "Rift Pulse",
        "desc": "Reclaim the outward breath: unlocks Rift Pulse "
                "(shove + slow).",
        "pos": (190, -40),
        "cost": 2,
        "crystals": 2,
        "min_level": 3,
        "requires": ["riftbound"],
        "effects": {},
        "grant_spell": "RiftPulse"
    },
    "vortex_pulse_2": {
        "name": "Concussive Breach",
        "desc": "The pulse hits like a falling wall: +60 shove force.",
        "pos": (190, -150),
        "cost": 2,
        "crystals": 2,
        "min_level": 6,
        "requires": ["vortex_pulse_1"],
        "effects": {"pulse_force": 60}
    },

    # --- CAPSTONE ---
    "abyssal_attunement": {
        "name": "Abyssal Attunement",
        "desc": "The Vortex answers before you call: +25 max mana, "
                "+0.05 mana regen, +10% Vortex spell power.",
        "pos": (0, -300),
        "cost": 3,
        "crystals": 4,
        "min_level": 9,
        "requires": ["riftbound"],
        "effects": {"max_mana": 25, "mana_regen": 0.05,
                    "vortex_power": 0.10}
    },
}
