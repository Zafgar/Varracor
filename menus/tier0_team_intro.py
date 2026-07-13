"""First-visit presentation art for the Rookie Dust Circuit teams.

The screen prefers hand-painted replacement PNGs from
``assets/ui/team_intros/tier0/<team-slug>.png``. Until those exist it builds
full 16:9 team portraits directly from the live league roster: race, armour,
main-hand weapon, shield and team colour all come from the same objects that
will fight in the arena.
"""
from __future__ import annotations

import math
import os
import re

import pygame


INTRO_FLAG = "tier0_team_portraits_seen"
OVERRIDE_DIR = os.path.join("assets", "ui", "team_intros", "tier0")


TEAM_PALETTES = {
    "Shanty Yard Saints": ((52, 49, 43), (127, 103, 57), (205, 179, 108)),
    "Muckford Ratcatchers": ((48, 26, 25), (118, 50, 41), (214, 143, 86)),
    "The Unclaimed Five": ((34, 25, 28), (105, 38, 45), (196, 101, 84)),
    "The Ragged Lanterns": ((21, 43, 32), (54, 105, 65), (218, 177, 76)),
    "Croak & Dagger": ((19, 43, 39), (37, 116, 80), (166, 211, 113)),
    "The Siltbound": ((30, 39, 48), (67, 91, 111), (173, 190, 191)),
    "Rusty Buckets": ((55, 37, 26), (132, 75, 43), (211, 154, 83)),
}


def _global_flags(manager) -> dict:
    state = getattr(manager, "npc_state", None)
    if not isinstance(state, dict):
        state = {}
        manager.npc_state = state
    global_state = state.setdefault("global", {})
    return global_state.setdefault("flags", {})


def has_seen_tier0_team_intro(manager) -> bool:
    return bool(_global_flags(manager).get(INTRO_FLAG, False))


def should_show_tier0_team_intro(manager) -> bool:
    engine = getattr(manager, "league_engine", None)
    tier = int(getattr(engine, "tier", 1) or 1)
    return tier == 1 and not has_seen_tier0_team_intro(manager)


def mark_tier0_team_intro_seen(manager) -> None:
    _global_flags(manager)[INTRO_FLAG] = True


def team_portrait_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")
    return slug or "unknown_team"


def _item_names(unit) -> list[str]:
    names = []
    for item in getattr(unit, "equipment", {}).values():
        if item is not None:
            names.append(str(getattr(item, "name", type(item).__name__)).lower())
    return names


def _main_weapon(unit) -> str:
    item = getattr(unit, "equipment", {}).get("main_hand")
    return str(getattr(item, "name", "Fists")).lower()


def _has_shield(unit) -> bool:
    for item in getattr(unit, "equipment", {}).values():
        if item is None:
            continue
        name = str(getattr(item, "name", "")).lower()
        group = str(getattr(item, "armor_group", "")).lower()
        if group == "shield" or any(k in name for k in ("shield", "buckler", "pot lid")):
            return True
    return False


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _darken(col, amount=0.25):
    return tuple(max(0, int(c * (1.0 - amount))) for c in col)


def _lighten(col, amount=0.25):
    return tuple(min(255, int(c + (255 - c) * amount)) for c in col)


def _team_palette(team):
    name = str(getattr(team, "name", "Unknown Team"))
    if name in TEAM_PALETTES:
        return TEAM_PALETTES[name]
    col = tuple(getattr(team, "color", (110, 90, 70)))[:3]
    return (_darken(col, 0.65), _darken(col, 0.15), _lighten(col, 0.35))


def _draw_gradient(surface, top, bottom):
    w, h = surface.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, _mix(top, bottom, t), (0, y), (w, y))


