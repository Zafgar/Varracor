# tests/test_city.py
"""
Muckfordin kaupunkisimulaation testit: villagerit tekevät töitä,
eläimet elävät, eikä mikään kaadu. Yksi jaettu 2 minuutin simulaatio
(module-scoped fixture), jota vasten kaikki tarkistukset ajetaan.
"""
import pytest


@pytest.fixture(scope="module")
def simulated_city():
    """Aja kaupunkia 2 min pelimaailmaa ja palauta lopputila."""
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    manager = GameManager()
    city = MuckfordCityMenu(manager)
    for _ in range(7200):
        city.update()
    return manager, city


def test_city_boots_with_npcs_and_animals(simulated_city):
    _, city = simulated_city
    assert len(city.npcs) > 0, "kaupungissa ei ole villagereita"
    assert len(city.animals) > 0, "kaupungissa ei ole elaimia"


def test_manure_stays_bounded(simulated_city):
    from assets.tiles.farm_objects import Manure
    _, city = simulated_city
    manure = sum(1 for p in city.arena.props if isinstance(p, Manure))
    assert manure <= 30, f"lantaa liikaa: {manure}"


def test_villagers_work(simulated_city):
    _, city = simulated_city
    working = sum(1 for n in city.npcs
                  if getattr(getattr(n, "ai_controller", None), "state", 0) == 1)
    assert working > 0, "yksikaan villager ei ole toissa"


def test_villagers_produce_to_city_storage(simulated_city):
    manager, _ = simulated_city
    total = sum(manager.city_storage.values())
    assert total > 0, f"varastoon ei kertynyt mitaan: {manager.city_storage}"


def test_cows_survive_peacetime(simulated_city):
    from units.farm_animals import Cow
    _, city = simulated_city
    cows = [a for a in city.animals if isinstance(a, Cow)]
    assert cows and all(not c.is_dead for c in cows), "lehmia kuoli rauhan aikana"


def test_chicken_hatch_respects_population_cap(manager):
    """Deterministinen kattotesti: 12 kanan jälkeen munat eivät kuoriudu."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from units.farm_animals import Chicken
    from assets.tiles.farm_objects import Egg
    from settings import GREEN

    city = MuckfordCityMenu(manager)
    # Täytä populaatio kattoon
    while sum(1 for a in city.animals if isinstance(a, Chicken)) < 12:
        city.animals.append(Chicken(500, 500, team_color=GREEN))

    egg = Egg(510, 510)
    egg.hatch_timer = 1
    city.arena.props.append(egg)
    before = sum(1 for a in city.animals if isinstance(a, Chicken))

    for _ in range(5):
        city._update_eggs()

    after = sum(1 for a in city.animals if isinstance(a, Chicken))
    assert after == before, "muna kuoriutui vaikka populaatiokatto oli taynna"
    assert egg not in city.arena.props, "muna ei poistunut"


def test_farm_has_storage_and_manure_pile(simulated_city):
    """Regressio: nämä puuttuivat kartalta, jolloin lantaquest oli
    mahdoton suorittaa (ei paikkaa mihin dumpata)."""
    from assets.tiles.farm_objects import FarmStorage, ManurePile
    _, city = simulated_city
    assert any(isinstance(p, FarmStorage) for p in city.arena.props)
    assert any(isinstance(p, ManurePile) for p in city.arena.props)


def test_manure_quest_dump(manager):
    """Lantaquest etenee ja valmistuu kun lanta dumpataan kompostiin."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.farm_objects import ManurePile
    from quest_system import quest_manager

    city = MuckfordCityMenu(manager)
    q = quest_manager.get_quest("quest_manure_cleanup")
    quest_manager.accept_quest("quest_manure_cleanup")
    manager.inventory["Manure"] = 5

    pile = next(p for p in city.arena.props if isinstance(p, ManurePile))
    assert city._try_interact_prop(pile, check_collision=False)
    assert q.progress == 5
    assert q.status == "completed"


def test_eggs_stay_bounded(manager):
    """Munien määrä kartalla ei kasva rajatta (katto 20)."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.farm_objects import Egg
    from units.farm_animals import Chicken

    city = MuckfordCityMenu(manager)
    chickens = [a for a in city.animals if isinstance(a, Chicken)]
    for _ in range(40):
        for c in chickens:
            c.ai_controller.egg_timer = 0
            c.ai_controller._lay_egg(manager)
    eggs = sum(1 for p in city.arena.props if isinstance(p, Egg))
    assert eggs <= 20, f"munia kartalla {eggs} (katto 20)"


def test_arena_gate_and_bram(manager):
    """Shanty Yard -portti ja Bram ovat kaupungissa; E portilla avaa liigan."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import ShantyYardGate

    city = MuckfordCityMenu(manager)
    gate = next((p for p in city.arena.props if isinstance(p, ShantyYardGate)), None)
    assert gate is not None, "Shanty Yard -portti puuttuu kartalta"
    assert getattr(city, "bram", None) is not None, "Bram puuttuu"

    city.player.rect.center = (gate.rect.centerx, gate.rect.bottom + 40)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "league"


