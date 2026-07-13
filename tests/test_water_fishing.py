# tests/test_water_fishing.py
"""
Vesi ja kalastus: koodipiirretty lampi (pohja + animoidut kerrokset),
kulkuesteet laiturikaistaa lukuunottamatta, kalastussession tilakone,
Angler-taitojen vaikutus ja kalojen talousintegraatio.
"""
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from systems import fishing as fs


def _manager():
    import main  # noqa: F401
    from game_manager import GameManager
    return GameManager()


# ---------------------------------------------------------------- vesi

def test_water_body_builds_and_animates():
    from assets.tiles.water import WaterBody
    water = WaterBody(100, 100, 400, 260, seed=3)
    assert water.base.get_size() == (400, 260)
    surf = pygame.Surface((800, 600))
    for _ in range(10):
        water.update()
        water.draw(surf, (0, 0))
    water.splash(200, 200)
    assert len(water.ripples) >= 1, "roiske synnyttää väreilyrenkaan"
    # Ruudun ulkopuolella piirto ei kaadu (näkyvyysrajaus)
    water.draw(surf, (5000, 5000))


def test_pond_carved_with_walkable_jetty():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(m)
    city.on_enter()
    arena = city.arena
    assert hasattr(arena, "fishing_pond") and hasattr(arena, "fishing_spot")
    blockers = [o for o in arena.obstacles if getattr(o, "is_water", False)]
    assert len(blockers) == 3
    # Laiturin keskikohta kulkukelpoinen, syvä vesi ei
    jc = arena.fishing_jetty.center
    assert not any(b.rect.collidepoint(jc) for b in blockers)
    deep = (arena.fishing_pond.centerx, arena.fishing_pond.top + 15)
    assert any(b.rect.collidepoint(deep) for b in blockers)
    # Lammen alle ei jäänyt puita/esteitä
    for prop in arena.props:
        assert not arena.fishing_pond.contains(prop.rect), \
            f"{type(prop).__name__} jäi lammen alle"


# ---------------------------------------------------------------- sessio

def test_fishing_session_state_machine_with_reeling():
    s = fs.FishingSession(skill=0, rng=random.Random(1))
    assert s.state == "WAITING"
    # Liian aikainen isku säikäyttää (ei saalista, odotus alkaa alusta)
    assert s.hook() is None
    # Kelaa nykäisyyn
    s.timer = 1
    assert s.update() == "bite"
    assert s.state == "BITE"
    # Tartutus aloittaa väsytyksen
    assert s.hook() is True
    assert s.state == "REELING"
    assert s.pending_fish["name"] in {f["name"] for f in fs.FISH_SPECIES}
    # Kireyteen reagoiva kelaus (kuten pelaaja pelaa) nostaa saaliin ylös
    result = None
    for _ in range(6000):
        result = s.reel(s.tension < 70)
        if result:
            break
    assert result == "caught", "kireyttä vahtiva kelaus onnistuu"
    assert s.caught is not None
    assert s.state == "WAITING", "saaliin jälkeen uusi heitto"
    # Ikkunan ohitus -> escaped
    s.timer = 1
    s.update()
    s.timer = 1
    assert s.update() == "escaped"


def test_reeling_constant_pull_snaps_line_on_big_fish():
    """Tauoton kelaus isolla kalalla katkaisee siiman - minipeli vaatii
    rytmiä, ei nappulan pohjaan hakkaamista."""
    s = fs.FishingSession(skill=0, rng=random.Random(3), rod_tier=5)
    s.state = "BITE"
    s.timer = 10
    s.hook()
    s.pending_fish = dict(fs.FISH_SPECIES[-1])  # Blind Abyss Sturgeon (T5)
    result = None
    for _ in range(3000):
        result = s.reel(True)   # ei koskaan hellitä
        if result:
            break
    assert result == "snapped", "tauoton kiskominen katkaisee siiman"


