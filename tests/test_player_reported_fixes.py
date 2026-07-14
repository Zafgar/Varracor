# tests/test_player_reported_fixes.py
"""Pelaajan raportoimat viat:
1) pause-menusta pääsee optioneihin ja takaisin samaan kohtaan kaupunkia
2) cast ei enää laukaise melee-lyöntiä samalla klikkauksella
3) tyhjän spell-slotin valinta ei jumita meleetä
4) intro antaa 3 Vortex-kykyä (SeamCut, VortexWarp, RiftPulse) ja ne
   viedään pois steal_sword-kohtauksessa
5) dialogin taustalla näkyy pelinäkymä (snapshot), ei musta ruutu
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
import pytest

pygame.init()
pygame.display.set_mode((1920, 1080))


class _FakeKeys:
    def __init__(self, *down):
        self.down = set(down)

    def __getitem__(self, code):
        if code > 100000:
            raise IndexError(code)
        return code in self.down


def _battle_manager(plain_weapon=False):
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    m.mode = "Arena"
    m.start_match([m.player_character], 1)
    if plain_weapon:
        # VortexBlade on charge-ase (pito lataa, irtipäästö lyö) -
        # melee-testit tarvitsevat tavallisen miekan
        from items.swords.weak_sword import WeakSword
        hero = m.player_character
        hero.weapon_masteries.add("sword")
        hero.equipment["main_hand"] = WeakSword()
        hero.calculate_final_stats()
    return m


def _drive_input(monkeypatch, keys=None, mouse=(False, False, False),
                 pos=(960, 540)):
    monkeypatch.setattr(pygame.key, "get_pressed",
                        lambda: keys or _FakeKeys())
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda: mouse)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: pos)


def test_pause_menu_options_roundtrip_keeps_position():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.muckford_city_menu import MuckfordCityMenu
    m = GameManager()
    menu = MuckfordCityMenu(m)
    menu.on_enter()
    menu.player.rect.center = (1234, 987)
    menu.show_pause_menu = True
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                            pos=menu.btn_options.rect.center, button=1)
    menu.btn_options._last_draw_rect = menu.btn_options.rect
    menu.handle_event(ev)
    assert menu.next_state == "options"
    assert m.city_spawn_point == "keep"
    # Paluu: on_enter EI teleporttaa pelaajaa tavernan ovelle
    menu.next_state = None
    menu.on_enter()
    assert menu.player.rect.center == (1234, 987)
    # Normaali sisääntulo spawnaa taas normaalisti
    menu.on_enter()
    assert menu.player.rect.center != (1234, 987)


def test_cast_does_not_trigger_melee_on_same_click(monkeypatch):
    from spells.commander.rift_pulse import RiftPulse
    m = _battle_manager(plain_weapon=True)
    hero = m.player_character
    hero.equipment["spell1"] = RiftPulse()
    hero.spell_cooldowns["spell1"] = 0
    hero.current_mana = hero.max_mana

    # Valitse spell 1 näppäimellä
    _drive_input(monkeypatch, keys=_FakeKeys(pygame.K_1))
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.selected_spell_slot == "spell1"

    # LMB pohjaan: cast onnistuu, valinta poistuu
    mana0 = hero.current_mana
    _drive_input(monkeypatch, mouse=(True, False, False))
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.current_mana < mana0, "loitsu castattiin"
    assert hero.selected_spell_slot is None

    # LMB YHÄ pohjassa seuraavat framet: EI melee-lyöntiä eikä latausta
    w = hero.equipment.get("main_hand")
    for _ in range(5):
        hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.attack_cooldown == 0, "melee ei laukea castin perään"
    assert getattr(w, "charge_time", 0) == 0, "lataus ei ala castin perään"

    # Irtipäästö castin jälkeen EI myöskään laukaise release-lyöntiä
    _drive_input(monkeypatch)
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.attack_cooldown == 0, "release ei lyö castin perään"

    # Uusi paina+päästä -sykli: melee toimii (charge-ase lyö irtipäästöllä)
    _drive_input(monkeypatch, mouse=(True, False, False))
    for _ in range(3):
        hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    _drive_input(monkeypatch)
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.attack_cooldown > 0, "melee toimii uudella klikkauksella"


def test_empty_slot_cannot_be_selected_and_does_not_block_melee(monkeypatch):
    m = _battle_manager(plain_weapon=True)
    hero = m.player_character
    hero.equipment["spell2"] = None

    # Tyhjän slotin valinta ei mene päälle
    _drive_input(monkeypatch, keys=_FakeKeys(pygame.K_2))
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.selected_spell_slot is None

    # Vanhan bugin tilanne: valinta jäänyt tyhjään slottiin -> LMB
    # vapauttaa valinnan ja melee (paina+päästä) toimii taas
    hero.selected_spell_slot = "spell2"
    _drive_input(monkeypatch, mouse=(True, False, False))
    for _ in range(4):
        hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.selected_spell_slot is None
    w = hero.equipment.get("main_hand")
    assert getattr(w, "charge_time", 0) > 0, "ase latautuu taas pidossa"
    _drive_input(monkeypatch)
    hero.run_combat_ai(m.all_units, m.current_arena.obstacles, m)
    assert hero.attack_cooldown > 0, "melee toimii taas"


def test_intro_grants_three_vortex_spells_and_steal_removes_them():
    import main  # noqa: F401
    from game_manager import GameManager
    from citys.mucford.forest_road_menu import ForestRoadMenu
    from settings import CHEAT_MODE
    if CHEAT_MODE:
        pytest.skip("cheat mode ohittaa tutoriaaligrantin")
    m = GameManager()
    menu = ForestRoadMenu(m)
    menu.on_enter()
    p = menu.player
    assert type(p.equipment.get("spell1")).__name__ == "SeamCut"
    assert type(p.equipment.get("spell2")).__name__ == "VortexWarp"
    assert type(p.equipment.get("spell3")).__name__ == "RiftPulse"

    menu.handle_dialogue_effect("steal_sword")
    assert p.equipment.get("spell1") is None
    assert p.equipment.get("spell2") is None
    assert p.equipment.get("spell3") is None
    assert p.selected_spell_slot is None


def test_rift_pulse_damages_and_pushes_nearby_enemy():
    m = _battle_manager()
    from spells.commander.rift_pulse import RiftPulse
    hero = m.player_character
    enemy = next(iter(m.enemy_team))
    enemy.rect.center = (hero.rect.centerx + 80, hero.rect.centery)
    enemy.defense = 0
    hp0 = enemy.current_hp
    dist0 = abs(enemy.rect.centerx - hero.rect.centerx)
    spell = RiftPulse()
    assert spell.cast(hero, None, m) is True
    assert enemy.current_hp < hp0
    assert abs(enemy.rect.centerx - hero.rect.centerx) > dist0, "sinkoutui"
    # Kaukainen vihollinen ei kärsi
    enemy2 = None
    for e in m.enemy_team:
        if e is not enemy:
            enemy2 = e
    if enemy2 is None:
        return
    enemy2.rect.center = (hero.rect.centerx + 900, hero.rect.centery)
    hp2 = enemy2.current_hp
    hero.current_mana = hero.max_mana
    spell.cast(hero, None, m)
    assert enemy2.current_hp == hp2


def test_dialogue_draws_world_snapshot_behind():
    import main  # noqa: F401
    from game_manager import GameManager
    m = GameManager()
    # Snapshot: kirkkaan punainen "pelinäkymä"
    snap = pygame.Surface((1920, 1080))
    snap.fill((200, 30, 30))
    m.scene_snapshot = snap
    from units.villager import Villager
    from settings import GREEN
    npc = Villager("Testi Torvinen", "Human", 100, 100, team_color=GREEN)
    menu = m.open_patron_dialogue(npc, return_state="muckford_city")
    screen = pygame.Surface((1920, 1080))
    menu.draw(screen)
    r, g, b, *_ = screen.get_at((10, 10))
    assert r > 60 and g < 60, "taustalla näkyy himmennetty pelinäkymä"
    # Ilman snapshotia tausta on tumma mutta piirto ei kaadu
    m.scene_snapshot = None
    menu.draw(screen)
