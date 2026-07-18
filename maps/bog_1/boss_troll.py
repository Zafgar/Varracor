# maps/bog_1/boss_troll.py
"""Forest Troll -bossitaistelu Rotmiren suolla (pelitesti 30).

Aiemmin boss_forest_troll oli BOSS_HUNTS-listassa mutta EI missään
mission-rekisterissä -> start_boss_hunt palautti hiljaa Nonen ja koko
questi oli rikki. Nyt bossilla on oikea taistelu:

- Ladataan uusittu Bog-areena (vesineen ja peikon pesineen).
- Forest Troll odottaa pesällään (arena.lair_rect); pelaaja astuu sisään
  sisäänkäynniltä. Muutama Giant Rat vartioi.
- Peikko paranee ajan myötä (units/troll.py regen) ellei sitä polteta -
  lore-vihje "bring fire" toteutuu itse Troll-luokan mekaniikassa.
"""
import random

import maps.bog_1.vfx as bog_vfx
from units.monster_registry import create_monster
from settings import ENEMY_TEAM


class MissionLogic:
    def __init__(self, mission_data):
        self.data = mission_data or {}
        self.handles_positioning = True
        self._troll = None

    def setup(self, manager):
        manager.enemy_team.empty()
        manager.all_units.empty()
        for u in manager.active_player_units:
            manager.all_units.add(u)

        arena = manager.current_arena

        # Kartan propit peliin (portti + kerättävät nodet) neutraaleina
        for p in getattr(arena, "props", []):
            if not hasattr(p, "run_combat_ai"):
                p.run_combat_ai = lambda *a, **k: None
            if not hasattr(p, "take_damage"):
                p.take_damage = lambda *a, **k: 0
            p.team_color = "Neutral"
            manager.all_units.add(p)

        # Pelaaja sisään sisäänkäynniltä (lounas)
        entry = getattr(arena, "entrance_point", (350, arena.height - 420))
        for i, unit in enumerate(list(manager.active_player_units)):
            unit.is_dead = False
            unit.current_hp = unit.max_hp
            unit.rect.center = (entry[0], entry[1] - 90 * (i - 1))

        manager.camera_x = entry[0] - 640
        manager.camera_y = entry[1] - 360

        # Forest Troll pesällään (koillinen)
        lair = getattr(arena, "lair_rect", None)
        tx, ty = (lair.center if lair else (arena.width - 700,
                                            arena.height // 2))
        troll = create_monster("Forest Troll", tx, ty, ENEMY_TEAM)
        troll.is_boss = True
        if hasattr(troll, "assign_manager"):
            troll.assign_manager(manager)
        self._troll = troll
        manager.enemy_team.add(troll)
        manager.all_units.add(troll)

        # Vartijarotat pesän edustalle
        for i in range(3):
            gx = tx + random.randint(-200, -80)
            gy = ty + random.randint(-160, 160)
            rat = create_monster("Giant Rat", gx, gy, ENEMY_TEAM)
            manager.enemy_team.add(rat)
            manager.all_units.add(rat)

    def update(self, manager):
        pass

    def is_finished(self, manager):
        return self._troll is not None and self._troll.is_dead


def setup(manager):
    """Boss_registryn kutsuma sisäänkäynti."""
    import maps.bog_1.arena as b_arena
    manager.current_arena = b_arena.Arena()
    manager.current_mission_logic = MissionLogic(manager.selected_mission)
    manager.current_map_vfx = bog_vfx.MapVFX()
    manager.current_mission_logic.setup(manager)