def test_angler_skill_speeds_waits_and_extends_window():
    slow = fs.FishingSession(skill=0, rng=random.Random(9))
    fast = fs.FishingSession(skill=2, rng=random.Random(9))
    assert fast.timer < slow.timer, "Angler lyhentää odotusta"
    slow.timer = 1
    fast.timer = 1
    slow.update()
    fast.update()
    assert fast.timer > slow.timer, "Angler pidentää tartuntaikkunaa"


def test_angler_skill_improves_rare_catch():
    rng = random.Random(42)
    base = sum(1 for _ in range(3000)
               if fs.roll_fish(rng, 0)["name"] in ("Whisker Catfish", "Marsh Pike"))
    rng = random.Random(42)
    skilled = sum(1 for _ in range(3000)
                  if fs.roll_fish(rng, 2)["name"] in ("Whisker Catfish", "Marsh Pike"))
    assert skilled > base * 1.2, "harvinaiset yleistyvät taidolla"


# ---------------------------------------------------------------- kaupunki

def test_city_fishing_flow_catch_to_inventory():
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from items.item_registry import create_item
    city = MuckfordCityMenu(m)
    city.on_enter()
    spot = city.arena.fishing_spot
    city.player.rect.center = (spot[0] - 60, spot[1])

    # Ilman vapaa E ei aloita
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.fishing_session is None

    rod = create_item("FishingRod")
    assert rod is not None and rod.tool_type == "fishing"
    m.equipment_bag.append(rod)
    assert fs.has_rod(m) is True

    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.fishing_session is not None
    city.fishing_session.rng = random.Random(5)
    city.fishing_session.timer = 1
    city.update()
    assert city.fishing_session.state == "BITE"
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.fishing_session.state == "REELING", "tartunta aloitti väsytyksen"

    # Väsytys: simuloi E pohjassa rytmillä (monkeypatch näppäintila)
    session = city.fishing_session

    class _Keys:
        def __init__(self):
            self.frame = 0
        def __getitem__(self, key):
            return key == pygame.K_e and session.tension < 70
    fake = _Keys()
    real_get_pressed = pygame.key.get_pressed
    try:
        pygame.key.get_pressed = lambda: fake
        for i in range(3000):
            fake.frame = i
            city.update()
            if city.fishing_session.state != "REELING":
                break
    finally:
        pygame.key.get_pressed = real_get_pressed

    fish_names = {f["name"] for f in fs.FISH_SPECIES} | \
        {t["name"] for t in fs.TREASURES}
    caught = [k for k in m.inventory if k in fish_names]
    assert caught, "saalis (kala tai aarre) päätyi reppuun"

    # Piirto kesken session (koho + siima) ei kaadu
    surf = pygame.Surface((1920, 1080))
    city._update_camera()
    city.draw(surf)


def test_fish_economy_and_recipe():
    from lore.world_data import MARKET_PRICES
    for f in fs.FISH_SPECIES:
        assert MARKET_PRICES["sell"].get(f["name"]) == f["price"], \
            f"{f['name']} puuttuu myyntihinnoista"
    assert "Fishing Rod" in MARKET_PRICES["buy"]
    from citys.mucford.market_data import MARKET_SHOPS
    odd = [g["name"] for g in MARKET_SHOPS["oddments"]["goods"]]
    assert "Fishing Rod" in odd, "vapa myynnissä Kradilla"
    from citys.mucford.farming_expansion import MEAL_RECIPES
    assert "Mudwater Fish Stew" in MEAL_RECIPES
    assert "Mudfin" in MEAL_RECIPES["Mudwater Fish Stew"]["ingredients"]


def test_fishing_progression_levels_1_to_30():
    """Opittu kalastustaso: XP saaliista, tasot 1-30, tallentuu saveen."""
    import json
    m = _manager()
    st = fs.get_progress(m)
    assert st == {"level": 1, "xp": 0}
    leveled = False
    for _ in range(10):
        leveled |= fs.grant_catch_xp(m, {"xp": 20})
    assert leveled and fs.get_progress(m)["level"] > 1
    json.dumps(m.npc_state)  # save-yhteensopiva
    # Katto 30
    fs.get_progress(m)["level"] = fs.MAX_LEVEL
    assert fs.grant_catch_xp(m, {"xp": 999}) is False


