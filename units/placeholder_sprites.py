# units/placeholder_sprites.py
"""Koodipiirretyt placeholder-spritet humanoidimonstereille.

Sama periaate kuin tier0_monsters.CodeMonster-piirroissa: jokaisella
olennolla on luettava siluetti pygame-primitiiveillä, jotta peli on heti
pelattavissa ilman asset-tiedostoja. Yksiköt kutsuvat näitä
_load_sprites-fallbackissa ja täyttävät vain PUUTTUVAT tilat, joten
oikeat maalatut spritet ohittavat placeholderit automaattisesti kun
ne joskus lisätään.
"""
from __future__ import annotations

from typing import Dict, Tuple

import pygame

Color = Tuple[int, int, int]


def _shade(color: Color, amount: int) -> Color:
    return tuple(max(0, min(255, c + amount)) for c in color)


def humanoid_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
    *,
    weapon: str = "none",  # "none" | "sword" | "bow"
) -> Dict[str, pygame.Surface]:
    """Piirtää humanoidin tilat: idle, run, attack, hit, aim, shoot.

    Siluetti: pää + torso + kädet + jalat. 'weapon' lisää aseen ääriviivan
    (miekka sivulla / jousikaari edessä), jotta rooli näkyy yhdellä
    silmäyksellä.
    """
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "attack", "hit", "aim", "shoot"):
        frames[state] = _draw_humanoid(size, body, accent, eye, weapon, state)
    return frames


