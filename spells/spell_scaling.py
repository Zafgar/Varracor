# spells/spell_scaling.py
"""Loitsujen tehon PERUSTA (yksi totuuslähde).

Suunnittelufilosofia (pelaajan linjaus):
- Teho tulee pääosin OSTAMALLA korkeamman tierin loitsu. Siksi matalat tierit
  tekevät vähän ja korkeat paljon - "osta kalliimpi taika -> jippii".
- INT on KERROIN päälle: base + INT * int_coef. Kun hahmon INT kasvaa
  (endgamessa jopa 1000+), kiinteä base muuttuu merkityksettömäksi ja
  kerroin hallitsee - juuri niin kuin halutaan.

Tässä määritellään vakiokäyrä yhden kohteen "nuke"-loitsulle per tier, sekä
arkkityyppikertoimet (AoE/DoT/heal tekevät vähemmän per osuma koska osuvat
useasti / useaan). Uudet loitsut hakevat lukunsa täältä, jotta tierien
eteneminen on johdonmukainen. Olemassa olevat käsinviritetyt loitsut voidaan
linjata tähän erikseen kun balanssi hiotaan.
"""

# Yhden kohteen nuke: kiinteä base per tier (ennen INT-kerrointa).
TIER_BASE = {
    1: 15,
    2: 35,
    3: 70,
    4: 130,
    5: 230,
    6: 380,
    7: 600,
    8: 900,
}

# INT-kerroin per tier: kuinka paljon jokainen INT-piste lisää vahinkoa.
# Kasvaa tierien myötä -> INT palkitsee enemmän isoissa loitsuissa.
TIER_INT_COEF = {
    1: 0.8,
    2: 1.2,
    3: 1.7,
    4: 2.3,
    5: 3.1,
    6: 4.1,
    7: 5.3,
    8: 6.8,
}

# Arkkityyppikerroin: kerrotaan sekä baseen että INT-kertoimeen. AoE/DoT
# osuvat useaan/useasti, joten per-osuma-budjetti on pienempi. Utility
# (liike/CC) tekee vain vähän vahinkoa.
ARCHETYPE_MULT = {
    "nuke": 1.0,        # yksi kohde, kerta-isku
    "aoe": 0.6,         # osuu useaan
    "dot_tick": 0.25,   # tikkii ~kerran sekunnissa (Burn/Poison/Regrowth)
    "channel_tick": 0.12,  # sädetikki ~6/s (Life Drain, Sun Ray)
    "heal": 0.7,        # parannus
    "utility": 0.10,    # liike/CC, minimivahinko (vähiten per osuma)
}


def tier_base(tier, archetype="nuke"):
    return TIER_BASE.get(int(tier), 0) * ARCHETYPE_MULT.get(archetype, 1.0)


def tier_int_coef(tier, archetype="nuke"):
    return TIER_INT_COEF.get(int(tier), 0) * ARCHETYPE_MULT.get(archetype, 1.0)


def scaled_damage(tier, intelligence, archetype="nuke"):
    """Loitsun teho = base(tier) + INT * int_coef(tier), arkkityypillä
    painotettuna. Palauttaa kokonaisluvun (>=0)."""
    base = tier_base(tier, archetype)
    coef = tier_int_coef(tier, archetype)
    return max(0, int(base + int(intelligence) * coef))
