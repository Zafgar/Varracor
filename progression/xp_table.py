# progression/xp_table.py
# XP thresholds + helpers used by menus and units.
# Designed for MAX_LEVEL = 30 (future-proof for spell tiers etc.)

from __future__ import annotations

from typing import Dict

# You can tune this later. Current curve matches your original 1-10 table:
# lvl2=100, lvl3=250, lvl4=450, ..., lvl10=2700
XP_STEP_BASE = 50

# Level cap (you wanted lvl 30 long-term)
MAX_LEVEL = 30


def xp_for_level(level: int) -> int:
    """
    Total XP required to reach `level`.
    Level 1 => 0.
    Formula matches the old table exactly for levels 1..10.
    """
    lvl = int(level)
    if lvl <= 1:
        return 0
    if lvl > MAX_LEVEL:
        lvl = MAX_LEVEL
    # 50 * (lvl*(lvl+1)/2 - 1)
    return int(XP_STEP_BASE * ((lvl * (lvl + 1)) // 2 - 1))


# Backwards-compatible alias (some files used this name)
def xp_required_for_level(level: int) -> int:
    return xp_for_level(level)


def level_from_xp(total_xp: int) -> int:
    """
    Convert total_xp -> current level (1..MAX_LEVEL).
    """
    xp = max(0, int(total_xp))
    lvl = 1
    for n in range(2, MAX_LEVEL + 1):
        if xp >= xp_for_level(n):
            lvl = n
        else:
            break
    return lvl


def next_level_xp(total_xp: int) -> int:
    """
    Total XP requirement for the next level (threshold), not remaining XP.
    If already max, returns current threshold.
    """
    lvl = level_from_xp(total_xp)
    if lvl >= MAX_LEVEL:
        return xp_for_level(MAX_LEVEL)
    return xp_for_level(lvl + 1)


def xp_to_next_level(total_xp: int) -> int:
    """
    Remaining XP until next level. If already max level, returns 0.
    """
    lvl = level_from_xp(total_xp)
    if lvl >= MAX_LEVEL:
        return 0
    return max(0, int(next_level_xp(total_xp) - int(total_xp)))


def level_progress_ratio(total_xp: int) -> float:
    """
    Progress within the current level [0..1].
    """
    xp = max(0, int(total_xp))
    lvl = level_from_xp(xp)
    if lvl >= MAX_LEVEL:
        return 1.0
    start = xp_for_level(lvl)
    end = xp_for_level(lvl + 1)
    span = max(1, end - start)
    return max(0.0, min(1.0, (xp - start) / float(span)))


def xp_progress_in_level(total_xp: int) -> int:
    """
    XP gained since the start of the current level.
    """
    xp = max(0, int(total_xp))
    lvl = level_from_xp(xp)
    return max(0, xp - xp_for_level(lvl))


def xp_span_current_level(total_xp: int) -> int:
    """
    XP span from current level start -> next level threshold.
    """
    lvl = level_from_xp(total_xp)
    if lvl >= MAX_LEVEL:
        return 0
    return max(1, xp_for_level(lvl + 1) - xp_for_level(lvl))


# Optional: table for UI/debugging
XP_TABLE: Dict[int, int] = {lvl: xp_for_level(lvl) for lvl in range(1, MAX_LEVEL + 1)}
