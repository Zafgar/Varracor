"""Print the canonical Tier 0 world-development status.

Usage from repository root:
    python tools/tier0_content_report.py
    python tools/tier0_content_report.py --next 12
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lore.tier0_world_plan import (  # noqa: E402
    CURRENT_FOCUS,
    PLAN_VERSION,
    TIER0_AREAS,
    completion_ratio,
    next_development_batch,
    validate_plan,
)


def _bar(ratio: float, width: int = 20) -> str:
    filled = max(0, min(width, int(round(float(ratio) * width))))
    return "#" * filled + "-" * (width - filled)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--next", type=int, default=8, dest="next_count")
    args = parser.parse_args()

    errors = validate_plan()
    print(f"Varracor Tier 0 world plan v{PLAN_VERSION}")
    print(f"Current focus: {CURRENT_FOCUS}\n")

    for area_id, area in TIER0_AREAS.items():
        ratio = completion_ratio(area_id)
        low, high = area["level_range"]
        gate = area["access_policy"]
        print(
            f"{area['order']:02d}  {area['name']:<24} "
            f"Lv {low}-{high}  [{_bar(ratio)}] {ratio * 100:5.1f}%  {gate}"
        )
        unfinished = [
            f"{domain}:{state}"
            for domain, state in area["deliverables"].items()
            if state != "live"
        ]
        if unfinished:
            print("    " + ", ".join(unfinished))

    print("\nNext development batch:")
    for index, task in enumerate(next_development_batch(args.next_count), 1):
        print(
            f"  {index:02d}. {task['area']} / {task['domain']} "
            f"({task['state']})"
        )

    if errors:
        print("\nPLAN ERRORS:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nPlan validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
