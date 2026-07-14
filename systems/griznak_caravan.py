# systems/griznak_caravan.py
"""Griznakin vankkurit (pelitesti 23).

Griznak the Shifty kiertää kaupunkeja omilla vankkureillaan: hän on
AINA kaupungissa (Muckford, Rattlebridge, tulevat tier-kaupungit) ja
toimii swarm-/bossieventtien kuuluttajana sekä Killan urakoiden
antajana ja seuraajana. E vankkureilla avaa oikean Griznak-dialogin
(ChatMenu, sama kuin Killan tiskillä) - "[Show me the contracts]"
hyppää urakkalistaan ja palaa takaisin kaupunkiin.

Käyttö kaupunkivalikossa:
    from systems import griznak_caravan
    wagon, griznak = griznak_caravan.spawn(x, y)      # luonti
    griznak_caravan.open_chat(manager, "muckford_city")  # E-interakti
    griznak_caravan.world_events(manager)             # kuulutukset
"""
import math
import random

import pygame

from assets.tiles.prop import Prop
from settings import GREEN


class GriznakWagon(Prop):
    """Goblinikauppiaan katettu vankkuri: paikattu kangaskuomu, isot
    pyörät, roikkuva lyhty ja pääkallokoriste. Koodipiirretty fallback;
    oikea kuva pudotetaan assets-polkuun."""

    def __init__(self, x, y):
        w, h = 240, 170
        coll_rect = pygame.Rect(x + 14, y + h - 74, w - 28, 64)
        super().__init__(x, y, w, h,
                         img_path="assets/tiles/muckford/griznak_wagon.png",
                         color=(96, 74, 48), collision_rect=coll_rect)
        self.interaction_range = 130
        self.interaction_label = "Griznak's wagon"
        self._draw_procedural(w, h)

    def _draw_procedural(self, w, h):
        if not self.image or self.image.get_at((0, 0)) == (96, 74, 48, 255):
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            wood = (92, 66, 40)
            wood_d = (62, 44, 26)
            canvas = (168, 152, 118)
            patch = (128, 108, 82)
            # Pyörät
            for wx in (52, w - 52):
                pygame.draw.circle(surf, (40, 32, 22), (wx, h - 26), 26)
                pygame.draw.circle(surf, (80, 62, 40), (wx, h - 26), 26, 5)
                for a in range(0, 360, 45):
                    r = math.radians(a)
                    pygame.draw.line(surf, (80, 62, 40), (wx, h - 26),
                                     (wx + 20 * math.cos(r),
                                      h - 26 + 20 * math.sin(r)), 3)
            # Kori
            body = pygame.Rect(16, h - 86, w - 32, 52)
            pygame.draw.rect(surf, wood, body, border_radius=6)
            pygame.draw.rect(surf, wood_d, body, 3, border_radius=6)
            for lx in range(body.x + 18, body.right - 10, 26):
                pygame.draw.line(surf, wood_d, (lx, body.y + 4),
                                 (lx, body.bottom - 4), 2)
            # Kaareva kuomu
            hood = pygame.Rect(24, 12, w - 48, h - 86)
            pygame.draw.ellipse(surf, canvas, hood)
            pygame.draw.ellipse(surf, (108, 94, 70), hood, 3)
            pygame.draw.rect(surf, canvas, (hood.x, hood.centery,
                                            hood.w, hood.h // 2))
            # Paikat kuomussa
            pygame.draw.rect(surf, patch, (hood.x + 30, hood.y + 26, 26, 20))
            pygame.draw.rect(surf, patch, (hood.right - 66, hood.y + 40, 30, 22))
            pygame.draw.line(surf, (90, 76, 56), (hood.x + 30, hood.y + 36),
                             (hood.x + 56, hood.y + 36), 2)
            # Aisa
            pygame.draw.line(surf, wood_d, (10, h - 60), (46, h - 76), 6)
            # Roikkuva lyhty
            pygame.draw.line(surf, (50, 44, 34), (w - 30, 30), (w - 30, 52), 2)
            pygame.draw.rect(surf, (56, 48, 36), (w - 38, 52, 16, 20),
                             border_radius=3)
            pygame.draw.rect(surf, (255, 214, 120), (w - 34, 56, 8, 12))
            # Pääkallokoriste aisan päässä
            pygame.draw.circle(surf, (208, 200, 182), (14, h - 70), 8)
            pygame.draw.circle(surf, (30, 26, 22), (11, h - 72), 2)
            pygame.draw.circle(surf, (30, 26, 22), (17, h - 72), 2)
            # "CONTRACTS"-lauta korin kyljessä
            sign = pygame.Rect(body.centerx - 42, body.y + 10, 84, 26)
            pygame.draw.rect(surf, (150, 122, 78), sign, border_radius=4)
            pygame.draw.rect(surf, wood_d, sign, 2, border_radius=4)
            for i in range(5):
                pygame.draw.line(surf, (70, 54, 34),
                                 (sign.x + 8 + i * 15, sign.y + 8),
                                 (sign.x + 14 + i * 15, sign.y + 18), 2)
            self.image = surf


def make_griznak(x, y):
    """Luo Griznak-hahmon (staattinen NPC, ei taistelu-AI:ta)."""
    from units.goblin import Goblin
    g = Goblin("Griznak the Shifty", x, y, GREEN)
    g.ai_controller = None          # seisoo vankkureillaan
    g.is_griznak = True
    g.animation_state = "idle"
    return g


def spawn(x, y):
    """(wagon, griznak) valmiina lisättäväksi kaupungin kentälle.
    Griznak seisoo vankkurien edessä."""
    wagon = GriznakWagon(x, y)
    griznak = make_griznak(wagon.rect.centerx - 40, wagon.rect.bottom + 6)
    return wagon, griznak


def near_griznak(player, griznak, dist=120):
    if griznak is None:
        return False
    return math.hypot(player.rect.centerx - griznak.rect.centerx,
                      player.rect.centery - griznak.rect.centery) < dist


def open_chat(manager, return_state):
    """Avaa Griznakin oikean dialogin (ChatMenu) kaupungista käsin.
    Palauttaa menun (asetettu pending_dialogue_meniin) tai None."""
    menu = manager.open_dialogue("griznak_quest_giver")
    if menu is None:
        return None
    menu.return_state = return_state
    # "[Show me the contracts]" (goto:quests) palaa urakkalistalta
    # samaan kaupunkiin eikä areenahubiin
    manager.quests_return_state = return_state
    manager.pending_dialogue_menu = menu
    return menu


# ----------------------------------------------------------------------
# Kuulutukset: swarmit ja bossit jotka riehuvat pitäjillä
# ----------------------------------------------------------------------

def world_events(manager):
    """Lista Griznakin kuulutuksia aktiivisista uhista. Griznak on
    pelin 'uutistoimisto' - hän tietää missä parvet ja bossit liikkuvat."""
    events = []
    try:
        from quest_system import quest_manager
    except Exception:
        quest_manager = None

    def _status(qid):
        try:
            return quest_manager.get_quest_status(qid) if quest_manager \
                else ""
        except Exception:
            return ""

    # 1. Rat King & viemäriverkosto (pelitesti 24): Griznak aloittaa ja
    # seuraa Warrens-kriisilinjan joka johtaa Rat Kingin luo
    rk = _status("hunt_01")
    if rk not in ("completed", "finished", "turn_in"):
        w = _warrens_status(manager)
        if w is not None:
            stage, objective = w
            if stage <= 0:
                events.append("The sewer hatch behind the market is open. "
                              "The Rat King's Warrens run under all of "
                              "Muckford - clear them or the raids never "
                              "stop. Talk to Hamo at the cellar hatch.")
            elif stage >= 6:
                events.append("Word is the Rat King's crown is cracked. "
                              "Report to Hamo and Rinna to close it out.")
            else:
                events.append(f"Warrens crisis, stage {stage}/6: {objective}")
        else:
            clock = getattr(manager, "world_clock", None)
            nrd = int(getattr(manager, "next_raid_day", 0) or 0)
            if clock is not None and nrd:
                days = nrd - int(clock.day)
                if days <= 0:
                    events.append("Rat King's swarm is massing TODAY - "
                                  "watch the market carts!")
                else:
                    events.append(f"Rat King's next swarm hits Muckford in "
                                  f"~{days} day(s). His sewers stink of it.")
            else:
                events.append("The Rat King still squats under Muckford, "
                              "sending swarms for the grain.")

    # 2. Vortex-repeämät (rift-invaasioalueet ovat pysyvä riesa)
    events.append("Rifts keep tearing open at Whisper Marsh, the Drowned "
                  "Graveyard and Bogwood. Sealed ones pay in crystals.")

    # 3. Bossikontrahdit killalta
    try:
        from mission_data import BOSS_HUNTS
        if "boss_forest_troll" in BOSS_HUNTS:
            events.append("A troll haunts the woods south of town - it "
                          "shrugs off steel unless you bring fire.")
    except Exception:
        pass

    return events


def _warrens_status(manager):
    """(stage, objective) Warrens-kriisilinjasta, tai None jos ei alkanut."""
    try:
        from citys.mucford.muckford_warrens import (
            warrens_state, warrens_objective, sync_warrens_story)
        sync_warrens_story(manager)
        state = warrens_state(manager)
        if state.get("boss_defeated") or state.get("completed"):
            return None
        stage = int(state.get("quest_stage", 0))
        return stage, warrens_objective(manager)
    except Exception:
        return None