def test_poi_icons(manager):
    """POI-ikonit kattavat questin, kaupan, liigan, tavernan ja sepän."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(manager)
    kinds = {k for _, _, k in city._poi_icon_list()}
    assert "trade" in kinds       # Hamo
    assert "league" in kinds      # Bram + portti
    assert "tavern" in kinds
    assert "smith" in kinds
    assert any(k.startswith("quest") for k in kinds)  # Farmer Gus


def test_barracks_in_city_and_enter(manager):
    """Team Barracks on kartalla ja E avaa käveltävän sisätilan."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import TeamBarracks

    city = MuckfordCityMenu(manager)
    barr = next((p for p in city.arena.props if isinstance(p, TeamBarracks)), None)
    assert barr is not None, "Barracks puuttuu kartalta"
    assert getattr(city, "barracks", None) is barr

    city.player.rect.center = (barr.rect.centerx, barr.rect.bottom + 40)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "barracks_interior"


def test_barracks_menu_roster_and_equip(manager):
    """Barracks-menu näyttää roosterin ja ohjaa varusteisiin."""
    import pygame
    from menus.barracks_menu import BarracksMenu

    manager.recruit_initial_hero()
    bm = BarracksMenu(manager)
    roster = bm._roster()
    assert manager.player_character in roster
    assert len(roster) >= 2  # commander + hero

    # Equipment-nappi -> guild + return state (draw asettaa _last_draw_rect)
    import pygame as pg
    surf = pg.Surface((1920, 1080))
    bm.draw(surf)
    pos = bm.btn_equip._last_draw_rect.center
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    bm.handle_event(ev)
    assert bm.next_state == "guild"
    assert manager.guild_return_state == "barracks"


def test_village_task_full_flow(manager):
    """Kylätehtävä: hyväksy, kerää, toimita, lunasta palkinnot."""
    vt = manager.village_tasks
    assert vt is not None
    assert any(t.id == "grain_haul" for t in vt.available_for(0))

    assert vt.accept("grain_haul")
    manager.inventory["Grain Sack"] = 3
    assert vt.notify_collect(manager, "grain_haul")
    assert vt.try_deliver(manager, "grain_haul", "market")
    t = vt.get("grain_haul")
    assert t.status == "ready_turnin"
    gold0 = manager.gold
    gained = vt.complete(manager, "grain_haul")
    assert gained and manager.gold > gold0
    assert t.status == "done"


def test_village_task_fighter_reward(manager):
    """Tehtävä voi palkita taistelijalla."""
    vt = manager.village_tasks
    manager.reputation = 10
    assert vt.accept("lost_girl")
    assert vt.notify_reach("lost_girl", "forest_road")
    before = len(manager.my_team)
    vt.complete(manager, "lost_girl")
    assert len(manager.my_team) == before + 1


def test_village_tasks_persist(manager, tmp_path, monkeypatch):
    """Kylätehtävien tila säilyy tallennuksessa."""
    import save_manager
    monkeypatch.setattr(save_manager, "SAVE_DIR", str(tmp_path))
    monkeypatch.setattr(save_manager, "SAVE_FILE", str(tmp_path / "s.json"))

    manager.village_tasks.accept("grain_haul")
    assert save_manager.save_game(manager)

    from game_manager import GameManager
    m2 = GameManager()
    assert save_manager.load_game(m2)
    assert m2.village_tasks.get("grain_haul").status == "active"


def test_ambient_bard_event(manager):
    """Ambient-bardieventti käynnistyy ja päättyy siististi."""
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(manager)
    assert getattr(city, "stage", None) is not None
    city._update_ambient_event()
    city._event_timer = 2
    seen = False
    for _ in range(400):
        city.update()
        if city._event_state == "bard":
            seen = True
            break
    assert seen, "bardieventti ei kaynnistynyt"
    for _ in range(1300):
        city.update()
    assert city._event_state == "idle"


def test_deed_memory(manager):
    """Urotyöt muistetaan; tehtävän valmistuminen kirjaa urotyön."""
    assert manager.record_deed("d1", "did a heroic thing")
    assert manager.has_deed("d1")
    assert not manager.record_deed("d1", "dup")  # ei duplikaattia

    vt = manager.village_tasks
    vt.accept("grain_haul")
    manager.inventory["Grain Sack"] = 3
    vt.notify_collect(manager, "grain_haul")
    vt.try_deliver(manager, "grain_haul", "market")
    vt.complete(manager, "grain_haul")
    assert manager.has_deed("task_grain_haul")


