# items/gear_scaling.py
"""Varusteiden tier-mitoitus statikäyrää vasten.

Statit tulevat pääosin GEARISTA (pelaajan linjaus), joten varusteiden
tier-budjetit johdetaan progression/stat_curve-käyrästä: tier vastaa
tasokaistaa, ja piece-budjetti on osuus tason gear-kokonaisbudjetista."""

from progression.stat_curve import gear_stat_budget

# Mille tasolle tier on mitoitettu (8 tieriä / 30 tasoa)
GEAR_TIER_LEVEL = {1: 3, 2: 7, 3: 11, 4: 15, 5: 19, 6: 23, 7: 26, 8: 30}

# Slotin osuus tason gear-kokonaisbudjetista (ase ~25% hoidetaan erikseen)
SLOT_SHARE = {"body": 0.45, "off_hand": 0.30, "head": 0.20}

# Ostohinta per tier (SP) - hieman loitsuja halvempi
GEAR_TIER_PRICE = {1: 100, 2: 300, 3: 650, 4: 1300, 5: 2400, 6: 4200,
                   7: 7000, 8: 11000}


def gear_tier_level(tier):
    return int(GEAR_TIER_LEVEL.get(int(tier), 1))


def piece_budget(tier, slot):
    """Yhden varusteen statibudjetti (pisteinä) tierillä."""
    lvl = gear_tier_level(tier)
    share = SLOT_SHARE.get(slot, 0.30)
    return max(2, int(gear_stat_budget(lvl) * share))


def gear_price(tier):
    return int(GEAR_TIER_PRICE.get(int(tier), 100))


def gear_level_req(tier):
    """Käyttövaatimus: pari tasoa mitoitustasoa aiemmin."""
    return max(1, gear_tier_level(tier) - 2)
