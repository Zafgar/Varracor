import pkgutil
import importlib
import leagues.premades  # Varmista, etta leagues/premades/__init__.py on olemassa


def _load_pkg(pkg_name, tier, flat_only=False):
    """Lataa create_team-tiimit annetusta paketista. flat_only ohittaa
    alipaketit (esim. tier1/) litteassa latauksessa."""
    try:
        pkg = importlib.import_module(pkg_name)
    except Exception:
        return []
    teams = []
    for _, name, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__ + "."):
        if flat_only and ispkg:
            continue
        try:
            module = importlib.import_module(name)
            if hasattr(module, "create_team"):
                team_obj = module.create_team(tier)
                if team_obj:
                    teams.append(team_obj)
                    print(f"[Loader] Loaded team: {team_obj.name}")
        except Exception as e:
            print(f"[Loader] ERROR loading team module '{name}': {e}")
    return teams


def load_all_premade_teams(tier):
    """Tier-tietoinen lataus. Engine tier N = lore tier N-1.
    Yrittaa ensin tier-kohtaista alipakettia (leagues.premades.tierK),
    muuten litteaa kansiota (Tier 0 / legacy)."""
    lore_tier = max(0, int(tier) - 1)
    sub = _load_pkg(f"leagues.premades.tier{lore_tier}", tier)
    if sub:
        return sub
    return _load_pkg("leagues.premades", tier, flat_only=True)