def _draw_humanoid(size, body, accent, eye, weapon, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2
    tone = _shade(body, 55) if state == "hit" else body
    lean = {"attack": 3, "shoot": 2, "hit": -3}.get(state, 0)

    head_r = max(5, w // 5)
    head_y = head_r + 2
    torso_top = head_y + head_r - 1
    torso_h = int(h * 0.42)
    leg_top = torso_top + torso_h

    # Jalat (run-tila levittää askeleen)
    spread = 6 if state == "run" else 3
    pygame.draw.line(s, _shade(tone, -25), (cx + lean, leg_top),
                     (cx - spread, h - 3), 4)
    pygame.draw.line(s, _shade(tone, -25), (cx + lean, leg_top),
                     (cx + spread + lean, h - 3), 4)

    # Torso
    pygame.draw.line(s, tone, (cx, torso_top), (cx + lean, leg_top), 6)
    # Rintakehä/haarniskavihje
    for i in range(3):
        y = torso_top + 4 + i * 6
        pygame.draw.line(s, accent, (cx - 5, y), (cx + 5 + lean, y), 2)

    # Kädet
    arm_y = torso_top + 5
    if state in ("attack",):
        # Isku: etukäsi ojennettuna
        pygame.draw.line(s, tone, (cx, arm_y), (cx + w // 3, arm_y - 2), 4)
        pygame.draw.line(s, tone, (cx, arm_y), (cx - w // 5, arm_y + 8), 4)
    elif state in ("aim", "shoot"):
        pygame.draw.line(s, tone, (cx, arm_y), (cx + w // 3, arm_y + 2), 4)
        pygame.draw.line(s, tone, (cx, arm_y), (cx + w // 6, arm_y + 4), 4)
    else:
        pygame.draw.line(s, tone, (cx, arm_y), (cx - w // 4, arm_y + 10), 4)
        pygame.draw.line(s, tone, (cx, arm_y), (cx + w // 4, arm_y + 10), 4)

    # Ase
    if weapon == "sword":
        hand = (cx + w // 4, arm_y + 10)
        if state == "attack":
            hand = (cx + w // 3, arm_y - 2)
        pygame.draw.line(s, _shade(accent, 60), hand,
                         (hand[0] + 6, hand[1] - 12), 3)
    elif weapon == "bow":
        bow_x = cx + w // 3
        rect = pygame.Rect(bow_x - 4, arm_y - 10, 10, 24)
        pygame.draw.arc(s, _shade(accent, 60), rect, -1.2, 1.2, 2)
        if state in ("aim", "shoot"):
            pygame.draw.line(s, _shade(accent, 60), (bow_x, arm_y - 9),
                             (bow_x, arm_y + 13), 1)

    # Pää + silmät
    pygame.draw.circle(s, tone, (cx + lean, head_y), head_r)
    pygame.draw.circle(s, accent, (cx + lean, head_y), head_r, 1)
    for ex in (-3, 3):
        pygame.draw.circle(s, eye, (cx + lean + ex, head_y - 1), 2)
    return s


def quadruped_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
) -> Dict[str, pygame.Surface]:
    """Piirtää nelijalkaisen (rotta tms.) tilat: idle, run, attack, hurt."""
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "attack", "hurt"):
        frames[state] = _draw_quadruped(size, body, accent, eye, state)
    return frames


def _draw_quadruped(size, body, accent, eye, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone = _shade(body, 55) if state == "hurt" else body
    stretch = {"run": 4, "attack": 6}.get(state, 0)

    body_rect = pygame.Rect(w // 8, h // 3, int(w * 0.6) + stretch, int(h * 0.42))
    # Häntä
    pygame.draw.line(s, _shade(tone, -30), (body_rect.left + 3, body_rect.centery),
                     (1, body_rect.centery - h // 5), 2)
    # Vartalo + selkäkaari
    pygame.draw.ellipse(s, tone, body_rect)
    pygame.draw.arc(s, accent, body_rect.inflate(-4, -4), 0.3, 2.8, 2)
    # Pää + kuono + korva
    head = (body_rect.right - 2, body_rect.top + 2)
    pygame.draw.circle(s, tone, head, max(5, w // 7))
    snout_len = 8 + (4 if state == "attack" else 0)
    pygame.draw.polygon(s, tone, [
        (head[0] + 2, head[1] - 4),
        (head[0] + snout_len + 4, head[1] + 2),
        (head[0] + 2, head[1] + 5),
    ])
    pygame.draw.circle(s, accent, (head[0] - 3, head[1] - 7), 3)
    pygame.draw.circle(s, eye, (head[0] + 2, head[1] - 1), 2)
    # Jalat
    leg_spread = 3 if state == "run" else 0
    for i, fx in enumerate((body_rect.left + 6, body_rect.centerx - 2,
                            body_rect.right - 8)):
        off = leg_spread if i % 2 else -leg_spread
        pygame.draw.line(s, _shade(tone, -25), (fx, body_rect.bottom - 2),
                         (fx + off, h - 2), 3)
    return s


def leech_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
) -> Dict[str, pygame.Surface]:
    """Segmentoitu iilimato: idle, run, attack, hurt."""
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "attack", "hurt"):
        frames[state] = _draw_leech(size, body, accent, eye, state)
    return frames


def _draw_leech(size, body, accent, eye, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone = _shade(body, 55) if state == "hurt" else body
    arch = {"run": 4, "attack": 2}.get(state, 0)
    # Segmentit hännästä päähän (pää oikealla)
    segs = 5
    for i in range(segs):
        t = i / (segs - 1)
        r = int(4 + t * (h // 3))
        x = int(4 + t * (w - 14))
        y = h // 2 - int(arch * (1 - abs(2 * t - 1)))
        pygame.draw.circle(s, tone, (x, y), r)
        if i:
            pygame.draw.circle(s, accent, (x, y), r, 1)
    # Imukuono
    head_x = w - 10
    mouth = 5 + (3 if state == "attack" else 0)
    pygame.draw.circle(s, _shade(tone, -35), (head_x + 4, h // 2), mouth, 2)
    pygame.draw.circle(s, eye, (head_x - 2, h // 2 - 4), 2)
    return s


def frog_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
) -> Dict[str, pygame.Surface]:
    """Iso sammakko: idle, run, attack, hurt."""
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "attack", "hurt"):
        frames[state] = _draw_frog(size, body, accent, eye, state)
    return frames


def _draw_frog(size, body, accent, eye, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone = _shade(body, 55) if state == "hurt" else body
    crouch = {"run": -6, "attack": -4}.get(state, 0)
    cy = int(h * 0.55) + crouch // 2
    # Takajalat
    pygame.draw.ellipse(s, _shade(tone, -25), (2, cy + 4, w // 3, h // 4))
    pygame.draw.ellipse(s, _shade(tone, -25), (w - w // 3 - 2, cy + 4, w // 3, h // 4))
    # Vartalo
    pygame.draw.ellipse(s, tone, (w // 8, cy - h // 4, int(w * 0.75), h // 2 - crouch))
    # Silmäkohoumat
    for ex in (int(w * 0.3), int(w * 0.62)):
        pygame.draw.circle(s, accent, (ex, cy - h // 4), max(4, w // 9))
        pygame.draw.circle(s, eye, (ex, cy - h // 4 - 1), 3)
    # Kieli iskussa
    if state == "attack":
        pygame.draw.line(s, (210, 110, 120), (w // 2, cy),
                         (w - 4, cy - h // 6), 3)
    # Täplät
    for px, py in ((int(w * 0.4), cy + 2), (int(w * 0.55), cy + 6)):
        pygame.draw.circle(s, _shade(tone, 40), (px, py), 3)
    return s


def bird_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
) -> Dict[str, object]:
    """Lintu (varis): idle=[2 framea], fly=[4], attack, hurt.

    HUOM: palauttaa CorruptedCrow'n odottaman rakenteen, jossa idle ja
    fly ovat frame-LISTOJA ja attack/hurt yksittäisiä pintoja."""
    idle = [_draw_bird(size, body, accent, eye, "idle", i) for i in range(2)]
    fly = [_draw_bird(size, body, accent, eye, "fly", i) for i in range(4)]
    return {
        "idle": idle,
        "fly": fly,
        "attack": _draw_bird(size, body, accent, eye, "attack", 0),
        "hurt": _draw_bird(size, body, accent, eye, "hurt", 0),
    }


def _draw_bird(size, body, accent, eye, state, frame) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone = _shade(body, 55) if state == "hurt" else body
    cy = h // 2
    # Siivet (räpytys vaiheen mukaan)
    flap = (-6, -2, 3, -2)[frame % 4] if state == "fly" else (frame % 2) * 2 - 1
    pygame.draw.polygon(s, accent, [
        (w // 2, cy), (4, cy - 6 + flap), (w // 3, cy + 3)])
    pygame.draw.polygon(s, accent, [
        (w // 2, cy), (w - 4, cy - 6 + flap), (w - w // 3, cy + 3)])
    # Vartalo + pää + nokka
    pygame.draw.ellipse(s, tone, (w // 3, cy - 4, w // 3, h // 3))
    head = (w // 2 + 4, cy - 5)
    pygame.draw.circle(s, tone, head, 5)
    beak_len = 7 if state == "attack" else 5
    pygame.draw.polygon(s, (200, 160, 60), [
        (head[0] + 3, head[1] - 2), (head[0] + 3 + beak_len, head[1]),
        (head[0] + 3, head[1] + 2)])
    pygame.draw.circle(s, eye, (head[0] + 1, head[1] - 1), 2)
    return s


def horror_frames(
    size: Tuple[int, int],
    body: Color,
    accent: Color,
    eye: Color,
) -> Dict[str, pygame.Surface]:
    """Leijuva kauhio (Mnemonic Devourer): idle, run, attack, cast, hurt."""
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "attack", "cast", "hurt"):
        frames[state] = _draw_horror(size, body, accent, eye, state)
    return frames


def _draw_horror(size, body, accent, eye, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone = _shade(body, 55) if state == "hurt" else body
    cx, cy = w // 2, int(h * 0.4)
    r = min(w, h) // 3
    # Lonkerot alas
    reach = 6 if state in ("attack", "cast") else 2
    for i, dx in enumerate((-r + 2, -r // 2, 0, r // 2, r - 2)):
        end_y = h - 3 - (i % 2) * 4
        pygame.draw.line(s, _shade(tone, -25), (cx + dx // 1, cy + r - 3),
                         (cx + dx + (reach if i % 2 else -reach), end_y), 3)
    # Pääkuori
    pygame.draw.circle(s, tone, (cx, cy), r)
    pygame.draw.circle(s, accent, (cx, cy), r, 2)
    # Iso keskussilmä + pikkusilmät
    pygame.draw.circle(s, (240, 238, 225), (cx, cy), r // 2)
    pygame.draw.circle(s, eye, (cx, cy), r // 4)
    for ex, ey in ((cx - r + 3, cy - 4), (cx + r - 3, cy - 4)):
        pygame.draw.circle(s, eye, (ex, ey), 2)
    # Cast-hehku
    if state == "cast":
        pygame.draw.circle(s, _shade(accent, 70), (cx, cy), r + 4, 2)
    return s


def rider_frames(
    size: Tuple[int, int],
    mount: Color,
    rider: Color,
    eye: Color,
) -> Dict[str, pygame.Surface]:
    """Piirtää ratsastajan tilat: idle, run, charge_1, charge_2, throw, hurt."""
    frames: Dict[str, pygame.Surface] = {}
    for state in ("idle", "run", "charge_1", "charge_2", "throw", "hurt"):
        frames[state] = _draw_rider(size, mount, rider, eye, state)
    return frames


def _draw_rider(size, mount, rider, eye, state) -> pygame.Surface:
    w, h = size
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    tone_m = _shade(mount, 55) if state == "hurt" else mount
    tone_r = _shade(rider, 55) if state == "hurt" else rider
    stretch = {"charge_1": -6, "charge_2": 10, "run": 4}.get(state, 0)

    # Ratsu: iso rotan vartalo + kuono + häntä
    body_rect = pygame.Rect(w // 6, h // 2, int(w * 0.62) + stretch, h // 3)
    pygame.draw.ellipse(s, tone_m, body_rect)
    nose = (body_rect.right + 6, body_rect.centery - 4)
    pygame.draw.polygon(s, tone_m, [
        (body_rect.right - 8, body_rect.top + 4),
        nose,
        (body_rect.right - 6, body_rect.bottom - 6),
    ])
    pygame.draw.line(s, _shade(tone_m, -30), (body_rect.left + 4, body_rect.centery),
                     (2, body_rect.centery - 10), 3)  # häntä
    # Jalat
    for fx in (body_rect.left + 10, body_rect.centerx, body_rect.right - 12):
        pygame.draw.line(s, _shade(tone_m, -25), (fx, body_rect.bottom - 3),
                         (fx - 2, h - 2), 3)
    pygame.draw.circle(s, eye, (body_rect.right - 4, body_rect.top + 8), 2)

    # Ratsastaja: huppupää + torso ratsun selässä
    rx = body_rect.centerx - 4
    ry = body_rect.top - 2
    pygame.draw.line(s, tone_r, (rx, ry), (rx + 3, ry - h // 4), 5)  # torso
    pygame.draw.circle(s, tone_r, (rx + 4, ry - h // 4 - 4), 6)      # pää
    pygame.draw.circle(s, eye, (rx + 6, ry - h // 4 - 5), 2)

    # Keihäs rynnäkössä, pommi heitossa
    if state in ("charge_1", "charge_2"):
        pygame.draw.line(s, _shade(tone_r, 70), (rx - 6, ry - h // 6),
                         (rx + w // 3, ry - h // 5), 3)
    elif state == "throw":
        pygame.draw.circle(s, (40, 40, 45), (rx + 14, ry - h // 3), 5)
        pygame.draw.line(s, (230, 160, 60), (rx + 14, ry - h // 3 - 5),
                         (rx + 17, ry - h // 3 - 10), 2)
    return s
