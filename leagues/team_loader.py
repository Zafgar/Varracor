import pkgutil
import importlib
import leagues.premades  # Varmista, että leagues/premades/__init__.py on olemassa

def load_all_premade_teams(tier):
    """
    Lataa dynaamisesti kaikki tiimit 'leagues/premades' -kansiosta.
    Kutsuu jokaisen moduulin 'create_team(tier)' -funktiota.
    """
    teams = []
    
    # Määritetään polku ja etuliite moduulien lataamista varten
    path = leagues.premades.__path__
    prefix = leagues.premades.__name__ + "."

    # Käydään läpi kaikki tiedostot premades-kansiossa
    for _, name, _ in pkgutil.iter_modules(path, prefix):
        try:
            # Yritetään ladata moduuli (esim. leagues.premades.rusty_buckets)
            module = importlib.import_module(name)
            
            # Tarkistetaan, onko moduulissa vaadittu funktio
            if hasattr(module, "create_team"):
                team_obj = module.create_team(tier)
                if team_obj:
                    teams.append(team_obj)
                    print(f"[Loader] Successfully loaded team: {team_obj.name}")
            
        except Exception as e:
            # Tulostetaan virhe, mutta ei kaadeta peliä.
            # Tämä auttaa löytämään vialliset tiimitiedostot (esim. väärä item-nimi).
            print(f"[Loader] CRITICAL ERROR loading team module '{name}': {e}")

    return teams