def _draw_background(surface, team, palette):
    w, h = surface.get_size()
    deep, mid, accent = palette
    _draw_gradient(surface, deep, _darken(mid, 0.35))

    glow = pygame.Surface((w, h), pygame.SRCALPHA)
    for radius, alpha in ((int(w * 0.42), 12), (int(w * 0.28), 20), (int(w * 0.15), 28)):
        pygame.draw.circle(glow, (*accent, alpha), (w // 2, int(h * 0.42)), radius)
    surface.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    horizon = int(h * 0.54)
    pygame.draw.rect(surface, _darken(deep, 0.35), (0, horizon, w, h - horizon))
    for i in range(18):
        x = int(i * w / 17)
        stand_h = int(h * (0.07 + 0.025 * ((i * 7) % 4)))
        pygame.draw.rect(surface, _darken(mid, 0.48), (x - 18, horizon - stand_h, 36, stand_h))
        pygame.draw.circle(surface, _lighten(deep, 0.18), (x, horizon - stand_h - 5), max(3, w // 300))

    arch_col = _darken(mid, 0.42)
    pygame.draw.rect(surface, arch_col, (int(w * 0.08), int(h * 0.17), int(w * 0.055), int(h * 0.42)))
    pygame.draw.rect(surface, arch_col, (int(w * 0.865), int(h * 0.17), int(w * 0.055), int(h * 0.42)))
    pygame.draw.arc(surface, arch_col, (int(w * 0.08), int(h * 0.02), int(w * 0.84), int(h * 0.47)), math.pi, math.tau, max(10, w // 75))

    banner_col = tuple(getattr(team, "color", accent))[:3]
    for bx in (int(w * 0.13), int(w * 0.83)):
        points = [(bx, int(h * 0.18)), (bx + int(w * 0.055), int(h * 0.18)),
                  (bx + int(w * 0.055), int(h * 0.42)), (bx + int(w * 0.028), int(h * 0.47)),
                  (bx, int(h * 0.42))]
        pygame.draw.polygon(surface, _darken(banner_col, 0.18), points)
        pygame.draw.line(surface, _lighten(banner_col, 0.28), points[0], points[1], max(2, w // 500))

    for i in range(15):
        y = horizon + int((i / 15) ** 1.65 * (h - horizon))
        pygame.draw.line(surface, _darken(mid, 0.48), (0, y), (w, y), 1)
    for i in range(75):
        x = (i * 173 + len(str(getattr(team, "name", ""))) * 29) % w
        y = (i * 97 + 41) % max(1, int(h * 0.62))
        r = 1 + (i % 3 == 0)
        pygame.draw.circle(surface, (*_lighten(accent, 0.18), 90), (x, y), r)


def _weapon_kind(name: str) -> str:
    if "crossbow" in name:
        return "crossbow"
    if "bow" in name:
        return "bow"
    if any(k in name for k in ("spear", "pole", "pike")):
        return "spear"
    if any(k in name for k in ("staff", "stick")):
        return "staff"
    if any(k in name for k in ("axe", "hatchet")):
        return "axe"
    if any(k in name for k in ("mace", "branch", "maul")):
        return "mace"
    if any(k in name for k in ("dagger", "shiv", "dirk")):
        return "dagger"
    return "sword"


def _draw_weapon(surface, kind, hand, scale, facing, metal, wood):
    hx, hy = hand
    s = max(1.0, scale)
    line = max(3, int(5 * s))
    tip_x = hx + int(facing * 30 * s)

    if kind == "bow":
        rect = pygame.Rect(0, 0, int(34 * s), int(102 * s))
        rect.center = (tip_x, hy - int(24 * s))
        start = math.pi * 0.55 if facing > 0 else -math.pi * 0.45
        pygame.draw.arc(surface, wood, rect, start, start + math.pi, line)
        pygame.draw.line(surface, _lighten(wood, 0.5), (tip_x, rect.top + 5), (tip_x, rect.bottom - 5), max(1, line // 3))
        return
    if kind == "crossbow":
        pygame.draw.line(surface, wood, (hx, hy), (tip_x + int(facing * 45 * s), hy - int(8 * s)), line)
        pygame.draw.arc(surface, metal, (tip_x - int(28 * s), hy - int(34 * s), int(56 * s), int(45 * s)), math.pi, math.tau, line)
        return

    length = 112 if kind in ("spear", "staff") else 74
    end = (hx + int(facing * length * s), hy - int(length * 0.72 * s))
    pygame.draw.line(surface, wood, (hx, hy), end, line)

    if kind == "spear":
        ex, ey = end
        pygame.draw.polygon(surface, metal, [(ex, ey - int(18 * s)),
                                             (ex - int(facing * 10 * s), ey + int(8 * s)),
                                             (ex + int(facing * 7 * s), ey + int(5 * s))])
    elif kind == "staff":
        pygame.draw.circle(surface, _lighten(wood, 0.25), end, int(8 * s))
        pygame.draw.circle(surface, metal, end, int(3 * s))
    elif kind == "axe":
        ex, ey = end
        blade = [(ex, ey), (ex + int(facing * 27 * s), ey - int(9 * s)),
                 (ex + int(facing * 22 * s), ey + int(22 * s)),
                 (ex, ey + int(15 * s))]
        pygame.draw.polygon(surface, metal, blade)
        pygame.draw.polygon(surface, _darken(metal, 0.38), blade, max(1, int(2 * s)))
    elif kind == "mace":
        pygame.draw.circle(surface, metal, end, int(14 * s))
        for a in range(0, 360, 60):
            dx = int(math.cos(math.radians(a)) * 21 * s)
            dy = int(math.sin(math.radians(a)) * 21 * s)
            pygame.draw.line(surface, metal, end, (end[0] + dx, end[1] + dy), max(2, int(3 * s)))
    elif kind == "dagger":
        ex, ey = end
        pygame.draw.polygon(surface, metal, [(ex, ey - int(10 * s)),
                                             (ex + int(facing * 14 * s), ey + int(5 * s)),
                                             (ex, ey + int(7 * s))])
    else:
        ex, ey = end
        pygame.draw.polygon(surface, metal, [(ex, ey - int(16 * s)),
                                             (ex + int(facing * 12 * s), ey + int(8 * s)),
                                             (ex - int(facing * 4 * s), ey + int(13 * s))])


def _draw_shield(surface, center, scale, team_color):
    cx, cy = center
    s = max(1.0, scale)
    w, h = int(58 * s), int(72 * s)
    pts = [(cx - w // 2, cy - h // 2), (cx + w // 2, cy - h // 2),
           (cx + int(w * 0.42), cy + int(h * 0.2)), (cx, cy + h // 2),
           (cx - int(w * 0.42), cy + int(h * 0.2))]
    pygame.draw.polygon(surface, _darken(team_color, 0.34), pts)
    pygame.draw.polygon(surface, (42, 36, 31), pts, max(2, int(4 * s)))
    pygame.draw.line(surface, _lighten(team_color, 0.45), (cx, cy - h // 2 + 5), (cx, cy + h // 2 - 7), max(2, int(3 * s)))
    pygame.draw.circle(surface, (142, 129, 103), (cx, cy), int(8 * s))


def _draw_character(surface, unit, cx, ground_y, scale, team_color, facing=1):
    race = str(getattr(unit, "race_name", type(unit).__name__)).lower()
    items = _item_names(unit)
    weapon = _weapon_kind(_main_weapon(unit))
    shielded = _has_shield(unit)
    heavy = any(k in " ".join(items) for k in ("mail", "iron helm"))
    robe = any("robe" in n for n in items)
    viking = any("viking" in n for n in items)
    leather_cap = any("leather cap" in n for n in items)

    race_scale = 1.0
    body_w = 54
    skin = (188, 146, 112)
    if "orc" in race:
        race_scale, body_w, skin = 1.12, 70, (91, 132, 72)
    elif "goblin" in race:
        race_scale, body_w, skin = 0.78, 48, (104, 151, 71)
    elif "elf" in race:
        race_scale, body_w, skin = 1.01, 50, (211, 178, 141)

    s = max(0.55, scale * race_scale)
    outline = (25, 22, 21)
    boot = (47, 35, 29)
    cloth = _darken(team_color, 0.22)
    cloth_hi = _lighten(team_color, 0.28)
    metal = (162, 166, 160) if heavy else (127, 117, 97)
    wood = (103, 70, 41)

    pygame.draw.ellipse(surface, (10, 9, 9), (cx - int(48 * s), ground_y - int(12 * s), int(96 * s), int(25 * s)))

    hip_y = ground_y - int(92 * s)
    shoulder_y = ground_y - int(190 * s)
    head_y = ground_y - int(244 * s)

    if robe:
        pygame.draw.polygon(surface, _darken(team_color, 0.46),
                            [(cx - int(38 * s), shoulder_y), (cx + int(38 * s), shoulder_y),
                             (cx + int(51 * s), ground_y - int(22 * s)), (cx - int(51 * s), ground_y - int(22 * s))])

    stance = int(21 * s)
    for side in (-1, 1):
        knee = (cx + side * stance, ground_y - int(55 * s))
        foot = (cx + side * int(30 * s), ground_y - int(5 * s))
        pygame.draw.line(surface, _darken(cloth, 0.32), (cx + side * int(15 * s), hip_y), knee, max(9, int(17 * s)))
        pygame.draw.line(surface, boot, knee, foot, max(9, int(18 * s)))

    bw = int(body_w * s)
    torso = [(cx - bw // 2, shoulder_y), (cx + bw // 2, shoulder_y),
             (cx + int(bw * 0.42), hip_y), (cx - int(bw * 0.42), hip_y)]
    pygame.draw.polygon(surface, metal if heavy else cloth, torso)
    pygame.draw.polygon(surface, outline, torso, max(2, int(4 * s)))
    if heavy:
        for y in range(shoulder_y + int(15 * s), hip_y, max(7, int(12 * s))):
            pygame.draw.line(surface, _lighten(metal, 0.16), (cx - bw // 2 + 7, y), (cx + bw // 2 - 7, y), max(1, int(2 * s)))
    else:
        pygame.draw.line(surface, cloth_hi, (cx, shoulder_y + int(8 * s)), (cx, hip_y - int(7 * s)), max(2, int(4 * s)))
    pygame.draw.line(surface, (73, 48, 31), (cx - int(31 * s), hip_y), (cx + int(31 * s), hip_y), max(4, int(8 * s)))

    left_hand = (cx - facing * int(48 * s), ground_y - int(122 * s))
    right_hand = (cx + facing * int(43 * s), ground_y - int(132 * s))
    pygame.draw.line(surface, skin, (cx - facing * int(25 * s), shoulder_y + int(13 * s)), left_hand, max(9, int(18 * s)))
    if shielded:
        _draw_shield(surface, (left_hand[0] - facing * int(8 * s), left_hand[1] + int(13 * s)), s, team_color)
    pygame.draw.line(surface, skin, (cx + facing * int(25 * s), shoulder_y + int(10 * s)), right_hand, max(9, int(18 * s)))
    _draw_weapon(surface, weapon, right_hand, s, facing, metal=(186, 184, 171), wood=wood)

    pygame.draw.rect(surface, _darken(skin, 0.08), (cx - int(10 * s), head_y + int(25 * s), int(20 * s), int(29 * s)))
    head_w = int((46 if "goblin" not in race else 42) * s)
    head_h = int((57 if "orc" not in race else 62) * s)
    head_rect = pygame.Rect(cx - head_w // 2, head_y - head_h // 2, head_w, head_h)

    if "elf" in race or "goblin" in race:
        ear_len = int((31 if "goblin" in race else 23) * s)
        pygame.draw.polygon(surface, skin, [(head_rect.left + 4, head_y - int(7 * s)),
                                            (head_rect.left - ear_len, head_y - int(16 * s)),
                                            (head_rect.left + 2, head_y + int(8 * s))])
        pygame.draw.polygon(surface, skin, [(head_rect.right - 4, head_y - int(7 * s)),
                                            (head_rect.right + ear_len, head_y - int(16 * s)),
                                            (head_rect.right - 2, head_y + int(8 * s))])

    pygame.draw.ellipse(surface, skin, head_rect)
    pygame.draw.ellipse(surface, outline, head_rect, max(2, int(3 * s)))

    hair = (45, 32, 27) if "elf" not in race else (94, 69, 43)
    pygame.draw.arc(surface, hair, head_rect.inflate(-int(4 * s), -int(6 * s)), math.pi, math.tau, max(4, int(9 * s)))
    eye_y = head_y - int(3 * s)
    eye_dx = int(10 * s)
    eye_col = (226, 210, 150) if "goblin" in race else (40, 35, 31)
    pygame.draw.circle(surface, eye_col, (cx - eye_dx, eye_y), max(1, int(2.5 * s)))
    pygame.draw.circle(surface, eye_col, (cx + eye_dx, eye_y), max(1, int(2.5 * s)))
    pygame.draw.line(surface, _darken(skin, 0.35), (cx - int(7 * s), head_y + int(15 * s)), (cx + int(9 * s), head_y + int(14 * s)), max(1, int(2 * s)))

    if "orc" in race:
        tusk = (226, 216, 183)
        pygame.draw.polygon(surface, tusk, [(cx - int(15 * s), head_y + int(17 * s)),
                                            (cx - int(8 * s), head_y + int(6 * s)),
                                            (cx - int(4 * s), head_y + int(19 * s))])
        pygame.draw.polygon(surface, tusk, [(cx + int(15 * s), head_y + int(17 * s)),
                                            (cx + int(8 * s), head_y + int(6 * s)),
                                            (cx + int(4 * s), head_y + int(19 * s))])

    if heavy:
        helm = [(head_rect.left - int(4 * s), head_y - int(7 * s)),
                (head_rect.left + int(6 * s), head_rect.top - int(7 * s)),
                (head_rect.right - int(6 * s), head_rect.top - int(7 * s)),
                (head_rect.right + int(4 * s), head_y - int(7 * s)),
                (head_rect.right - int(2 * s), head_y + int(4 * s)),
                (head_rect.left + int(2 * s), head_y + int(4 * s))]
        pygame.draw.polygon(surface, (132, 135, 132), helm)
        pygame.draw.polygon(surface, outline, helm, max(2, int(3 * s)))
    elif viking:
        pygame.draw.arc(surface, (108, 100, 84), head_rect.inflate(int(7 * s), int(5 * s)), math.pi, math.tau, max(6, int(10 * s)))
        pygame.draw.polygon(surface, (196, 183, 145), [(head_rect.left, head_y - int(12 * s)),
                                                       (head_rect.left - int(18 * s), head_y - int(34 * s)),
                                                       (head_rect.left + int(6 * s), head_y - int(18 * s))])
        pygame.draw.polygon(surface, (196, 183, 145), [(head_rect.right, head_y - int(12 * s)),
                                                       (head_rect.right + int(18 * s), head_y - int(34 * s)),
                                                       (head_rect.right - int(6 * s), head_y - int(18 * s))])
    elif leather_cap:
        pygame.draw.arc(surface, (73, 48, 31), head_rect.inflate(int(4 * s), int(3 * s)), math.pi, math.tau, max(6, int(10 * s)))


def _draw_title(surface, name, palette):
    w, h = surface.get_size()
    deep, _, accent = palette
    panel_h = int(h * 0.19)
    overlay = pygame.Surface((w, panel_h), pygame.SRCALPHA)
    overlay.fill((*_darken(deep, 0.35), 224))
    surface.blit(overlay, (0, h - panel_h))
    pygame.draw.line(surface, accent, (int(w * 0.08), h - panel_h), (int(w * 0.92), h - panel_h), max(2, w // 360))

    size = max(28, int(h * 0.095))
    while size >= 24:
        font = pygame.font.SysFont("georgia", size, bold=True)
        text = font.render(str(name).upper(), True, (239, 228, 199))
        if text.get_width() <= int(w * 0.84):
            break
        size -= 3
    shadow = font.render(str(name).upper(), True, (18, 14, 12))
    x = (w - text.get_width()) // 2
    y = h - panel_h + (panel_h - text.get_height()) // 2
    surface.blit(shadow, (x + max(2, w // 500), y + max(2, h // 300)))
    surface.blit(text, (x, y))


def render_team_portrait(team, size) -> pygame.Surface:
    """Render a complete 16:9 poster from a live Team object."""
    w, h = max(320, int(size[0])), max(180, int(size[1]))
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    palette = _team_palette(team)
    _draw_background(surface, team, palette)

    members = list(getattr(team, "members", None) or getattr(team, "roster", None) or [])[:5]
    if not members:
        return surface

    positions = [0.12, 0.30, 0.50, 0.70, 0.88]
    scales = [0.72, 0.88, 1.04, 0.88, 0.72]
    ground = int(h * 0.84)
    for i, unit in enumerate(members):
        x = int(w * positions[i])
        y = ground - int(abs(2 - i) * h * 0.018)
        facing = 1 if i < 2 else (-1 if i > 2 else 1)
        scale = scales[i] * (h / 720.0)
        _draw_character(surface, unit, x, y, scale, tuple(getattr(team, "color", palette[2]))[:3], facing)

    _draw_title(surface, getattr(team, "name", "Unknown Team"), palette)

    vignette = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(14):
        alpha = int(4 + i * 2.5)
        pygame.draw.rect(vignette, (0, 0, 0, alpha), (i, i, w - i * 2, h - i * 2), width=max(1, int(w / 500)))
    surface.blit(vignette, (0, 0))
    return surface


def _fit_cover(image: pygame.Surface, size) -> pygame.Surface:
    w, h = size
    iw, ih = image.get_size()
    scale = max(w / max(1, iw), h / max(1, ih))
    scaled = pygame.transform.smoothscale(image, (max(1, int(iw * scale)), max(1, int(ih * scale))))
    x = (scaled.get_width() - w) // 2
    y = (scaled.get_height() - h) // 2
    return scaled.subsurface((x, y, w, h)).copy()


def _load_override(team, size):
    path = os.path.join(OVERRIDE_DIR, team_portrait_slug(getattr(team, "name", "")) + ".png")
    if not os.path.exists(path):
        return None
    try:
        return _fit_cover(pygame.image.load(path).convert_alpha(), size)
    except Exception as exc:
        print(f"[Tier0Intro] Could not load {path}: {exc}")
        return None


def _tier0_teams(manager) -> list:
    engine = getattr(manager, "league_engine", None)
    if engine is None:
        return []
    try:
        engine._ensure_initialized()
        season = engine.seasons.get("5v5") or next(iter(engine.seasons.values()))
        return [team for team in getattr(season, "premades", []) if team]
    except Exception as exc:
        print(f"[Tier0Intro] Could not read live league teams: {exc}")
        return []


class Tier0TeamIntroOverlay:
    """Seven-page first-entry overlay embedded in ``LeagueMenu``."""

    def __init__(self, manager):
        self.manager = manager
        self.active = should_show_tier0_team_intro(manager)
        self.index = 0
        self.teams = _tier0_teams(manager) if self.active else []
        self._cards = {}
        self._fade = 255
        if self.active and not self.teams:
            self.finish()

    def finish(self):
        mark_tier0_team_intro_seen(self.manager)
        self.active = False

    def _advance(self, step=1):
        if not self.active:
            return
        new_index = self.index + step
        if new_index >= len(self.teams):
            self.finish()
            return
        self.index = max(0, new_index)
        self._fade = 210

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.finish()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER,
                               pygame.K_RIGHT, pygame.K_e, pygame.K_d):
                self._advance(1)
            elif event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_BACKSPACE):
                self._advance(-1)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            width = pygame.display.get_surface().get_width() if pygame.display.get_surface() else 1280
            self._advance(-1 if event.pos[0] < width * 0.22 else 1)
            return True
        return True

    def update(self):
        self._fade = max(0, self._fade - 24)

    def _card(self, team, size):
        key = (id(team), int(size[0]), int(size[1]))
        if key not in self._cards:
            self._cards[key] = _load_override(team, size) or render_team_portrait(team, size)
        return self._cards[key]

    def draw(self, screen) -> bool:
        if not self.active or not self.teams:
            return False
        size = screen.get_size()
        screen.blit(self._card(self.teams[self.index], size), (0, 0))

        w, h = size
        chevron = max(16, int(h * 0.035))
        alpha_layer = pygame.Surface(size, pygame.SRCALPHA)
        if self.index > 0:
            pygame.draw.polygon(alpha_layer, (238, 226, 197, 150),
                                [(int(w * 0.035) + chevron, h // 2 - chevron),
                                 (int(w * 0.035), h // 2),
                                 (int(w * 0.035) + chevron, h // 2 + chevron)])
        pygame.draw.polygon(alpha_layer, (238, 226, 197, 170),
                            [(int(w * 0.965) - chevron, h // 2 - chevron),
                             (int(w * 0.965), h // 2),
                             (int(w * 0.965) - chevron, h // 2 + chevron)])

        dot_y = int(h * 0.055)
        gap = max(17, int(w * 0.018))
        start_x = w // 2 - (len(self.teams) - 1) * gap // 2
        for i in range(len(self.teams)):
            radius = max(4, int(h * (0.008 if i == self.index else 0.006)))
            col = (242, 211, 132, 220) if i == self.index else (220, 211, 191, 105)
            pygame.draw.circle(alpha_layer, col, (start_x + i * gap, dot_y), radius)
        screen.blit(alpha_layer, (0, 0))

        if self._fade > 0:
            fade = pygame.Surface(size)
            fade.fill((0, 0, 0))
            fade.set_alpha(self._fade)
            screen.blit(fade, (0, 0))
        return True
