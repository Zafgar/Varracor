#!/usr/bin/env python3
"""
Areenan voimatasapaino-raportti.

Tulostaa jokaiselta tieriltä joukkueiden voiman (level-osuus vs gear-osuus
eriteltyna), kokoonpanon ja sisaisen voimahierarkian. Nain balanssia voi
seurata yhdella silmayksella kun rosterit / gear / rodut muuttuvat.

Aja:  python tools/balance_report.py
      python tools/balance_report.py --tier 1
"""
import os
import sys
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((64, 64))

from leagues.league_data import generate_league_teams          # noqa: E402
from leagues.league_engine import (_unit_power, _weapon_damage,  # noqa: E402
                                    _has_shield, _safe_roster)

# Lore-tier nimet (engine tier N = lore tier N-1)
try:
    from lore.world_data import ARENA_TIERS
except Exception:
    ARENA_TIERS = {}


def _level_part(u):
    return float(getattr(u, "level", 1) or 1) * 12.0


def _gear_part(u):
    return _unit_power(u) - _level_part(u)


def report_tier(engine_tier):
    lore_tier = max(0, engine_tier - 1)
    tname = ARENA_TIERS.get(lore_tier, {}).get("name", f"Tier {lore_tier}")
    print(f"\n{'='*72}")
    print(f"  ENGINE TIER {engine_tier}  (lore Tier {lore_tier}: {tname})")
    print(f"{'='*72}")

    teams = generate_league_teams(engine_tier)
    rows = []
    for t in teams:
        roster = _safe_roster(t)
        if not roster:
            rows.append((0.0, t, roster, 0.0, 0.0))
            continue
        n = len(roster)
        power = sum(_unit_power(u) for u in roster) / n
        lvl_p = sum(_level_part(u) for u in roster) / n
        gear_p = sum(_gear_part(u) for u in roster) / n
        rows.append((power, t, roster, lvl_p, gear_p))

    rows.sort(key=lambda r: r[0], reverse=True)
    if not rows:
        print("  (no teams)")
        return

    top = rows[0][0] or 1.0
    print(f"  {'TEAM':22s} {'PWR':>6} {'LVL%':>5} {'GEAR%':>6} {'n':>3}  bar")
    for power, t, roster, lvl_p, gear_p in rows:
        name = getattr(t, "name", "?")[:22]
        lvlpct = 100 * lvl_p / power if power else 0
        gearpct = 100 * gear_p / power if power else 0
        bar = "#" * int(28 * power / top)
        print(f"  {name:22s} {power:6.1f} {lvlpct:4.0f}% {gearpct:5.0f}% "
              f"{len(roster):3d}  {bar}")

    spread = rows[0][0] / (rows[-1][0] or 1.0)
    print(f"\n  Champion: {getattr(rows[0][1],'name','?')}  "
          f"| Weakest: {getattr(rows[-1][1],'name','?')}  "
          f"| Spread (top/bottom): {spread:.2f}x")

    # Aseiden kirjo tierilla
    weapons = {}
    for _, t, roster, _l, _g in rows:
        for u in roster:
            w = u.equipment.get("main_hand") if hasattr(u, "equipment") else None
            wn = getattr(w, "name", "Fists")
            weapons[wn] = weapons.get(wn, 0) + 1
    unarmed = weapons.get("Fists", 0)
    print(f"  Weapons in play: {len(weapons)} types"
          + (f"   !! {unarmed} UNARMED (Fists)" if unarmed else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", type=int, default=None,
                    help="Engine tier (1 = lore Tier 0). Oletus: kaikki 1-6.")
    args = ap.parse_args()

    tiers = [args.tier] if args.tier else range(1, 7)
    for et in tiers:
        report_tier(et)
    print()


if __name__ == "__main__":
    main()
