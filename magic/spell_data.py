# magic/spell_data.py
"""
SPELL_LIBRARY - data-driven loitsukirjasto (yksi LibrarySpell lukee namat).

Statukset kaytetaan mekaanisesti toimivia: Slow (hidastaa), Silence (estaa
loitsinnan), Burn/Poison (DoT). Buff "Warded" = -30% vahinko. Summon nostaa
apulaisen (UndeadSkeleton) loitsijan puolelle.

Kentat: school, tier(1-8), cast(instant/channel/ritual), kind
(damage/heal/debuff/buff/summon), mana, strain, cooldown, range, power,
scaling, status(type,dur,dmg), buff{type,duration}, summon, summon_count, desc.
"""

def dmg_for(t):    return int(10 * (t ** 1.4))
def heal_for(t):   return int(24 * (t ** 1.15))
def mana_for(t):   return 6 + t * 5
def strain_for(t): return 3 + t * 4
def cd_for(t):     return 70 + t * 18
def rng_for(t):    return 280 + t * 12


def _rar(t):
    return "Common" if t <= 2 else ("Rare" if t <= 5 else ("Epic" if t <= 7 else "Legendary"))


def _dmg(name, school, tier, status=None, cast="instant", power=None, desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast,
        "kind": "debuff" if status else "damage",
        "mana": mana_for(tier), "strain": strain_for(tier), "cooldown": cd_for(tier),
        "range": rng_for(tier), "power": power or dmg_for(tier),
        "scaling": {"INT": 1.0 + 0.1 * tier}, "status": status, "desc": desc,
        "rarity": _rar(tier), "cost": 40 * tier,
    })


def _heal(name, school, tier, cast="instant", power=None, desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast, "kind": "heal",
        "mana": mana_for(tier) + 4, "strain": strain_for(tier),
        "cooldown": cd_for(tier) + 40, "range": rng_for(tier) - 40,
        "power": power or heal_for(tier), "scaling": {"INT": 0.8 + 0.1 * tier},
        "desc": desc, "rarity": _rar(tier), "cost": 45 * tier,
    })


def _buff(name, school, tier, btype="Warded", duration=None, cast="instant", desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast, "kind": "buff",
        "mana": mana_for(tier), "strain": strain_for(tier), "cooldown": cd_for(tier) + 60,
        "range": 0, "power": 0,
        "buff": {"type": btype, "duration": duration or (180 + tier * 40)},
        "scaling": {}, "desc": desc, "rarity": _rar(tier), "cost": 45 * tier,
    })


def _summon(name, school, tier, unit="UndeadSkeleton", count=1, cast="instant", desc=""):
    return (name, {
        "school": school, "tier": tier, "cast": cast, "kind": "summon",
        "mana": mana_for(tier) + 6, "strain": strain_for(tier) + 4,
        "cooldown": cd_for(tier) + 120, "range": 0, "power": 0,
        "summon": unit, "summon_count": count, "scaling": {}, "desc": desc,
        "rarity": _rar(tier), "cost": 60 * tier,
    })


def _abyssal(name, tier, kind, tree, status=None, power=None, rng=None,
             cast="instant", desc=""):
    """Abyssal Weave - vain paahenkilo. tree = Vortex-taitopuu."""
    return (name, {
        "school": "abyssal", "tier": tier, "cast": cast, "kind": kind, "tree": tree,
        "mana": mana_for(tier), "strain": strain_for(tier) + 2, "cooldown": cd_for(tier),
        "range": rng if rng is not None else rng_for(tier),
        "power": power or dmg_for(tier), "scaling": {"INT": 1.0 + 0.1 * tier},
        "status": status, "desc": desc, "rarity": "Epic" if tier <= 6 else "Legendary",
        "cost": 80 * tier,
    })


