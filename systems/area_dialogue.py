# systems/area_dialogue.py
"""Muckford-tyylinen dialogipiirto seikkailualueille (Warrens, Low Fields,
Greywash Ford, Drowned Chapel, Kingsreach Toll, Old Mine...).

Alueet käyttävät yhteistä kevyttä sivudialogia (dialogue_active +
dialogue_name/pages/index). Aiemmin ne piirsivät pelkän tekstilaatikon -
tämä piirtää saman sisällön kaupungin chattien tyyliin: himmennetty
pelinäkymä, puhujan hahmo nostettuna esiin paneelin viereen ja nimikilpi.
"""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD_COLOR, WHITE, GRAY
from ui_kit import draw_text, font_main, font_small, font_header


# NPC-listojen tunnetut attribuutinimet eri alueilla
_NPC_LIST_ATTRS = ("npcs", "warrens_npcs", "mine_npcs", "chapel_npcs",
                   "ford_npcs", "toll_npcs", "area_npcs", "dynamic_props")


def _find_speaker(menu):
    """Etsii puhujan yksikön nimen perusteella alueen NPC-listoista."""
    name = str(getattr(menu, "dialogue_name", "") or "")
    if not name:
        return None
    def _matches(npc):
        # Villager liittää nimeen roolin: "Old Rinna Net (Farmer)"
        npc_name = str(getattr(npc, "name", "") or "")
        return npc_name == name or npc_name.startswith(name + " (") or \
            name.startswith(npc_name + " (")

    unit = getattr(menu, "dialogue_unit", None)
    if unit is not None and _matches(unit):
        return unit
    for attr in _NPC_LIST_ATTRS:
        for npc in getattr(menu, attr, None) or ():
            if _matches(npc) and getattr(npc, "image", None) is not None:
                return npc
    return None


def _wrap(text, font, width):
    lines = []
    current = ""
    for word in str(text).split():
        trial = word if not current else f"{current} {word}"
        if font.size(trial)[0] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_area_dialogue(menu, screen):
    """Piirtää aktiivisen aluedialogin. Palauttaa True jos dialogi on auki
    (kutsuja voi silloin ohittaa oman vanhan piirtonsa)."""
    if not getattr(menu, "dialogue_active", False):
        return False
    pages = getattr(menu, "dialogue_pages", None) or []
    if not pages:
        return False
    index = max(0, min(len(pages) - 1, int(getattr(menu, "dialogue_index", 0))))

    # Himmennys: pelinäkymä jää taustalle kuten kaupungin chateissa
    shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    shade.fill((0, 0, 0, 135))
    screen.blit(shade, (0, 0))

    panel = pygame.Rect(230, SCREEN_HEIGHT - 300, SCREEN_WIDTH - 460, 240)

    # Puhuja nostetaan esiin paneelin vasempaan reunaan
    speaker = _find_speaker(menu)
    if speaker is not None and getattr(speaker, "image", None):
        img = speaker.image
        # Enintään 4x natiivikoko, ettei pieni sprite muutu mössöksi
        target_h = min(300, img.get_height() * 4)
        scale = target_h / max(1, img.get_height())
        big = pygame.transform.scale(
            img, (int(img.get_width() * scale), target_h))
        frame = pygame.Rect(panel.x - 40, panel.y - big.get_height() + 60,
                            big.get_width() + 40, big.get_height() + 20)
        # Pehmeä valokehä hahmon taakse
        glow = pygame.Surface(frame.size, pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (240, 220, 160, 46),
                            glow.get_rect().inflate(-8, -30))
        screen.blit(glow, frame.topleft)
        screen.blit(big, (frame.x + 20, frame.y))

    # Tekstipaneeli
    body = pygame.Surface(panel.size, pygame.SRCALPHA)
    body.fill((22, 19, 26, 240))
    screen.blit(body, panel.topleft)
    pygame.draw.rect(screen, (168, 134, 78), panel, 3, border_radius=12)

    # Nimikilpi paneelin yläreunaan
    name = str(getattr(menu, "dialogue_name", "") or "???")
    plate_w = font_header.size(name)[0] + 44
    plate = pygame.Rect(panel.x + 26, panel.y - 26, plate_w, 46)
    pygame.draw.rect(screen, (34, 28, 22), plate, border_radius=9)
    pygame.draw.rect(screen, GOLD_COLOR, plate, 2, border_radius=9)
    draw_text(name, font_header, GOLD_COLOR, screen, plate.x + 22, plate.y + 6)

    # Sivun teksti
    y = panel.y + 40
    for line in _wrap(pages[index], font_main, panel.w - 60)[:5]:
        draw_text(line, font_main, WHITE, screen, panel.x + 30, y)
        y += 32

    # Sivuindikaattori + ohje
    if len(pages) > 1:
        draw_text(f"{index + 1}/{len(pages)}", font_small, GRAY, screen,
                  panel.right - 70, panel.y + 14)
    draw_text("[E / Enter] continue    [Esc] close", font_small, GRAY,
              screen, panel.right - 360, panel.bottom - 30)
    return True