def test_frog_smith_recruit_and_fights(manager):
    """Sammakko-seppä liittyy tehtävästä, asettaa has_smith, ja taistelee."""
    from settings import PLAYER_TEAM, ENEMY_TEAM
    from units.orc import Orc

    vt = manager.village_tasks
    manager.reputation = 30
    assert vt.accept("marsh_smith")
    manager.inventory["Iron Ingot"] = 2  # marsh_smith collect-vaihe vaatii Iron Ingotia
    assert vt.notify_collect(manager, "marsh_smith")
    before = len(manager.my_team)
    vt.complete(manager, "marsh_smith")
    assert len(manager.my_team) == before + 1
    assert manager.has_smith is True

    smith = [u for u in manager.my_team if getattr(u, "is_smith", False)][0]
    assert smith.race_name == "Frogfolk"
    assert smith.ai_controller is not None

    # Seppä taistelee liittolaisena
    smith.rect.center = (300, 500)
    foe = Orc("Foe", 360, 500, ENEMY_TEAM)
    manager.match_in_progress = True
    manager.all_units.add(smith, foe)
    hp0 = foe.current_hp
    for _ in range(600):
        for u in (smith, foe):
            if not u.is_dead:
                u.run_combat_ai(manager.all_units, None, manager=manager)
                u.update(None, manager=manager)
        manager.vfx.update(obstacles=None)
        if foe.current_hp < hp0:
            break
    assert foe.current_hp < hp0, "seppa ei tehnyt vahinkoa"


def test_notice_board_in_city(manager):
    """Ilmoitustaulu on kartalla ja E avaa sen."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    from assets.tiles.muckford_objects import NoticeBoard

    city = MuckfordCityMenu(manager)
    board = next((p for p in city.arena.props if isinstance(p, NoticeBoard)), None)
    assert board is not None
    assert getattr(city, "notice_board", None) is board

    city.player.rect.center = (board.rect.centerx, board.rect.bottom + 30)
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "notice_board"


def test_monster_loot_keys(manager):
    """Kaikki spawnattavat hirviöt mäppäytyvät LOOT_DROPS-avaimeen."""
    from settings import ENEMY_TEAM
    from units.undead_zombie import UndeadZombie
    from units.corrupted_crow import CorruptedCrow
    from units.rat_rider import RatRider
    from units.undead_skeleton_archer import UndeadSkeletonArcher
    from loot_data import LOOT_DROPS

    checks = [
        (UndeadZombie, "Zombie 2", "Zombie"),
        (CorruptedCrow, "Corrupted Crow", "Corrupted Crow"),
        (RatRider, "Rat Rider 1", "Rat Rider"),
        (UndeadSkeletonArcher, "Skeleton Archer 3", "Skeleton Archer"),
    ]
    for cls, nm, expected in checks:
        try:
            u = cls(nm, 0, 0, ENEMY_TEAM)
        except TypeError:
            u = cls(nm, 0, 0)
        u.name = nm
        key = manager._loot_key_for(u)
        assert key == expected, f"{nm} -> {key} (want {expected})"
        assert key in LOOT_DROPS, f"no drop table for {key}"


def test_forest_excursion_forage_and_exit(manager):
    """Whisper Marsh -retki: Bogwort-node kerätään ja pohjoisreuna palauttaa
    kaupunkiin. (Vanha herbs-lista korvautui MarshResourceNode-keräyksellä.)"""
    from citys.mucford.forest_excursion import ForestExcursionMenu
    fe = ForestExcursionMenu(manager)
    fe.on_enter()
    assert len(fe.monsters) > 0
    bogworts = [n for n in fe.arena.resources
                if n.resource_name == "Bogwort" and not n.harvested]
    assert bogworts, "suolla pitäisi kasvaa Bogwortia"

    node = bogworts[0]
    manager.player_character.rect.center = node.rect.center
    assert fe._try_gather() is True
    assert manager.inventory.get("Bogwort", 0) >= 1
    assert node.harvested

    # Pohjoisreuna palauttaa kaupunkiin
    manager.player_character.rect.top = 5
    fe.update()
    assert fe.next_state == "muckford_city"


def test_forest_gate_from_city(manager):
    """Kylän eteläportti vie metsäretkelle."""
    import pygame
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    city = MuckfordCityMenu(manager)
    fg = city._forest_gate_rect()
    city.player.rect.center = fg.center
    city.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert city.next_state == "forest_excursion"
