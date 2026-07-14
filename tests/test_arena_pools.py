# tests/test_arena_pools.py
"""Areenapoolit: vähintään 3 areenaa joka tasolla, kaikilla reunaseinät
JA sisäesteitä jotka toimivat suojana myös ammuksia vastaan.
Regressio: Storm- ja SpikeArena eivät koskaan latautuneet (rikkinäinen
vfx-import) ja registry pudotti tier 2+:n pelkkään BasicArenaan."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame
pygame.init()
pygame.display.set_mode((1920, 1080))

from arenas import arena_registry as reg


def _cover_walls(arena):
    return [o for o in arena.obstacles
            if getattr(o, "type", "") == "wall"
            and o.rect.w <= 400 and o.rect.h <= 400]


def test_pools_have_three_real_arenas_per_tier():
    seen_names = {}
    for tier, pool in reg.TIER_POOLS.items():
        assert len(pool) >= 3, f"tier {tier} tarvitsee vähintään 3 areenaa"
        names = [c.__name__ for c in pool]
        assert len(set(names)) == len(names), f"tier {tier}: duplikaatteja {names}"
        seen_names[tier] = names
    # Fallback-regressio: näiden pitää olla omia luokkiaan, ei BasicArenaa
    assert "StormArena" in seen_names[2]
    assert "SpikeArena" in seen_names[3]
    assert "EmberQuarry" in seen_names[3]


def test_every_pool_arena_has_cover_and_draws():
    surf = pygame.Surface((1920, 1080))
    for tier, pool in reg.TIER_POOLS.items():
        for cls in pool:
            a = cls()
            walls = [o for o in a.obstacles if getattr(o, "type", "") == "wall"]
            assert len(walls) >= 4, f"{a.name}: reunaseinät puuttuvat"
            assert len(_cover_walls(a)) >= 3, f"{a.name}: liian vähän suojia"
            try:
                a.draw_background(surf)
            except TypeError:
                a.draw_background(surf, (0, 0))
            a.update([])
            try:
                a.draw_foreground(surf)
            except TypeError:
                a.draw_foreground(surf, (0, 0))


def test_cover_blocks_projectiles_but_lava_does_not():
    import main  # noqa: F401
    from vfx import Projectile
    from arenas.tier_3.ember_quarry import EmberQuarry
    a = EmberQuarry()
    pillar = _cover_walls(a)[0]

    # Nuoli suoraan suojan läpi -> tuhoutuu seinään
    start = (pillar.rect.centerx - 300, pillar.rect.centery)
    end = (pillar.rect.centerx + 300, pillar.rect.centery)
    p = Projectile(start[0], start[1], end, speed=12, damage=5, owner=None,
                   manager=None)
    group = pygame.sprite.Group(p)  # alive() vaatii ryhmäjäsenyyden
    for _ in range(120):
        p.update(a.obstacles)
        if not p.alive():
            break
    assert not p.alive(), "suoja pysäyttää ammuksen"
    assert p.rect.centerx <= pillar.rect.right, "pysähtyi suojan kohdalle"

    # Laavan yli nuoli lentää vapaasti
    lava = [o for o in a.obstacles if getattr(o, "type", "") == "lava"][0]
    p2 = Projectile(lava.rect.centerx - 300, lava.rect.centery,
                    (lava.rect.centerx + 300, lava.rect.centery),
                    speed=12, damage=5, owner=None, manager=None, duration=600)
    group2 = pygame.sprite.Group(p2)
    lava_only = [o for o in a.obstacles if getattr(o, "type", "") == "lava"]
    for _ in range(60):
        p2.update(lava_only)
    assert p2.alive(), "laava ei estä ammuksia"
    assert p2.rect.centerx > lava.rect.right


def test_storm_lightning_is_telegraphed_and_dodgeable():
    import main  # noqa: F401
    from arenas.tier_2.storm_arena import StormArena
    from units.human import Human
    from settings import GREEN
    a = StormArena()
    u = Human("Target", 0, 0, GREEN, "Common")
    u.rect.center = (900, 500)
    a.lightning_timer = 1
    a.update([u])            # telegraafi alkaa
    assert a.strike_warning > 0 and a.strike_pos is not None
    # Väistö: siirry kauas ennen iskua
    u.rect.center = (a.strike_pos[0] + 500, a.strike_pos[1])
    hp0 = u.current_hp
    for _ in range(60):
        a.update([u])
    assert u.current_hp == hp0, "telegraafattu salama on väisteltävissä"

    # Paikallaan seisova ottaa osuman
    a.lightning_timer = 1
    a.update([u])
    u.rect.center = a.strike_pos
    for _ in range(60):
        a.update([u])
        u.rect.center = (a.strike_pos or u.rect.center)  # pysy iskussa
        if u.current_hp < hp0:
            break
    assert u.current_hp < hp0


def test_spike_traps_warn_before_damage():
    import main  # noqa: F401
    from arenas.tier_3.spike_arena import SpikeArena
    from units.human import Human
    from settings import GREEN
    a = SpikeArena()
    trap = a.traps[0]
    u = Human("Stomper", 0, 0, GREEN, "Common")
    u.rect.center = trap["rect"].center
    hp0 = u.current_hp

    trap["timer"] = 1  # -> warn seuraavalla updatella
    a.update([u])
    assert trap["state"] == "warn"
    # Koko varoituksen ajan EI vahinkoa
    for _ in range(49):
        a.update([u])
    assert u.current_hp == hp0, "varoitusvaihe ei vahingoita"
    # Piikit nousevat -> vahinkoa
    for _ in range(60):
        a.update([u])
        if u.current_hp < hp0:
            break
    assert u.current_hp < hp0, "piikit vahingoittavat noustuaan"
