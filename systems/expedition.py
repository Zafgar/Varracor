# systems/expedition.py
"""Retkikunta ja kenttäkomennot + Commanderin kaatumis-rescue (pelitesti 21).

RETKIKUNTA
- COMMAND-puun Warband-haara (skills/commander_skills_data.py) avaa
  retkikapasiteetin: 2 -> 4 -> 6 -> 8 -> 10 soturia.
- Ryhmä kootaan AINA barracksin sotapöydältä (muster); valitut kulkevat
  mukana maailmankartan retkikohteissa (kaivostie, luola, rift-alueet).
- Kenttäkomennot [T]-valikosta numeronäppäimillä: FOLLOW ME ja FREE
  FIGHT heti, KITE ja DEFEND avataan puusta (tactic_kite/tactic_defend).
  Valikon ollessa auki numerot EIVÄT castaa hotbar-slotteja.
- Kaatunut retkeläinen raahataan pois kentältä loppuretkeksi ja saa
  areenataisteluiden tapaan vammoja (severe wound/fracture + fatigue);
  sairaana retkelle viety voi KUOLLA (sama kuolemanriski kuin areenalla).

RESCUE
- Kun Commander kaatuu retkellä: joku raahaa hänet takaisin Muckfordiin.
  Jos tiimi on pystyssä (team_registered + elossa olevia sotureita),
  hän herää barracksista ja toveri kertoo mitä tapahtui. Muuten hän
  herää Sunk Caskista ja Marda perii noutopalkkion (RESCUE_FEE).
"""
import math
import random

# Käskyt: (id, nimi, kuvaus, vaatimusnoodi tai None)
ORDERS = [
    ("follow", "FOLLOW ME", "Stay on me; fight only what's on top of us.",
     None),
    ("free", "FREE FIGHT", "Loose formation; everyone picks their fights.",
     None),
    ("kite", "KITE", "Ranged give ground and shoot; melee falls back.",
     "tactic_kite"),
    ("defend", "DEFEND", "Screen the Commander; shield ranged and healers.",
     "tactic_defend"),
]

RESCUE_FEE = 25          # SP; Marda perii kun sinut kannetaan Sunk Caskiin
DOWN_WOUND_CHANCE = 0.30 # kaatuneen riski saada vakava vamma (kuten areena)


# ----------------------------------------------------------------------
# Retkikunnan kokoonpano
# ----------------------------------------------------------------------

def party_cap(manager) -> int:
    pc = getattr(manager, "player_character", None)
    return int(getattr(pc, "expedition_cap", 0) or 0)


def party(manager):
    """Elossa olevat, yhä rosterissa olevat retkeläiset."""
    roster = list(getattr(manager, "my_team", []) or [])
    out = []
    for u in getattr(manager, "expedition_party", []) or []:
        if u in roster and not getattr(u, "is_dead", False):
            out.append(u)
    return out


def toggle_member(manager, unit):
    """Muster-paneelin rivivalinta. Palauttaa (ok, viesti)."""
    sel = getattr(manager, "expedition_party", None)
    if sel is None:
        sel = manager.expedition_party = []
    if unit in sel:
        sel.remove(unit)
        return True, f"{unit.name} stays behind."
    cap = party_cap(manager)
    if cap <= 0:
        return False, "Unlock Warband I in the COMMAND tree first."
    if len(sel) >= cap:
        return False, f"The warband is full ({cap})."
    if getattr(unit, "is_dead", False):
        return False, f"{unit.name} is in no shape to march."
    sel.append(unit)
    return True, f"{unit.name} joins the expedition."


def available_orders(pc):
    """[(id, nimi, kuvaus)] jotka Commander on oppinut."""
    tactics = getattr(pc, "tactics", None) or {"follow", "free"}
    return [(oid, name, desc) for oid, name, desc, req in ORDERS
            if req is None or oid in tactics]


# ----------------------------------------------------------------------
# Kenttäelämä: spawn, kaatumiset
# ----------------------------------------------------------------------

def spawn_party(manager, x, y):
    """Sijoittaa retkikunnan Commanderin ympärille kartalle ja lukitsee
    kuolemanriskin sairaana lähteneille (kuten areenan start_match)."""
    members = party(manager)
    try:
        from systems import conditions as _cond
    except Exception:
        _cond = None
    for i, u in enumerate(members):
        ang = (2 * math.pi) * (i / max(1, len(members)))
        u.rect.center = (int(x + 80 * math.cos(ang) - 60),
                         int(y + 70 * math.sin(ang)))
        u.is_dead = False
        u.current_hp = max(1, int(u.current_hp))
        u.animation_state = "idle"
        u._expedition_out = False
        if _cond is not None:
            u._prebattle_death_risk = _cond.death_risk(u)
    return members