def test_rod_tiers_gate_fish_pools_and_require_level():
    import random as _r
    from items.item_registry import create_item
    m = _manager()
    tiers = {"FishingRod": (1, 1), "BogwoodRod": (2, 7),
             "IronwireRod": (3, 13), "DuskwillowRod": (4, 20),
             "VortexlineRod": (5, 26)}
    for cls, (tier, req) in tiers.items():
        rod = create_item(cls)
        assert rod is not None, cls
        assert rod.tool_tier == tier and rod.fishing_level_required == req

    # Paras käytettävä vapa kunnioittaa opittua tasoa
    m.equipment_bag += [create_item("FishingRod"), create_item("VortexlineRod")]
    _rod, t = fs.best_rod(m)
    assert t == 1, "tason 1 kalastaja ei voi käyttää Vortexline-vapaa"
    fs.get_progress(m)["level"] = 30
    _rod, t = fs.best_rod(m)
    assert t == 5

    # Tier rajaa kalapoolin
    rng = _r.Random(1)
    t1 = {fs.roll_fish(rng, 0, 1)["name"] for _ in range(300)}
    assert t1 == {"Mudfin", "Bog Perch"}
    rng = _r.Random(1)
    t5 = {fs.roll_fish(rng, 3, 5)["name"] for _ in range(4000)}
    assert "Vortex Koi" in t5 and "Blind Abyss Sturgeon" in t5
    # Kaikilla kaloilla myyntihinta
    from lore.world_data import MARKET_PRICES
    for f in fs.FISH_SPECIES:
        assert MARKET_PRICES["sell"].get(f["name"]) == f["price"], f["name"]


def test_editor_paints_water_and_places_jetty():
    """Karttaeditori: raahaus = yhtenäinen vesialue (joki/järvi), laituri
    lisää kalastuspaikan, save/load säilyttää kaiken."""
    m = _manager()
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from tools.map_editor import MapEditor
    from assets.tiles.water import WaterBody, FishingJetty
    city = MuckfordCityMenu(m)
    city.on_enter()
    m.current_arena = city.arena
    ed = MapEditor(m)
    ed.active = True
    assert "Water" in ed.categories

    waters0 = sum(1 for p in city.arena.floor_props if isinstance(p, WaterBody))
    ed.selected_prop_class = WaterBody
    ed.execute_fill((1000, 2400), (1900, 2900))
    waters1 = sum(1 for p in city.arena.floor_props if isinstance(p, WaterBody))
    assert waters1 == waters0 + 1, "raahaus loi YHDEN altaan, ei ruudukkoa"

    spots0 = len(city.arena.fishing_spots)
    ed.selected_prop_class = FishingJetty
    ed.place_prop(980, 2600)
    assert len(city.arena.fishing_spots) == spots0 + 1

    tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "_water_proj.json")
    ed.save_project(tmp)
    ed.load_project(tmp)
    os.remove(tmp)
    waters2 = sum(1 for p in city.arena.floor_props if isinstance(p, WaterBody))
    jetties2 = sum(1 for p in city.arena.floor_props if isinstance(p, FishingJetty))
    assert waters2 == waters1 and jetties2 >= 2
    assert len(city.arena.fishing_spots) == spots0 + 1
    # Lähin laituri valikoituu pelaajan sijainnin mukaan
    spots = city.arena.fishing_spots
    river_spot = min(spots, key=lambda s: s[0])  # uusi jokilaituri (länsi)
    city.player.rect.center = (river_spot[0] - 40, river_spot[1])
    near = city._nearest_fishing_spot()
    assert near == river_spot, "uusi jokilaituri on lähin"


def test_fishing_skill_nodes_in_commander_tree():
    from skills.commander_skills_data import COMMANDER_SKILL_TREE
    assert "fishing_1" in COMMANDER_SKILL_TREE
    assert COMMANDER_SKILL_TREE["fishing_2"]["requires"] == ["fishing_1"]
    m = _manager()
    hero = m.player_character
    hero.unlocked_skills.update({"husbandry_1", "fishing_1", "fishing_2"})
    hero.calculate_final_stats()
    assert hero.fishing == 2
