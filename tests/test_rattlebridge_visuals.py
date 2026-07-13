# tests/test_rattlebridge_visuals.py
"""
Rattlebridgen koodigrafiikka-lorevisuaalit: sillan pilarit, Ironspan-tornit ja
ketjut, jättirattaat, proomut, punalyhtykujat + karanteeniteltat, Kruunun ja
sponsorien banderollit, vesirattaat, sumu - ja lorenmukainen väestö.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))


def _map():
    from citys.rattlebridge.rattlebridge_map import RattlebridgeCityMap
    return RattlebridgeCityMap()


def test_lore_setpieces_are_built():
    m = _map()
    assert len(m.piers) >= 8, "siltakaupungilla oltava kivipilarit vedessä"
    assert len(m.towers) == 2, "Ironspan-riipputornit"
    assert len(m.great_gears) >= 3, "Scrapringin jättirattaat"
    assert len(m.barges) >= 3
    assert len(m.red_lantern_lines) >= 3, "kuumeslummien punalyhdyt"
    assert len(m.crown_banners) >= 3, "Kruunun tullibanderollit"
    assert len(m.sponsor_banners) >= 5, "sponsoribannerit Scrapringissä"
    assert len(m.waterwheels) == 2
    assert len(m.fog_banks) >= 3, "Hush-Mantlen sumu"
    assert len(m.deck_stains) > 10


def test_sponsor_banners_use_sponsor_colors():
    from systems.sponsors import SPONSORS
    m = _map()
    colors = {color for _, _, color in m.sponsor_banners}
    assert colors == {s["banner"] for s in SPONSORS.values()}


def test_setpieces_do_not_add_collision():
    """Lore-visuaalit eivät saa muuttaa gameplay-törmäyksiä."""
    m = _map()
    for rect in m.quarantine_tents:
        assert rect not in m.obstacles


def test_full_scene_draws_at_every_district():
    m = _map()
    surf = pygame.Surface((1920, 1080))
    for rect in m.districts.values():
        cx, cy = rect.center
        offset = (max(0, min(m.width - 1920, cx - 960)),
                  max(0, min(m.height - 1080, cy - 540)))
        m.draw_background(surf, offset)
        m.draw_landmarks(surf, offset)
        m.draw_foreground(surf, offset)
    assert surf.get_bounding_rect().width == 1920


def test_population_races_match_lore():
    from citys.rattlebridge.rattlebridge_city_menu import RattlebridgeCityMenu
    races = set(RattlebridgeCityMenu.POPULATION_RACES)
    # Lore: kääpiöt, gnomit ja örkit ovat Rattlebridgessä yleisiä
    assert {"Dwarf", "Orc", "Gnome"} <= races
