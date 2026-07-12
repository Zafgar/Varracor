#!/usr/bin/env python3
"""
Loitsujen tasapaino-raportti.

Listaa kaikki SPELL_LIBRARYn loitsut koulukunnittain ja tasoittain, nayttaa
vahingon/parannuksen, manan, strainin, cooldownin ja kantaman, ja laskee
tehokkuusluvut (vahinko/mana, vahinko/strain) seka varoittaa epasaannoista
tasoskaalauksesta. Nain magian balanssia voi seurata yhdella silmayksella.

Aja:  python tools/spell_report.py
      python tools/spell_report.py --school pure
"""
import os
import sys
import argparse

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from magic.spell_data import SPELL_LIBRARY          # noqa: E402
from magic.schools import SCHOOLS, tier_name        # noqa: E402

SCHOOL_ORDER = ["pure", "holy", "necromancy", "druidism", "manipulation", "abyssal"]


def report_school(school):
    spells = sorted(
        [(n, v) for n, v in SPELL_LIBRARY.items() if v["school"] == school],
        key=lambda kv: (kv[1]["tier"], kv[0]))
    if not spells:
        return
    meta = SCHOOLS.get(school, {})
    print(f"\n{'='*82}")
    print(f"  {meta.get('name', school).upper()}   ({meta.get('org','')})")
    print(f"{'='*82}")
    print(f"  {'SPELL':22} {'T':>2} {'KIND':7} {'PWR':>4} {'MANA':>4} "
          f"{'STRN':>4} {'CD':>4} {'RNG':>4}  {'P/M':>4} {'P/S':>4}")
    warnings = []
    prev_strain = 0
    for n, v in spells:
        t = v["tier"]
        pwr = v.get("power", 0)
        mana = v.get("mana", 0)
        strn = v.get("strain", 0)
        cd = v.get("cooldown", 0)
        rng = v.get("range", 0)
        pm = pwr / mana if mana else 0
        ps = pwr / strn if strn else 0
        print(f"  {n:22} {t:>2} {v['kind']:7} {pwr:>4} {mana:>4} "
              f"{strn:>4.0f} {cd:>4} {rng:>4}  {pm:>4.1f} {ps:>4.1f}")
        # varoitus: strain ei kasva tason myota
        if strn < prev_strain:
            warnings.append(f"  ! {n}: strain {strn:.0f} < edellinen {prev_strain:.0f}")
        prev_strain = strn
    for w in warnings:
        print(w)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--school", default=None, help="pure/holy/necromancy/druidism/manipulation/abyssal")
    args = ap.parse_args()
    schools = [args.school] if args.school else SCHOOL_ORDER
    total = len(SPELL_LIBRARY)
    print(f"\nSPELL LIBRARY - {total} spells across {len(SCHOOL_ORDER)} schools")
    for sk in schools:
        report_school(sk)
    print()


if __name__ == "__main__":
    main()
