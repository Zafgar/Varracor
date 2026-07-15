# spells/casting.py
"""Cast time, interrupt ja counterspell -perusta.

Kovemmat loitsut latautuvat ennen laukeamista (cast time). Latautuva loitsu
voidaan keskeyttää:
- vahingolla (jos interruptible)
- counterspellillä (jos counterable)
- liikkeellä / käskystä (cancel)

Tyypistä riippuen loitsu JUURRUTTAA (rooted) loitsijan paikalleen latauksen
ajaksi. Valmistuessaan cast laukaisee efektin (on_complete)."""

import math

INTERRUPT_DAMAGE = "damage"
INTERRUPT_COUNTER = "counter"
INTERRUPT_MOVE = "move"
INTERRUPT_CANCEL = "cancel"


class Cast:
    """Yksittäisen latautuvan loitsun tila."""

    def __init__(self, caster, spell, total_frames, on_complete,
                 rooted=True, interruptible=True, counterable=True):
        self.caster = caster
        self.spell = spell
        self.total = max(1, int(total_frames))
        self.elapsed = 0
        self.on_complete = on_complete
        self.rooted = bool(rooted)
        self.interruptible = bool(interruptible)
        self.counterable = bool(counterable)
        self.done = False
        self.fired = False
        self.interrupted_by = None

    @property
    def progress(self):
        return min(1.0, self.elapsed / self.total)

    @property
    def remaining(self):
        return max(0, self.total - self.elapsed)

    def tick(self, manager=None):
        if self.done:
            return
        self.elapsed += 1
        if self.elapsed >= self.total:
            self.fire()

    def fire(self):
        if self.done:
            return
        self.done = True
        self.fired = True
        try:
            if self.on_complete:
                self.on_complete()
        except Exception:
            pass

    def interrupt(self, reason=INTERRUPT_CANCEL):
        """Keskeyttää latauksen (ei laukaise efektiä). Palauttaa True jos
        keskeytys meni läpi."""
        if self.done:
            return False
        if reason == INTERRUPT_DAMAGE and not self.interruptible:
            return False
        if reason == INTERRUPT_COUNTER and not self.counterable:
            return False
        self.done = True
        self.interrupted_by = reason
        return True


def start_cast(caster, spell, total_frames, on_complete, rooted=True,
               interruptible=True, counterable=True):
    c = Cast(caster, spell, total_frames, on_complete, rooted,
             interruptible, counterable)
    caster.active_cast = c
    return c


def tick_caster(caster, manager=None):
    """Kutsutaan casterin update():ssa: edistää aktiivista castia ja siivoaa
    valmiin/keskeytetyn."""
    c = getattr(caster, "active_cast", None)
    if c is None:
        return
    c.tick(manager)
    if c.done:
        caster.active_cast = None


def is_casting(caster):
    c = getattr(caster, "active_cast", None)
    return c is not None and not c.done


def is_rooted(caster):
    """True jos caster on juurrutettu latauksen ajaksi (ei saa liikkua)."""
    c = getattr(caster, "active_cast", None)
    return c is not None and not c.done and c.rooted


def cancel_cast(caster, reason=INTERRUPT_CANCEL):
    c = getattr(caster, "active_cast", None)
    if c is not None and c.interrupt(reason):
        caster.active_cast = None
        return True
    return False


def on_caster_damaged(caster):
    """Vahinko keskeyttää latauksen jos loitsu on interruptible."""
    c = getattr(caster, "active_cast", None)
    if c is not None and not c.done and c.interruptible:
        if c.interrupt(INTERRUPT_DAMAGE):
            caster.active_cast = None
            return True
    return False


def on_caster_moved(caster):
    """Liike keskeyttää juurruttavan (rooted) loitsun latauksen."""
    c = getattr(caster, "active_cast", None)
    if c is not None and not c.done and c.rooted:
        if c.interrupt(INTERRUPT_MOVE):
            caster.active_cast = None
            return True
    return False


def counter_cast(counterer, units, rng=420):
    """Counterspell: keskeyttää lähimmän vastustajan counterable-latauksen
    kantaman sisällä. Palauttaa keskeytetyn casterin tai None."""
    best = None
    best_d = rng
    cx, cy = counterer.rect.center
    my = getattr(counterer, "team_color", None)
    for u in units:
        if u is counterer or getattr(u, "team_color", None) == my:
            continue
        c = getattr(u, "active_cast", None)
        if c is None or c.done or not c.counterable:
            continue
        d = math.hypot(u.rect.centerx - cx, u.rect.centery - cy)
        if d <= best_d:
            best_d = d
            best = u
    if best is not None:
        best.active_cast.interrupt(INTERRUPT_COUNTER)
        best.active_cast = None
        return best
    return None
