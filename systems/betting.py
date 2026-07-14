# systems/betting.py
"""Vintin vedonlyöntitoimisto (pelitesti 15).

Pelaaja voi lyödä vetoa MINKÄ TAHANSA tiimin seuraavasta liigamatsista
(1v1/3v3/5v5), ei vain omastaan. Kertoimet lasketaan ELO-erosta talon
marginaalilla, panoksia rajaa tierikohtainen pöytäraja ja avoimia
kuponkeja voi olla useita.

Kupongit ratkeavat "laiskasti": kun tiimin ottelu on pelattu (pelaajan
oma matsi tai simuloitu taustamatsi), TeamRecordin played-laskuri
kasvaa - voitto näkyy wins-laskurissa. check_open_bets vertaa näitä
kupongin ottohetken lukuihin, maksaa voitot ja poistaa ratkenneet.

UI: menus/betting_menu.py (tila "betting_office", E Vintin kojulla).
"""

from ui_kit import format_money

# Tierikohtaiset pöytärajat määritellään Arena Hallin yhteydessä
from citys.mucford.city_interiors import WAGER_MAX_BY_TIER

MAX_OPEN_BETS = 6
HOUSE_MARGIN = 0.92   # talo pitää siivunsa: reilu kerroin olisi 1/p
MODES = ("1v1", "3v3", "5v5")


def _season(manager, mode):
    eng = getattr(manager, "league_engine", None)
    if eng is None:
        return None
    try:
        eng._ensure_initialized()
    except Exception:
        return None
    return eng.seasons.get(mode)


def open_bets(manager):
    if getattr(manager, "open_bets", None) is None:
        manager.open_bets = []
    return manager.open_bets


def table_limit(manager) -> int:
    tier = int(getattr(getattr(manager, "league_engine", None),
                       "tier", 1)) or 1
    return WAGER_MAX_BY_TIER.get(tier, 50)


def win_probability(season, team_id, opp_id) -> float:
    """Tiimin voittotodennäköisyys ELO-erosta, kevyesti kohti 50 %
    regressoituna (alkukauden ELO ei vielä kerro kaikkea)."""
    from leagues.league_engine import _elo_expected
    ra = season.records.get(team_id)
    rb = season.records.get(opp_id)
    if not ra or not rb:
        return 0.5
    p = _elo_expected(ra.elo, rb.elo)
    return 0.5 + (p - 0.5) * 0.85


def odds_multiplier(season, team_id, opp_id) -> float:
    """Maksukerroin: talon marginaali / todennäköisyys, 1.05-6.00."""
    p = max(0.01, win_probability(season, team_id, opp_id))
    return round(max(1.05, min(6.0, HOUSE_MARGIN / p)), 2)


def current_opponent(season, team_id):
    """Tiimin vastustaja käynnissä olevalla kierroksella tai None."""
    for a, b in getattr(season, "_current_pairings", []):
        if a == team_id:
            return b
        if b == team_id:
            return a
    return None


def fixtures(season):
    """Kierroksen ottelut [(a_id, b_id), ...]."""
    return list(getattr(season, "_current_pairings", []))


def place_bet(manager, mode, team_id, amount):
    """Yrittää asettaa kupongin. Palauttaa (onnistuiko, viesti)."""
    bets = open_bets(manager)
    if len(bets) >= MAX_OPEN_BETS:
        return False, f"Vint caps you at {MAX_OPEN_BETS} open tickets."
    season = _season(manager, mode)
    if season is None:
        return False, "No league running."
    rec = season.records.get(team_id)
    if rec is None:
        return False, "Vint doesn't know that team."
    opp = current_opponent(season, team_id)
    if opp is None:
        return False, "No match scheduled for that team."
    amount = int(amount)
    limit = table_limit(manager)
    if amount <= 0:
        return False, "Put some coin down first."
    if amount > limit:
        return False, f"Table limit here is {format_money(limit)}."
    if int(getattr(manager, "gold", 0)) < amount:
        return False, "Not enough coin."
    rnd = int(getattr(season, "current_round", 0))
    for b in bets:
        if b["mode"] == mode and b["team_id"] == team_id \
                and b.get("round") == rnd:
            return False, "You already hold a ticket on that team."
    mult = odds_multiplier(season, team_id, opp)
    manager.gold -= amount
    bets.append({
        "mode": mode,
        "team_id": team_id,
        "team_name": season._team_name(team_id),
        "opp_name": season._team_name(opp),
        "amount": amount,
        "mult": mult,
        "round": rnd,
        "placed_played": int(rec.played),
        "placed_wins": int(rec.wins),
    })
    return True, (f"Ticket in: {season._team_name(team_id)} to beat "
                  f"{season._team_name(opp)}, pays x{mult:.2f}.")


def check_open_bets(manager):
    """Ratkoo kupongit joiden ottelu on pelattu. Palauttaa viestilistan."""
    bets = open_bets(manager)
    if not bets:
        return []
    messages, still_open = [], []
    for b in bets:
        season = _season(manager, b.get("mode"))
        rec = season.records.get(b.get("team_id")) if season else None
        if rec is None:
            manager.gold += int(b.get("amount", 0))
            messages.append(f"Void ticket refunded "
                            f"({format_money(int(b.get('amount', 0)))}).")
            continue
        placed_played = int(b.get("placed_played", 0))
        if rec.played < placed_played:
            # Kausi nollautui kupongin oton jälkeen -> panos takaisin
            manager.gold += int(b.get("amount", 0))
            messages.append(f"Season reset - stake refunded "
                            f"({format_money(int(b.get('amount', 0)))}).")
            continue
        if rec.played == placed_played:
            still_open.append(b)
            continue
        won = rec.wins > int(b.get("placed_wins", 0))
        if won:
            payout = int(b["amount"] * float(b.get("mult", 2.0)))
            manager.gold += payout
            messages.append(f"{b['team_name']} WON - Vint pays "
                            f"{format_money(payout)} (x{b['mult']:.2f})!")
        else:
            messages.append(f"{b['team_name']} lost - "
                            f"{format_money(int(b['amount']))} to the Yard.")
    manager.open_bets = still_open
    return messages