def field_party(manager):
    """Kentällä aktiiviset retkeläiset (ei kaatuneita/ulos kannettuja)."""
    return [u for u in party(manager)
            if not getattr(u, "_expedition_out", False)
            and not getattr(u, "is_dead", False)]


def check_party_downs(manager):
    """Kutsu joka frame retkikartalla: kaatunut retkeläinen kannetaan
    pois kentältä ja saa areenataistelun tapaiset jälkiseuraukset."""
    try:
        from systems import conditions as _cond
    except Exception:
        _cond = None
    roster = list(getattr(manager, "my_team", []) or [])
    # HUOM: EI party()-apuria - se suodattaa kuolleet pois, jolloin
    # kaatunutta ei koskaan käsiteltäisi
    for u in list(getattr(manager, "expedition_party", []) or []):
        if u not in roster:
            continue
        if not getattr(u, "is_dead", False) or \
                getattr(u, "_expedition_out", False):
            continue
        u._expedition_out = True
        # 1. Sairaana kentälle viety voi menehtyä (sama kuin areenalla)
        risk = float(getattr(u, "_prebattle_death_risk", 0.0) or 0.0)
        u._prebattle_death_risk = 0.0
        if risk > 0 and random.random() < risk:
            try:
                manager.my_team.remove(u)
            except Exception:
                pass
            try:
                manager.expedition_party.remove(u)
            except Exception:
                pass
            _toast(manager, u, f"{u.name} died on the road...",
                   (255, 90, 90))
            continue
        # 2. Selviää, mutta retki on hänen osaltaan ohi: vammat + lepo
        u.is_dead = False
        u.current_hp = max(1, int(u.max_hp * 0.10))
        if _cond is not None:
            if random.random() < DOWN_WOUND_CHANCE:
                _cond.add_condition(
                    u, random.choice(("severe_wound", "fracture")), manager)
            _cond.add_condition(u, "fatigue", manager)
        _toast(manager, u, f"{u.name} is down - dragged clear of the fight!",
               (255, 160, 110))


def _toast(manager, unit, text, color):
    try:
        manager.vfx.show_damage(unit.rect.centerx, unit.rect.top - 40,
                                text, color=color)
    except Exception:
        pass


# ----------------------------------------------------------------------
# Käskyjen AI (gladiator.run_combat_ai kutsuu retkikartoilla)
# ----------------------------------------------------------------------

def follow_order(unit, all_units, obstacles, manager):
    """Toteuttaa aktiivisen retkikäskyn tälle yksikölle. Palauttaa True
    jos käsky ohjasi framen (normaali AI ohitetaan), False = FREE FIGHT
    tai käsky ei sovellu -> normaali taistelu-AI jatkaa."""
    order = str(getattr(manager, "expedition_order", "follow") or "follow")
    if order == "free":
        return False
    ai = getattr(unit, "ai_controller", None)
    pc = getattr(manager, "player_character", None)
    if ai is None or pc is None or not hasattr(ai, "_move_towards"):
        return False

    enemy, e_dist = _nearest_enemy(unit, all_units)
    pc_enemy, pc_e_dist = _nearest_enemy(pc, all_units)
    dx = pc.rect.centerx - unit.rect.centerx
    dy = pc.rect.centery - unit.rect.centery
    pc_dist = math.hypot(dx, dy)
    ranged = _is_ranged(unit)

    if order == "follow":
        # Taistele vain jos vaara on iholla (oma tai Commanderin)
        if (enemy is not None and e_dist < 240) or \
                (pc_enemy is not None and pc_e_dist < 260):
            return False
        return _hold_near(unit, ai, pc, _formation_slot(unit, manager),
                          obstacles, all_units, manager)

    if order == "kite":
        # Ranged: ammu kaukaa, väistä kun vihollinen pääsee lähelle.
        # Melee: peräänny samaan aikaan Commanderin suuntaan.
        if enemy is None:
            return _hold_near(unit, ai, pc, _formation_slot(unit, manager),
                              obstacles, all_units, manager)
        if ranged:
            if e_dist < 280:
                _flee_from(unit, ai, enemy, obstacles, all_units, manager)
                return True
            return False  # normaali AI hoitaa ampumisen etäältä
        # Melee vetäytyy: kohti Commanderia, ja hänen ohitseen poispäin
        if e_dist < 340:
            if pc_dist > 90:
                unit.set_sprinting(unit.current_stamina > 10)
                ai._move_towards(dx, dy, pc_dist, obstacles, all_units,
                                 manager)
            else:
                _flee_from(unit, ai, enemy, obstacles, all_units, manager)
            return True
        return _hold_near(unit, ai, pc, _formation_slot(unit, manager),
                          obstacles, all_units, manager)

    if order == "defend":
        # Melee muodostaa kilpimuurin Commanderin ja uhan väliin;
        # ranged/parantajat asemoituvat Commanderin taakse.
        threat = pc_enemy or enemy
        if ranged:
            spot = _behind_commander(pc, threat, 84,
                                     _slot_index(unit, manager))
            sx = spot[0] - unit.rect.centerx
            sy = spot[1] - unit.rect.centery
            sd = math.hypot(sx, sy)
            if sd > 36:
                ai._move_towards(sx, sy, sd, obstacles, all_units, manager)
                return True
            return False  # asemissa: normaali AI ampuu vapaasti
        # Melee: torju uhka joka on jo kimpussa
        if threat is not None:
            t_dist = math.hypot(threat.rect.centerx - pc.rect.centerx,
                                threat.rect.centery - pc.rect.centery)
            if t_dist < 240 or e_dist < 140:
                return False  # päästä normaali AI lyömään
        spot = _screen_position(pc, threat, 96, _slot_index(unit, manager))
        sx = spot[0] - unit.rect.centerx
        sy = spot[1] - unit.rect.centery
        sd = math.hypot(sx, sy)
        if sd > 26:
            unit.set_sprinting(sd > 220 and unit.current_stamina > 10)
            ai._move_towards(sx, sy, sd, obstacles, all_units, manager)
        else:
            unit.set_sprinting(False)
            unit.animation_state = "idle"
        return True

    return False


