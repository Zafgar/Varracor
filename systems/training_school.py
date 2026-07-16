# systems/training_school.py
"""Gladiaattorien koulutus (pelaajan suunnittelu):

- Gladiaattori laitetaan kouluun, jossa hän viettää PELIPÄIVIÄ ja saa
  statteja. Koulutuksen aikana hän ei ole käytettävissä (in_training).
- Maksu: joko PÄIVITTÄIN (rahaa lähtee joka päivä; loppuu jos ei varaa)
  tai ETUKÄTEEN kiinteä jakso (5 tai 10 päivää).
- REPUTATION avaa parempia koulutuksia: Basic (rep 0), Advanced (rep 10),
  Elite (rep 25). Parempi taso = isompi päivähyöty, kovempi hinta.
- Päivähyöty skaalautuu statikäyrän mukana (progression/stat_curve):
  ~3% tason stat-tavoitteesta per päivä -> pysyy relevanttina kun luvut
  kasvavat satoihin/tuhansiin.

Stateihin kasvu kirjataan base_attributes-sanakirjaan, jotta
calculate_final_stats säilyttää sen (gear + % puusta tulevat päälle)."""

from progression.stat_curve import daily_training_gain

# Koulutustasot: reputation-vaatimus, hyötykerroin, hintakerroin
TIERS = {
    "basic":    {"rep": 0,  "gain_mult": 1.0, "cost_mult": 1.0,
                 "label": "Basic Drills"},
    "advanced": {"rep": 10, "gain_mult": 1.5, "cost_mult": 1.8,
                 "label": "Advanced Regimen"},
    "elite":    {"rep": 25, "gain_mult": 2.2, "cost_mult": 3.2,
                 "label": "Elite Mentorship"},
}

# Mitä statteja voi kouluttaa -> base_attributes-avain
STATS = {"str": "str", "dex": "dex", "int": "int"}

PREPAID_PERIODS = (5, 10)


def daily_cost(unit, tier="basic"):
    """Päivämaksu: kasvaa hahmon tason ja koulutustason mukaan."""
    t = TIERS.get(tier, TIERS["basic"])
    return max(2, int((6 + int(getattr(unit, "level", 1)) * 2)
                      * t["cost_mult"]))


def available_tiers(manager):
    rep = int(getattr(manager, "reputation", 0))
    return [k for k, t in TIERS.items() if rep >= t["rep"]]


def enroll(manager, unit, stat, tier="basic", days=None):
    """Aloita koulutus. days=None -> päivittäinen maksu; days=5|10 ->
    etukäteen maksettu jakso. Palauttaa (ok, viesti)."""
    if stat not in STATS:
        return False, "Unknown stat"
    if tier not in TIERS:
        return False, "Unknown tier"
    if getattr(unit, "in_training", None):
        return False, f"{unit.name} is already in training"
    rep = int(getattr(manager, "reputation", 0))
    if rep < TIERS[tier]["rep"]:
        return False, f"Requires reputation {TIERS[tier]['rep']}"
    cost = daily_cost(unit, tier)
    if days is not None:
        if int(days) not in PREPAID_PERIODS:
            return False, f"Prepaid periods: {PREPAID_PERIODS}"
        total = cost * int(days)
        if manager.gold < total:
            return False, f"Prepay costs {total} SP"
        manager.gold -= total
    else:
        if manager.gold < cost:
            return False, f"Daily fee is {cost} SP"

    unit.in_training = {
        "stat": stat, "tier": tier,
        "days_left": int(days) if days is not None else None,  # None = kunnes rahat/lopetus
        "prepaid": days is not None,
        "days_done": 0,
    }
    roster = getattr(manager, "training_roster", None)
    if roster is None:
        roster = manager.training_roster = []
    if unit not in roster:
        roster.append(unit)
    return True, f"{unit.name} enrolled: {TIERS[tier]['label']} ({stat.upper()})"


def withdraw(manager, unit):
    """Keskeytä koulutus (ei hyvitystä etukäteismaksusta)."""
    if not getattr(unit, "in_training", None):
        return False
    unit.in_training = None
    roster = getattr(manager, "training_roster", [])
    if unit in roster:
        roster.remove(unit)
    return True


def _apply_gain(unit, stat, tier):
    gain = daily_training_gain(getattr(unit, "level", 1),
                               TIERS[tier]["gain_mult"])
    key = STATS[stat]
    base = getattr(unit, "base_attributes", None)
    if base is None:
        base = unit.base_attributes = {}
    cur_defaults = {"str": 5, "dex": 5, "int": 5}
    base[key] = int(base.get(key, cur_defaults.get(key, 5))) + gain
    try:
        unit.calculate_final_stats()
    except Exception:
        pass
    return gain


def advance_day(manager):
    """Kutsutaan kerran per pelipäivä (world_clockin day-listener).
    Veloittaa päivämaksut, antaa statihyödyt, valmistaa jaksot."""
    roster = list(getattr(manager, "training_roster", []) or [])
    report = []
    for unit in roster:
        rec = getattr(unit, "in_training", None)
        if not rec or getattr(unit, "is_dead", False):
            withdraw(manager, unit)
            continue
        tier = rec["tier"]
        # Päivittäinen maksu (ei etukäteen maksettu)
        if not rec["prepaid"]:
            cost = daily_cost(unit, tier)
            if manager.gold < cost:
                withdraw(manager, unit)
                report.append((unit, 0, "expelled (unpaid)"))
                continue
            manager.gold -= cost
        gain = _apply_gain(unit, rec["stat"], tier)
        rec["days_done"] += 1
        report.append((unit, gain, "trained"))
        if rec["days_left"] is not None:
            rec["days_left"] -= 1
            if rec["days_left"] <= 0:
                withdraw(manager, unit)
                report.append((unit, 0, "graduated"))
    return report
