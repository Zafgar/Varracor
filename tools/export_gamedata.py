# tools/export_gamedata.py
"""Exporttaa pelidatan JSONiksi Godot-versiota varten.

PY-versio on TOTUUSLÄHDE: katalogit, käyrät ja puut määritellään
Pythonissa ja exportataan godot/data/*.json -tiedostoiksi, jotka Godot
lukee (res://data/...). Näin rinnakkaiset versiot pysyvät peilissä:
kun dataa muutetaan py-puolella, ajetaan tämä uudelleen.

Aja:  python tools/export_gamedata.py
Testi tests/test_gamedata_export.py varmistaa että export on ajan
tasalla ja arvot täsmäävät py-toteutukseen."""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

OUT_DIR = os.path.join(_ROOT, "godot", "data")


def _clean(obj):
    """Tuplat listoiksi, callablet pois, muut merkkijonoiksi."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items() if not callable(v)}
    if isinstance(obj, (list, tuple, set)):
        return [_clean(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def _write(name, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {path}")


def export_stat_curve():
    from progression.stat_curve import BASE, COEF, POWER, stat_target
    _write("stat_curve.json", {
        "base": BASE, "coef": COEF, "power": POWER,
        "samples": {str(l): stat_target(l) for l in
                    (1, 5, 10, 15, 20, 25, 30)},
    })


def export_spells():
    from spells import spell_scaling as ss
    from spells.catalog import CATALOG
    _write("spells.json", {
        "tier_base": _clean(ss.TIER_BASE),
        "tier_int_coef": _clean(ss.TIER_INT_COEF),
        "tier_mana": _clean(ss.TIER_MANA),
        "tier_price": _clean(ss.TIER_PRICE),
        "archetype_mult": _clean(ss.ARCHETYPE_MULT),
        "catalog": _clean(CATALOG),
    })


def export_gear():
    import pygame
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((64, 64))
    from items.gear_catalog import all_gear
    out = []
    for g in all_gear():
        out.append({
            "id": g.gear_id, "name": g.name, "tier": g.tier,
            "line": g.line, "slot": g.slot_type, "kind": g.type,
            "school": g.school, "armor_group": g.armor_group,
            "str_bonus": g.str_bonus, "dex_bonus": g.dex_bonus,
            "int_bonus": g.int_bonus, "defense": g.defense,
            "health_bonus": g.health_bonus, "mana_bonus": g.mana_bonus,
            "passive_bonuses": _clean(g.passive_bonuses),
            "school_bonuses": _clean(g.school_bonuses),
            "level_required": g.level_required, "price": g.cost,
            "rarity": g.rarity, "flavor": g.flavor,
        })
    _write("gear.json", {"items": out})


def export_skill_tree():
    from skills.skills_data import SKILL_TREE
    _write("skill_tree.json", {"nodes": _clean(SKILL_TREE)})


def export_forms():
    from spells.druid import shapeshift as ss
    _write("shapeshift.json", {
        "forms": _clean(ss.FORMS),
        "cooldown_frames": ss.SHIFT_COOLDOWN,
    })


def export_training():
    from systems import training_school as ts
    _write("training.json", {
        "tiers": _clean(ts.TIERS),
        "prepaid_periods": list(ts.PREPAID_PERIODS),
    })


def export_all():
    export_stat_curve()
    export_spells()
    export_gear()
    export_skill_tree()
    export_forms()
    export_training()


if __name__ == "__main__":
    export_all()