def _nearest_enemy(unit, all_units):
    best, best_d = None, 1e9
    for u in all_units:
        if u is unit or getattr(u, "is_dead", True):
            continue
        if getattr(u, "is_structure", False):
            continue
        if getattr(u, "team_color", None) == unit.team_color:
            continue
        d = math.hypot(u.rect.centerx - unit.rect.centerx,
                       u.rect.centery - unit.rect.centery)
        if d < best_d:
            best, best_d = u, d
    return best, best_d


def _is_ranged(unit):
    return (getattr(unit, "weapon_type", "") == "ranged"
            or int(getattr(unit, "max_spell_tier", 0)) > 0)


def _slot_index(unit, manager):
    sel = getattr(manager, "expedition_party", []) or []
    try:
        return sel.index(unit)
    except ValueError:
        return 0


def _formation_slot(unit, manager):
    """Yksikön vakiopaikka Commanderin ympärillä (rinki)."""
    sel = getattr(manager, "expedition_party", []) or []
    n = max(1, len(sel))
    i = _slot_index(unit, manager)
    ang = (2 * math.pi) * (i / n) + math.pi  # aloita takaviistosta
    return (86 * math.cos(ang), 74 * math.sin(ang))


def _hold_near(unit, ai, pc, offset, obstacles, all_units, manager):
    tx = pc.rect.centerx + offset[0]
    ty = pc.rect.centery + offset[1]
    dx = tx - unit.rect.centerx
    dy = ty - unit.rect.centery
    dist = math.hypot(dx, dy)
    if dist > 46:
        unit.set_sprinting(dist > 260 and unit.current_stamina > 10)
        ai._move_towards(dx, dy, dist, obstacles, all_units, manager)
    else:
        unit.set_sprinting(False)
        unit.animation_state = "idle"
    return True


def _flee_from(unit, ai, enemy, obstacles, all_units, manager):
    dx = unit.rect.centerx - enemy.rect.centerx
    dy = unit.rect.centery - enemy.rect.centery
    d = math.hypot(dx, dy) or 1.0
    unit.set_sprinting(unit.current_stamina > 10)
    ai._move_towards(dx, dy, d, obstacles, all_units, manager)


