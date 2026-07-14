# systems/grand_slam_series.py
"""Grand Slam -finaalin best-of-3 -sarjalogiikka.

Sarjatila elää manager.finale_series-sanakirjassa:
    {"round": 1..3, "wins": n, "losses": n, "mode": "intro"/"round"/"champion"}

Kulku:
    League: PLAY RANK UP! -> begin_series() -> prepare -> finale_show
    (announcer + walk-in) -> battle -> battle_report -> loot_screen ->
    handle_promotion_result():
        voitot 2  -> promote + finale_show (champion) -> promotion_ceremony
        tappiot 2 -> league (sarja hävitty)
        muuten    -> uusi kierros (revive + start_match) -> finale_show
"""

from leagues.league_engine import PROMOTION_BATTLE_SIZE

ROUND_TWISTS = {
    1: ("A CLEAN BOUT", "No tricks. Steel, sand and nerve."),
    2: ("CROWD DEBRIS", "The stands throw crates into the pit - watch the red rings!"),
    3: ("FIRE RING", "Sudden death! A ring of fire closes toward the centre."),
}


def begin_series(manager):
    """Nollaa sarjan kun promotion-matsi käynnistetään liigasta."""
    manager.finale_series = {"round": 1, "wins": 0, "losses": 0,
                             "mode": "intro"}


def get_series(manager):
    s = getattr(manager, "finale_series", None)
    if not isinstance(s, dict):
        begin_series(manager)
        s = manager.finale_series
    return s


def _revive_fighters(manager):
    """Best-of-3: jokainen kierros alkaa täysissä voimissa."""
    for u in list(getattr(manager, "last_fighters", []) or []):
        if not u:
            continue
        u.is_dead = False
        u.current_hp = u.max_hp
        u.current_mana = u.max_mana
        u.current_stamina = u.max_stamina
        try:
            u.status_effects.clear()
        except Exception:
            pass


def handle_promotion_result(manager) -> str:
    """Kutsutaan loot-ruudusta kun PROMOTION-kierros on ohi.
    Palauttaa seuraavan tilan nimen."""
    series = get_series(manager)
    won = manager.match_result == "VICTORY"
    if won:
        series["wins"] += 1
    else:
        series["losses"] += 1

    if series["wins"] >= 2:
        # SARJA VOITETTU -> tier nousee, mestaruusjuhla areenalla,
        # sitten varsinainen seremonia (farewell-sivut)
        engine = getattr(manager, "league_engine", None)
        won_tier = int(getattr(engine, "tier", 0)) if engine else 0
        # Mestaruus kylän muistiin - näkyy mm. Arena Hallin vitriinissä
        try:
            manager.record_deed(
                f"tier{won_tier}_champion",
                f"won the Grand Slam and claimed the Tier {won_tier} "
                f"championship")
        except Exception:
            pass
        if engine:
            engine.promote_player()
        series["mode"] = "champion"
        return "finale_show"

    if series["losses"] >= 2:
        # Sarja hävitty - takaisin liigaan (kausi jatkuu normaalisääntöjen
        # mukaan; uusi yritys vaatii uuden kauden)
        manager.finale_series = None
        manager.match_mode = ""
        return "league"

    # Seuraava kierros: elvytä molemmat puolet ja käynnistä matsi heti
    series["round"] += 1
    series["mode"] = "round"
    _revive_fighters(manager)
    manager.match_mode = "PROMOTION"
    fighters = [u for u in (getattr(manager, "last_fighters", []) or []) if u]
    manager.start_match(fighters, PROMOTION_BATTLE_SIZE)
    return "finale_show"
