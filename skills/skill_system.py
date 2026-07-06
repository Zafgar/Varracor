from skills.skills_data import SKILL_TREE as SKILLS

def can_unlock(unit, skill_id: str):
    if skill_id not in SKILLS:
        return False, "Unknown Skill"

    s = SKILLS[skill_id]
    if skill_id in unit.unlocked_skills:
        return False, "Already Unlocked"

    # Support both 'requires' and 'prereq'
    reqs = s.get("requires", []) or s.get("prereq", [])
    for req in reqs:
        if req not in unit.unlocked_skills:
            return False, "Prerequisites not met"

    if unit.level < s.get("min_level", 1):
        return False, f"Requires Level {s.get('min_level', 1)}"

    if unit.skill_points < s.get("cost", 1):
        return False, "Not enough Skill Points"

    return True, "Available"

def apply_effect(unit, skill_id: str):
    # Legacy function.
    # New system: Gladiator.calculate_final_stats() handles all effects
    # defined in SKILL_TREE[skill_id]["effects"].
    pass

def unlock_skill(unit, skill_id: str):
    can, reason = can_unlock(unit, skill_id)
    if not can:
        return False, reason

    cost = SKILLS[skill_id].get("cost", 1)
    unit.skill_points -= cost
    unit.unlocked_skills.add(skill_id)
    apply_effect(unit, skill_id)
    return True, "Unlocked"