def _behind_commander(pc, threat, radius, idx):
    """Piste Commanderin takana (uhkaan nähden), pieni sivuhajonta."""
    if threat is None:
        vx, vy = -1.0, 0.0
    else:
        vx = pc.rect.centerx - threat.rect.centerx
        vy = pc.rect.centery - threat.rect.centery
        d = math.hypot(vx, vy) or 1.0
        vx, vy = vx / d, vy / d
    side = (-1) ** idx * (18 + 14 * (idx // 2))
    return (pc.rect.centerx + vx * radius - vy * side,
            pc.rect.centery + vy * radius + vx * side)


def _screen_position(pc, threat, radius, idx):
    """Kilpimuuripaikka Commanderin ja uhan välissä, rivissä."""
    if threat is None:
        ang = (2 * math.pi) * (idx / 6.0)
        return (pc.rect.centerx + radius * math.cos(ang),
                pc.rect.centery + radius * math.sin(ang))
    vx = threat.rect.centerx - pc.rect.centerx
    vy = threat.rect.centery - pc.rect.centery
    d = math.hypot(vx, vy) or 1.0
    vx, vy = vx / d, vy / d
    side = (-1) ** idx * (26 + 20 * (idx // 2))
    return (pc.rect.centerx + vx * radius - vy * side,
            pc.rect.centery + vy * radius + vx * side)


# ----------------------------------------------------------------------
# Taktiikkavalikko ([T] + numerot) - Commanderin input
# ----------------------------------------------------------------------

def handle_tactics_input(pc, keys, manager):
    """Kutsutaan Commanderin run_combat_ai:sta joka frame retkikartoilla.
    Palauttaa True kun valikko on auki (= numeronäppäimet varattu
    käskyille, hotbar-castit estetään)."""
    import pygame
    from systems import keybinds
    if not getattr(manager, "expedition_field_active", False) or \
            not party(manager):
        manager.tactics_menu_open = False
        return False
    prev = getattr(pc, "prev_keys", None)

    def just_pressed(code):
        try:
            return keys[code] and not (prev and prev[code])
        except Exception:
            return False

    for code in keybinds.keys_for("tactics"):
        if just_pressed(code):
            manager.tactics_menu_open = \
                not getattr(manager, "tactics_menu_open", False)
            break

    if not getattr(manager, "tactics_menu_open", False):
        return False

    number_keys = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4)
    orders = available_orders(pc)
    for i, code in enumerate(number_keys):
        if i < len(orders) and just_pressed(code):
            oid, name, _desc = orders[i]
            manager.expedition_order = oid
            manager.tactics_menu_open = False
            _toast(manager, pc, f"ORDER: {name}!", (255, 210, 90))
            try:
                from sound_manager import sound_system
                sound_system.play_sound("battle_start")
            except Exception:
                pass
            break
    return True


def draw_tactics_ui(screen, pc, manager):
    """Piirtää käskychipin ja [T]-valikon (kutsutaan draw_hudista)."""
    import pygame
    from settings import SCREEN_WIDTH, SCREEN_HEIGHT
    from ui_kit import font_small, font_main
    if not getattr(manager, "expedition_field_active", False):
        return
    members = field_party(manager)
    total = len(party(manager))
    if total == 0:
        return
    # Chip: nykyinen käsky + retkeläisten määrä
    order = str(getattr(manager, "expedition_order", "follow"))
    label = next((n for oid, n, _d, _r in ORDERS if oid == order), "FOLLOW ME")
    txt = f"[T] {label}   ({len(members)}/{total} fighters)"
    surf = font_small.render(txt, True, (235, 220, 170))
    chip = pygame.Rect(16, SCREEN_HEIGHT - 330, surf.get_width() + 24, 30)
    pygame.draw.rect(screen, (18, 18, 26), chip, border_radius=8)
    pygame.draw.rect(screen, (170, 140, 85), chip, 1, border_radius=8)
    screen.blit(surf, (chip.x + 12, chip.y + 6))

    if not getattr(manager, "tactics_menu_open", False):
        return
    # Valikko: käskyt numeroittain (lukitut himmeinä listan alla)
    orders = available_orders(pc)
    locked = [(n, req) for oid, n, _d, req in ORDERS
              if req is not None and oid not in
              (getattr(pc, "tactics", None) or set())]
    row_h = 54
    h = 66 + row_h * len(orders) + (26 * len(locked) if locked else 0) + 14
    panel = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - h // 2,
                        600, h)
    pygame.draw.rect(screen, (16, 16, 24), panel, border_radius=12)
    pygame.draw.rect(screen, (255, 210, 90), panel, 2, border_radius=12)
    head = font_main.render("EXPEDITION ORDERS", True, (255, 210, 90))
    screen.blit(head, (panel.x + 24, panel.y + 16))
    y = panel.y + 58
    for i, (oid, name, desc) in enumerate(orders):
        active = (oid == str(getattr(manager, "expedition_order", "follow")))
        col = (140, 230, 150) if active else (235, 235, 235)
        line = font_main.render(f"{i + 1}.  {name}", True, col)
        screen.blit(line, (panel.x + 36, y))
        sub = font_small.render(desc, True, (170, 170, 180))
        screen.blit(sub, (panel.x + 66, y + 26))
        y += row_h
    for name, req in locked:
        node = _node_name(req)
        line = font_small.render(f"{name} - locked ({node})", True,
                                 (110, 110, 120))
        screen.blit(line, (panel.x + 36, y))
        y += 26
    hint = font_small.render("Press a number - or [T] to close",
                             True, (150, 150, 160))
    screen.blit(hint, (panel.x + 24, panel.bottom - 26))


def _node_name(node_id):
    try:
        from skills.commander_skills_data import COMMANDER_COMMAND_TREE
        return COMMANDER_COMMAND_TREE[node_id]["name"]
    except Exception:
        return node_id


# ----------------------------------------------------------------------
# Commanderin kaatuminen retkellä -> rescue
# ----------------------------------------------------------------------

def commander_down(manager, place_label="the wilds"):
    """Commander kaatui retkellä. Joku raahaa hänet Muckfordiin:
    barracksiin jos tiimi on pystyssä, muuten Sunk Caskiin (Marda perii
    noutopalkkion). Palauttaa next_state-arvon kutsuvalle kartalle."""
    pc = manager.player_character
    pc.is_dead = False
    pc.current_hp = max(1, int(pc.max_hp * 0.4))
    pc.current_stamina = int(pc.max_stamina * 0.5)

    # Herätään seuraavana aamuna (joku kantoi sinua koko yön)
    try:
        clock = manager.world_clock
        clock.advance_day()
        clock.minutes = 8 * 60.0
    except Exception:
        pass

    teammates = [u for u in getattr(manager, "my_team", []) or []
                 if not getattr(u, "is_dead", False)]
    use_barracks = bool(getattr(manager, "team_registered", False)
                        and teammates)

    fee = 0
    if not use_barracks:
        fee = min(RESCUE_FEE, int(getattr(manager, "gold", 0)))
        manager.gold = int(getattr(manager, "gold", 0)) - fee

    manager.pending_rescue = {
        "place": "barracks" if use_barracks else "inn",
        "fee": fee,
        "from": str(place_label),
    }
    # Kaupunkisijainti järkeväksi (kentän koordinaatit eivät saa vuotaa
    # kaupunkiin _city_return_posin kautta)
    pos = getattr(manager, "last_city_pos", None)
    if pos:
        try:
            pc.rect.center = (int(pos[0]), int(pos[1]))
        except Exception:
            pass
    manager.tactics_menu_open = False
    return "barracks_interior" if use_barracks else "muckford_city"


class _Speaker:
    """Kevyt puhuja in-game dialogiin (nimi riittää piirtoon)."""

    def __init__(self, name):
        self.name = name
        self.big_image = None


def deliver_rescue_dialogue(manager, state):
    """Kutsutaan kohteen on_enterissä: avaa heräämisdialogin kerran.
    state = "inn" tai "barracks"."""
    data = getattr(manager, "pending_rescue", None)
    if not data or data.get("place") != state:
        return False
    manager.pending_rescue = None
    origin = data.get("from", "the wilds")
    if state == "inn":
        fee = int(data.get("fee", 0))
        fee_txt = (f"That's {fee} silver for the stretcher and the bed."
                   if fee > 0 else
                   "You owe me for the stretcher - pay when you can.")
        text = (f"Easy now, Commander. A carter found you face-down out "
                f"by {origin} and hauled you to my door. {fee_txt}")
        manager.start_dialogue(_Speaker("Marda"), text)
    else:
        mate = None
        for u in getattr(manager, "my_team", []) or []:
            if not getattr(u, "is_dead", False):
                mate = u
                break
        name = getattr(mate, "name", "One of the fighters")
        text = (f"You're awake! We dragged you back from {origin} - "
                f"you went down hard out there. Rest up before the next "
                f"march, Commander.")
        manager.start_dialogue(mate or _Speaker(name), text)
    return True


# ----------------------------------------------------------------------
# Persistenssi (save_manager kutsuu)
# ----------------------------------------------------------------------

def to_save(manager):
    return {
        "order": str(getattr(manager, "expedition_order", "follow")),
        "party": [u.name for u in getattr(manager, "expedition_party", [])
                  or []],
    }


def from_save(manager, data):
    data = data or {}
    manager.expedition_order = str(data.get("order", "follow"))
    names = list(data.get("party", []) or [])
    roster = list(getattr(manager, "my_team", []) or [])
    sel = []
    for name in names:
        for u in roster:
            if u.name == name and u not in sel:
                sel.append(u)
                break
    manager.expedition_party = sel