SPELL_LIBRARY = dict([

    # ================= PURE MAGIC (Prism Collegium) =================
    _dmg("Spark Bolt", "pure", 1, desc="A simple bolt of raw mana."),
    _buff("Mana Shield", "pure", 2, desc="A shell of woven mana softens blows."),
    _dmg("Arcane Dart", "pure", 2, desc="A focused dart of force."),
    _dmg("Force Pulse", "pure", 3, status=("Slow", 90, 0), desc="A concussive wave that staggers."),
    _dmg("Mana Lance", "pure", 4, desc="A lance of condensed mana."),
    _dmg("Arcane Nova", "pure", 5, desc="A burst of pure arcane energy."),
    _dmg("Nullfield", "pure", 6, status=("Silence", 150, 0), desc="Collapses a foe's channeling."),
    _dmg("Starfall", "pure", 7, desc="Calls down a shard of the firmament."),
    _dmg("Prime Equation", "pure", 8, cast="ritual",
         desc="Briefly rewrites the local rules of magic. Priceless and perilous."),

    # ================= HOLY MAGIC (Radiant Synod) =================
    _heal("Light Mend", "holy", 1, desc="A basic mending light."),
    _dmg("Smite", "holy", 2, desc="A shaft of judging light."),
    _heal("Purify", "holy", 2, desc="Cleansing radiance that knits and cleanses."),
    _buff("Radiant Ward", "holy", 3, desc="A ward of light that turns aside harm."),
    _heal("Bless", "holy", 3, desc="A deeper healing benediction."),
    _dmg("Consecrate", "holy", 4, status=("Burn", 120, 7), desc="Holy fire that lingers."),
    _heal("Sanctify", "holy", 5, desc="A veteran's field-healing prayer."),
    _heal("Resurrection Seal", "holy", 6, cast="ritual",
          desc="An immensely costly rite that drags life back from the edge."),
    _dmg("Dawnbreak", "holy", 7, desc="The first light of a new dawn, weaponized."),
    _dmg("Judgment", "holy", 8, cast="ritual",
         desc="The Synod's final word: an area-scouring pillar of light."),

    # ================= NECROMANCY (Ashen Ossuary) =================
    _dmg("Grave Chill", "necromancy", 1, status=("Slow", 100, 0), desc="A creeping chill of the grave."),
    _summon("Raise Servant", "necromancy", 2, count=1, desc="Binds a restless skeleton to your side."),
    _dmg("Bone Spear", "necromancy", 3, desc="A hurled spike of blackened bone."),
    _dmg("Wither", "necromancy", 4, status=("Poison", 150, 8), desc="Rots flesh from a distance."),
    _dmg("Soul Rend", "necromancy", 5, desc="Tears at the soul itself."),
    _dmg("Plague Wind", "necromancy", 6, status=("Poison", 180, 10), cast="channel",
         desc="A rolling wind of pestilence."),
    _summon("Bonestorm", "necromancy", 7, count=2, desc="Raises a whirl of clattering servants."),
    _dmg("Death Sovereignty", "necromancy", 8, cast="ritual",
         desc="A forbidden rite that claims dominion over the dead of an entire region."),

    # ================= DRUIDISM (Verdant Covenant) =================
    _dmg("Thorn Lash", "druidism", 1, status=("Poison", 90, 4), desc="A whip of venomous thorns."),
    _buff("Barkskin", "druidism", 2, desc="Bark sheathes the skin against blows."),
    _dmg("Entangle", "druidism", 3, status=("Slow", 140, 0), desc="Roots snare the foe's feet."),
    _dmg("Wildfire", "druidism", 4, status=("Burn", 130, 8), desc="A gout of untamed flame."),
    _dmg("Thornburst", "druidism", 5, desc="An eruption of barbed vines."),
    _dmg("Nature's Wrath", "druidism", 6, cast="channel", desc="The wild turned to weapon."),
    _dmg("Stormcall", "druidism", 7, desc="Calls the sky's fury down."),
    _dmg("Worldroot Awakening", "druidism", 8, cast="ritual",
         desc="Stirs the world-roots themselves - balance-shaking, region-altering."),

    # ================= MANIPULATION (Argent Veil) =================
    _dmg("Mind Spike", "manipulation", 1, desc="A needle of psychic force."),
    _buff("Minor Illusion", "manipulation", 1, duration=200,
          desc="A blur of false images makes you harder to strike."),
    _dmg("Confuse", "manipulation", 2, status=("Slow", 120, 0), desc="Disorients the target's senses."),
    _dmg("Mirror Shard", "manipulation", 3, desc="A shard of reflected pain."),
    _dmg("Terror", "manipulation", 4, status=("Slow", 150, 0), desc="Floods the mind with dread."),
    _dmg("Psychic Lance", "manipulation", 5, desc="A spear of raw thought."),
    _dmg("Memory Rewrite", "manipulation", 6, status=("Silence", 200, 0), cast="channel",
         desc="Rewrites a mind mid-battle - it forgets how to act."),
    _dmg("Mind Shatter", "manipulation", 7, desc="Shatters the psyche outright."),
    _dmg("Perfect Lie", "manipulation", 8, cast="ritual",
         desc="A reality-warping deception the target cannot help but believe."),

    # ================= ABYSSAL WEAVE (Commander / Vortex) =================
    # Viisi taitopuuta: Anchoring, Severing, Echoing, Warping, Taint.
    # Anchoring - vakauttaa: estaa liikkeen ja teleportit
    _abyssal("Anchor Field", 3, "debuff", "anchoring", status=("Web", 210, 0),
             desc="Pins a foe to a fixed point in space - no step, no blink."),
    _abyssal("Absolute Anchor", 6, "debuff", "anchoring", status=("Web", 360, 0),
             cast="channel", desc="Nails an entire skirmish in place around you."),
    # Severing - katkaisee siteet: purkaa suojat, poistaa kutsutut
    _abyssal("Sever Bonds", 4, "dispel", "severing",
             desc="Cuts a foe's Vortex-threads: strips wards and cheap tricks."),
    _abyssal("Unmake", 7, "dispel", "severing", cast="channel",
             desc="Severs what should not be - wards, bindings, summoned things."),
    # Echoing - aika ja varjot: toistaa iskuja / kelaa aikaa
    _abyssal("Echo Strike", 3, "damage", "echoing", power=None,
             desc="Replays your last blow as a lash of the Weave."),
    _abyssal("Rewind", 6, "heal", "echoing", cast="channel", power=None,
             desc="Winds your own timeline back a breath, undoing wounds."),
    # Warping - vaantaa tilaa ilman teleportaatiota
    _abyssal("Warp Step", 3, "warp", "warping", rng=220,
             desc="Folds the space between here and there and simply... arrives."),
    _abyssal("Fold Space", 6, "warp", "warping", rng=420,
             desc="Creases the battlefield, crossing it in a single unnatural stride."),
    # Taint Management - siirtaa/muuttaa Vortex-korruptiota voimaksi
    _abyssal("Taint Lance", 5, "drain", "taint", status=("Poison", 150, 8),
             desc="Spears a foe with corruption and drinks the backlash as strength."),
    _abyssal("Corruption Bloom", 7, "drain", "taint", status=("Poison", 220, 12),
             cast="channel", desc="Blossoms rot across a foe and turns their ruin into your power."),
])
