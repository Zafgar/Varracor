from __future__ import annotations

"""
League simulation engine (fast + UI-friendly)
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
import random
import math
import time

# IMPORTANT: league_data.py provides Team + generate_league_teams(tier)
from leagues.league_data import generate_league_teams

PLAYER_ID = "PLAYER"

# --- Tuning ---
DEFAULT_ELO = 1000.0
ELO_K = 22.0
MC_TRIALS = 9
AUTO_RESOLVE_ON_QUERY = True

# --- Grand Slam scoring ---
POINTS_PER_WIN: Dict[str, int] = {
    "1v1": 2,
    "3v3": 4,
    "5v5": 6,
}

# --- CONFIG: VAADITUT PELIT ---
# Pidä nämä pieninä testauksen ajan (esim. 2).
REQ_GAMES: Dict[str, int] = {
    "1v1": 2,
    "3v3": 2,
    "5v5": 2,
}

# --- SEASON CYCLES ---
SEASON_THEMES = ["Spring", "Summer", "Autumn", "Winter"]
SEASONS_PER_THEME = 2  # Kuinka monta kautta yksi vuodenaika kestää


@dataclass
class TeamRecord:
    team_id: str
    team: object | None
    wins: int = 0
    losses: int = 0
    played: int = 0
    elo: float = DEFAULT_ELO

    @property
    def points(self) -> int:
        return self.wins * 3


def _safe_roster(team: object, size: int | None = None) -> List[object]:
    if not team:
        return []
    # Ensisijaisesti käytetään get_roster-metodia, joka tukee lazy loadingia
    if hasattr(team, "roster") and isinstance(team.roster, list):
        r = team.roster
        return r[:size] if size else r
    if hasattr(team, "get_roster"):
        try:
            if size is None:
                return list(team.get_roster(5))
            return list(team.get_roster(size))
        except Exception:
            return []
    if hasattr(team, "members") and isinstance(team.members, list):
        r = team.members
        return r[:size] if size else r
    return []


def _weapon_damage(u: object) -> float:
    """Efektiivinen aseen vahinko (base + stat-skaalaus). Nyrkit ~3."""
    try:
        w = u.equipment.get("main_hand")
        if w is not None and hasattr(w, "calculate_damage"):
            stats = {"str": getattr(u, "strength", 10),
                     "dex": getattr(u, "dexterity", 10),
                     "int": getattr(u, "intelligence", 10)}
            return float(w.calculate_damage(stats))
    except Exception:
        pass
    return 3.0


def _has_shield(u: object) -> bool:
    try:
        for it in getattr(u, "equipment", {}).values():
            if it is not None and getattr(it, "armor_group", "") == "shield":
                return True
    except Exception:
        pass
    return False


def _unit_power(u: object) -> float:
    """Yksikon voima. Level painaa eniten alussa (12/lvl), mutta gear
    (aseen vahinko, panssari/defense, kilpi) vaikuttaa merkittavasti.
    Nain liigasimulaatio ja tiedustelu heijastavat todellista vahvuutta."""
    if not u:
        return 0.0
    lvl = float(getattr(u, "level", 1) or 1)
    hp = float(getattr(u, "max_hp", 100) or 100)
    dmg = _weapon_damage(u)
    dfn = float(getattr(u, "defense", 0) or 0)
    shield = 8.0 if _has_shield(u) else 0.0
    return lvl * 12.0 + hp * 0.06 + dmg * 1.6 + dfn * 2.0 + shield


def _elo_expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _elo_update(ra: TeamRecord, rb: TeamRecord, a_wins: bool):
    ea = _elo_expected(ra.elo, rb.elo)
    sa = 1.0 if a_wins else 0.0
    ra.elo += ELO_K * (sa - ea)
    rb.elo += ELO_K * ((1.0 - sa) - (1.0 - ea))


class LeagueSeason:
    def __init__(self, tier: int, rounds_per_season: int = 20, promotions_enabled: bool = False):
        self.tier = int(tier)
        self.rounds_per_season = int(rounds_per_season)
        
        # Generoidaan tiimit. Sallitaan jopa 8 rivaalia (lore Tier 1:ssa on 8).
        MAX_RIVALS = 8
        self.premades: List[object] = generate_league_teams(self.tier)
        if len(self.premades) > MAX_RIVALS:
            self.premades = self.premades[:MAX_RIVALS]
        while len(self.premades) < 7:
            self.premades.append(None)

        self.records: Dict[str, TeamRecord] = {PLAYER_ID: TeamRecord(PLAYER_ID, None, elo=DEFAULT_ELO)}

        for i, t in enumerate(self.premades):
            if not t: continue
            unique_slot_id = f"T{self.tier}_RIVAL_{i+1}"
            self.records[unique_slot_id] = TeamRecord(unique_slot_id, t, elo=DEFAULT_ELO)
            if not hasattr(t, "team_id"): setattr(t, "team_id", unique_slot_id)

        self.current_round = 0
        self.phase = "regular"
        self._current_pairings = []
        self._next_opponent_id = None
        self._played_matchups = set()
        self._pending_matches = []
        self._pending_advance = False
        
        # Hall of Fame stats (kausikohtainen)
        self.hof_kills = {} 
        self.match_history = [] # Tallennetut ottelutulokset

        self._ensure_pairings()

    def _team_name(self, team_id: str) -> str:
        if team_id == PLAYER_ID: return "My Guild"
        tr = self.records.get(team_id)
        if tr and tr.team and hasattr(tr.team, "name"): return tr.team.name
        return team_id

    def get_standings_sorted(self) -> List[TeamRecord]:
        recs = list(self.records.values())
        recs.sort(key=lambda r: (r.points, r.elo, r.wins, -r.losses), reverse=True)
        if AUTO_RESOLVE_ON_QUERY and self._pending_matches:
            self.resolve_pending(max_matches=9999)
        return recs

    def _sorted_team_ids(self) -> List[str]:
        return [r.team_id for r in self.get_standings_sorted()]

    def _pair_neighbors(self, order: List[str]) -> List[Tuple[str, str]]:
        pairs = []
        i = 0
        while i < len(order) - 1:
            pairs.append((order[i], order[i + 1]))
            i += 2
        return pairs

    def _ensure_pairings(self):
        if self.current_round >= self.rounds_per_season:
            self._reset_season()
            return

        order = self._sorted_team_ids()
        if len(order) >= 4 and random.random() < 0.25:
            k = random.randrange(0, len(order) - 1)
            order[k], order[k + 1] = order[k + 1], order[k]

        pairs = self._pair_neighbors(order)
        self._current_pairings = pairs
        self._next_opponent_id = None
        for a, b in pairs:
            if a == PLAYER_ID: self._next_opponent_id = b; break
            if b == PLAYER_ID: self._next_opponent_id = a; break

        self._pending_matches.clear()
        self._pending_advance = False

    def _reset_season(self):
        for r in self.records.values():
            r.wins = r.losses = r.played = 0
            r.elo = DEFAULT_ELO
        self.current_round = 0
        self._played_matchups.clear()
        self._ensure_pairings()

    def _update_record(self, winner_id: str, loser_id: str):
        wr = self.records[winner_id]
        lr = self.records[loser_id]
        wr.played += 1; lr.played += 1
        wr.wins += 1; lr.losses += 1
        _elo_update(wr, lr, a_wins=True)
        
        # --- TALLENNA HISTORIA ---
        self.match_history.insert(0, {
            "winner": self._team_name(winner_id),
            "loser": self._team_name(loser_id),
            "round": self.current_round + 1
        })
        # Pidetään vain viimeiset 20 tulosta muistissa per liiga
        if len(self.match_history) > 20:
            self.match_history.pop()

    def _team_power(self, team_id: str) -> float:
        if team_id == PLAYER_ID: return 120.0
        t = self.records[team_id].team
        roster = _safe_roster(t)
        if not roster: return 80.0
        vals = [_unit_power(u) for u in roster if u]
        return sum(vals) / max(1, len(vals))

    def _match_win_prob(self, a: str, b: str) -> float:
        pa = self._team_power(a)
        pb = self._team_power(b)
        diff = max(-260.0, min(260.0, pa - pb))
        return max(0.08, min(0.92, 0.5 + (diff / 520.0)))

    def _simulate_match_mc(self, a: str, b: str) -> str:
        p = self._match_win_prob(a, b)
        wins = 0
        for _ in range(MC_TRIALS):
            if random.random() < p: wins += 1
        return a if wins > (MC_TRIALS // 2) else b

    def get_phase_label(self) -> str:
        return f"Round {self.current_round + 1}/{self.rounds_per_season}"

    def get_next_opponent_team(self):
        if AUTO_RESOLVE_ON_QUERY and self._pending_matches:
            self.resolve_pending(max_matches=9999)
        if self._pending_advance and not self._pending_matches:
            self._advance_round()
        if not self._next_opponent_id: return None
        rec = self.records.get(self._next_opponent_id)
        return rec.team if rec else None

    def has_pending_results(self) -> bool: return bool(self._pending_matches)
    def get_pending_count(self) -> int: return len(self._pending_matches)

    def resolve_pending(self, max_matches: int = 9999):
        n = 0
        while self._pending_matches and n < max_matches:
            a, b = self._pending_matches.pop(0)
            w = self._simulate_match_mc(a, b)
            l = b if w == a else a
            self._update_record(w, l)
            n += 1
        if self._pending_advance and not self._pending_matches:
            self._advance_round()

    def tick_simulation(self, budget_ms: float = 3.0, max_matches: int = 2):
        self.resolve_pending(max_matches)

    def _advance_round(self):
        self.current_round += 1
        self._ensure_pairings()

    def report_player_result(self, win: bool, enemy_team, match_stats: Optional[dict] = None):
        enemy_id = getattr(enemy_team, "team_id", None)
        if not enemy_id or enemy_id not in self.records:
             ename = getattr(enemy_team, "name", "Enemy")
             for tid, rec in self.records.items():
                 if tid != PLAYER_ID and rec.team and getattr(rec.team, "name", None) == ename:
                     enemy_id = tid
                     break
        
        if not enemy_id: return

        # Hall of Fame tilastointi
        if match_stats:
            for f in match_stats.get("fighters", []):
                n = f.get("name")
                if n:
                    self.hof_kills[n] = self.hof_kills.get(n, 0) + int(f.get("kills", 0) or 0)

        if win:
            self._update_record(PLAYER_ID, enemy_id)
        else:
            self._update_record(enemy_id, PLAYER_ID)

        self._pending_matches.clear()
        for a, b in self._current_pairings:
            if PLAYER_ID in (a, b): continue
            self._pending_matches.append((a, b))
        self._pending_advance = True

    def get_recent_matches(self, count=10):
        return self.match_history[:count]


class LeagueEngine:
    def __init__(self):
        self.tier = 1
        self.season_number = 1
        # Tier-nimet tulevat maailman loresta (lore/world_data.py).
        # LeagueEnginen tier 1 = loren Tier 0 (Muckford/Rookie Dust).
        try:
            from lore.world_data import ARENA_TIERS
            self.tier_names = {gt: ARENA_TIERS[gt - 1]["name"]
                               for gt in range(1, 7) if (gt - 1) in ARENA_TIERS}
        except Exception:
            self.tier_names = {
                1: "The Rookie Dust Circuit", 2: "The Scrapring Circuit",
                3: "The Iron Circle Circuit", 4: "The Steel Arena Circuit",
                5: "The Silver League Circuit", 6: "The Golden League"
            }
        self.TIER_NAMES = self.tier_names
        self.seasons: Dict[str, LeagueSeason] = {}
        self.simulation_progress: float = 1.0
        self.total_pending_start: int = 0
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            self._init_seasons()
            self._initialized = True

    def _init_seasons(self) -> None:
        self.seasons.clear()
        print("[LeagueEngine] Initializing seasons and generating teams...")
        for mode in ("1v1", "3v3", "5v5"):
            self.seasons[mode] = LeagueSeason(tier=self.tier)

    # --- SEASON CYCLE LOGIC ---
    def get_season_info(self) -> dict:
        self._ensure_initialized()
        """Palauttaa tiedot nykyisestä kaudesta ja vuodenajasta."""
        cycle_idx = (self.season_number - 1) // SEASONS_PER_THEME
        theme_idx = cycle_idx % len(SEASON_THEMES)
        theme = SEASON_THEMES[theme_idx]
        
        return {
            "number": self.season_number,
            "theme": theme,
            "tier": self.tier
        }

    def next_season(self):
        """Siirrytään seuraavaan kauteen (reset)."""
        self.season_number += 1
        self._initialized = False # Pakotetaan uudelleenlataus
        self._init_seasons()

    def get_tier_name(self, mode: str) -> str:
        if mode == "TOTAL": return "Grand Slam"
        return self.tier_names.get(self.tier, f"Tier {self.tier}")

    def get_phase_label(self, mode: str) -> str:
        self._ensure_initialized()
        s = self.seasons.get(mode)
        return s.get_phase_label() if s else ""

    def get_standings(self, mode: str) -> List[TeamRecord]:
        self._ensure_initialized()
        s = self.seasons.get(mode)
        return s.get_standings_sorted() if s else []

    def get_next_opponent(self, mode: str):
        self._ensure_initialized()
        s = self.seasons.get(mode)
        return s.get_next_opponent_team() if s else None

    def get_recent_matches(self, mode: str, count: int = 10):
        self._ensure_initialized()
        s = self.seasons.get(mode)
        return s.get_recent_matches(count) if s else []

    def prepare_battle(self, mode: str):
        """
        Kutsu tätä 'Next Match' -ruudussa.
        Lataa seuraavan vastustajan grafiikat muistiin ennen taistelua.
        """
        self._ensure_initialized()
        opp_team = self.get_next_opponent(mode)
        if opp_team and hasattr(opp_team, "load_team_assets"):
            opp_team.load_team_assets()

    # --- GRAND SLAM & PROMOTION ---
    def get_grand_score(self, team_id: str) -> dict:
        self._ensure_initialized()
        total_score = 0
        games = {}
        wins = 0; losses = 0
        for mode, season in self.seasons.items():
            rec = season.records.get(team_id)
            if rec:
                total_score += rec.wins * POINTS_PER_WIN.get(mode, 0)
                wins += rec.wins
                losses += rec.losses
                games[mode] = rec.played
            else:
                games[mode] = 0
        return {"id": team_id, "score": total_score, "games": games, "wins": wins, "losses": losses}

    def get_grand_slam_standings(self) -> List[dict]:
        self._ensure_initialized()
        all_ids = set()
        for season in self.seasons.values():
            all_ids.update(season.records.keys())

        standings = []
        for tid in all_ids:
            data = self.get_grand_score(tid)
            name = "Player" if tid == PLAYER_ID else tid
            if tid != PLAYER_ID:
                for season in self.seasons.values():
                    rec = season.records.get(tid)
                    if rec and rec.team and hasattr(rec.team, "name"):
                        name = rec.team.name
                        break
            data["team_name"] = name
            data["team_id"] = tid
            standings.append(data)

        standings.sort(key=lambda x: x["score"], reverse=True)
        return standings
    
    def get_grand_standings(self): return self.get_grand_slam_standings()

    def get_player_rank(self):
        standings = self.get_grand_slam_standings()
        for i, entry in enumerate(standings):
            if entry['team_id'] == PLAYER_ID:
                return i + 1
        return 99

    # --- UUSI: TARKISTAA ONKO KAUSI OHI ---
    def is_season_complete(self) -> bool:
        p_stats = self.get_grand_score(PLAYER_ID)
        for mode, req in REQ_GAMES.items():
            if p_stats["games"].get(mode, 0) < req:
                return False
        return True
    
    # --- UI HELPER: ONKO MOODI PELATTU? ---
    def is_mode_complete(self, mode: str) -> bool:
        if mode == "TOTAL": return False
        p_stats = self.get_grand_score(PLAYER_ID)
        return p_stats["games"].get(mode, 0) >= REQ_GAMES.get(mode, 999)

    def check_promotion_eligibility(self) -> Tuple[bool, str, object]:
        if not self.is_season_complete():
            p_stats = self.get_grand_score(PLAYER_ID)
            missing = []
            for mode, req in REQ_GAMES.items():
                played = p_stats["games"].get(mode, 0)
                if played < req: missing.append(f"{mode} ({played}/{req})")
            return False, f"Play more: {', '.join(missing)}", None

        rank = self.get_player_rank()
        if rank > 2: return False, f"Rank #{rank} (Need Top 2)", None

        standings = self.get_grand_slam_standings()
        opp_entry = standings[0]
        if opp_entry["team_id"] == PLAYER_ID:
            opp_entry = standings[1]
        
        opp_id = opp_entry["team_id"]
        
        # Etsi oikea vastustaja-olio
        real_team_obj = None
        for s in self.seasons.values():
            if opp_id in s.records:
                rec = s.records[opp_id]
                if rec.team:
                    real_team_obj = rec.team
                    break
        
        if real_team_obj:
            return True, "PROMOTION MATCH READY!", real_team_obj
        
        # Fallback jos ei löydy
        class BossTeamFallback:
            def __init__(self, name): 
                self.name = name
                self.team_id = "BOSS"
            def get_roster(self, n): return []
            
        return True, "PROMOTION MATCH READY!", BossTeamFallback(opp_entry['team_name'])

    def fail_season(self) -> str:
        """Kausi ohi ilman ylennystä. Jos pelaaja on korkeammalla tierillä
        (engine tier > 1 = yli lore Tier 0) ja sijoittui kentän alempaan
        puoliskoon, hänet pudotetaan tier alaspäin (relegaatio). Muuten kausi
        vain nollataan ja tier säilyy."""
        standings = self.get_grand_slam_standings()
        winner = standings[0]['team_name']
        if winner == "My Guild" or winner == "Player":
            winner = standings[1]['team_name']

        rank = self.get_player_rank()
        total = max(1, len(standings))

        # Relegaatio: pidä paikkasi tai putoat. Tier 1 (lore Tier 0) on pohja.
        if self.tier > 1 and rank > (total // 2):
            self.relegate_player()
            tier_name = self.tier_names.get(self.tier, f"Tier {self.tier}")
            return (f"{winner} won promotion. You finished #{rank} and were "
                    f"relegated to {tier_name}.")

        self.next_season()
        tier_name = self.tier_names.get(self.tier, f"Tier {self.tier}")
        return f"{winner} won promotion. Season reset — hold your ground in {tier_name}."

    def promote_player(self):
        self.tier = min(self.tier + 1, 6)
        self.next_season()
        return True

    def relegate_player(self):
        """Pudota yksi tier (ei koskaan alle 1 = lore Tier 0) ja aloita uusi kausi."""
        self.tier = max(self.tier - 1, 1)
        self.next_season()
        return True

    def report_match_result(self, mode: str, player_win: bool, enemy_team, match_stats: Optional[dict] = None, **kwargs):
        if mode == "PROMOTION":
            if player_win: self.promote_player()
            return player_win
        
        s = self.seasons.get(mode)
        if s: s.report_player_result(player_win, enemy_team, match_stats)

    def tick_simulation(self, budget_ms: float = 5.0, max_matches: int = 5):
        self._ensure_initialized()
        total_pending = sum(s.get_pending_count() for s in self.seasons.values())
        if total_pending > self.total_pending_start: self.total_pending_start = total_pending
        
        if self.total_pending_start == 0: self.simulation_progress = 1.0
        else:
            done = self.total_pending_start - total_pending
            self.simulation_progress = max(0.0, min(1.0, done / float(self.total_pending_start)))

        for s in self.seasons.values():
            s.tick_simulation(budget_ms, max_matches)

    def get_scout_report(self, enemy_team, player_roster=None) -> List[str]:
        """Tiedusteluraportti: nayttaa tiimin todellisen identiteetin
        (tyyli, maine, kokoonpano) ja arvioi uhan pelaajan tehoon nahden."""
        if not enemy_team:
            return ["No opponent."]
        name = getattr(enemy_team, "name", "Enemy")
        lines = [f"Opponent: {name}"]

        style = getattr(enemy_team, "style", None)
        if style:
            lines.append(f"Style: {style}")

        roster = _safe_roster(enemy_team)
        if roster:
            from collections import Counter
            races = Counter(getattr(u, "race_name", "?") for u in roster)
            comp = ", ".join(f"{n}x {r}" for r, n in races.most_common())
            avg_lvl = sum(getattr(u, "level", 1) for u in roster) / len(roster)
            lines.append(f"Squad: {len(roster)} fighters (avg Lv {avg_lvl:.0f})")
            lines.append(comp)

            enemy_pow = sum(_unit_power(u) for u in roster) / len(roster)
            # Pelaajan todellinen voima roosterista (jos annettu), muuten perustaso.
            if player_roster:
                pr = [u for u in player_roster if u]
                player_pow = (sum(_unit_power(u) for u in pr) / len(pr)) if pr else 120.0
            else:
                player_pow = 120.0
            ratio = enemy_pow / max(1.0, player_pow)
            if ratio < 0.85:
                threat = "Low - you outclass them"
            elif ratio < 1.1:
                threat = "Even - a real fight"
            elif ratio < 1.35:
                threat = "High - they have the edge"
            else:
                threat = "Severe - heavily favored"
            lines.append(f"Threat: {threat}")

        rep = getattr(enemy_team, "reputation", None)
        if rep:
            lines.append("")
            lines.append(f'"{rep}"')
        return lines

    # --- HALL OF FAME SUPPORT (TOP 10) ---
    def get_top_10_gladiators(self, player_roster=None):
        """
        Palauttaa listan Top 10 gladiaattoreista (Unit-olioita tai dummyja).
        Järjestetty tappojen (kills) mukaan.
        """
        self._ensure_initialized()
        all_stats = {} # name -> kills
        
        all_seasons = self.seasons.values()
        for season in all_seasons:
            for name, kills in season.hof_kills.items():
                if name not in all_stats:
                    all_stats[name] = 0
                if kills > all_stats[name]:
                    all_stats[name] = kills

        # Järjestä ja ota Top 10
        sorted_names = sorted(all_stats.keys(), key=lambda n: all_stats[n], reverse=True)[:10]
        
        top_units = []
        
        class HallOfFameDummy:
            def __init__(self, name, kills, team_name="Unknown"):
                self.name = name
                self.race_name = "Legend"
                self.level = "??"
                self.image = None
                self.hof_stats = {"kills": kills, "team_name": team_name}

        for name in sorted_names:
            kills = all_stats[name]
            found_unit = None
            found_team_name = "Unknown"
            
            # Etsi oikea olio
            for season in all_seasons:
                for rec in season.records.values():
                    if rec.team and hasattr(rec.team, "members"):
                        for unit in rec.team.members:
                            if getattr(unit, "name", "") == name:
                                found_unit = unit
                                found_team_name = getattr(rec.team, "name", "Unknown")
                                break
                    if found_unit: break
                if found_unit: break
            
            # Etsi pelaajan tiimistä jos ei löytynyt muualta
            if not found_unit and player_roster:
                for unit in player_roster:
                    if getattr(unit, "name", "") == name:
                        found_unit = unit
                        found_team_name = "Player's Guild"
                        break
            
            if found_unit:
                # Tallennetaan tiedot väliaikaisesti olioon UI:ta varten
                found_unit.hof_stats = {"kills": kills, "team_name": found_team_name}
                top_units.append(found_unit)
            else:
                top_units.append(HallOfFameDummy(name, kills, found_team_name))
                
        return top_units

    # Legacy-tuki
    def get_all_time_best_gladiator(self):
        top = self.get_top_10_gladiators()
        return top[0] if top else None