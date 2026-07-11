# systems/village_task_manager.py
"""
Kylän pikkutehtävien ajologiikka: mitkä ovat tarjolla (maineen mukaan),
edistyminen, palkintojen jako ja tallennus.
"""
from quests.village_tasks import get_all_village_tasks


class VillageTaskManager:
    def __init__(self):
        self.tasks = {t.id: t for t in get_all_village_tasks()}

    # --- Kysely ---
    def available_for(self, reputation):
        return [t for t in self.tasks.values()
                if t.status == "available" and reputation >= t.rep_req]

    def active_tasks(self):
        return [t for t in self.tasks.values()
                if t.status in ("active", "ready_turnin")]

    def tasks_from(self, giver_name):
        return [t for t in self.tasks.values() if t.giver == giver_name]

    def get(self, task_id):
        return self.tasks.get(task_id)

    # --- Elinkaari ---
    def accept(self, task_id):
        t = self.tasks.get(task_id)
        if t and t.status == "available":
            t.status = "active"
            t.stage_index = 0
            # Talk-stagen ohitus heti (johtolause näytetään dialogissa)
            if t.current_stage and t.current_stage.get("kind") == "talk":
                t.advance()
            return True
        return False

    def notify_collect(self, manager, task_id):
        """Tarkistaa collect-vaiheen inventaariosta ja etenee jos täynnä."""
        t = self.tasks.get(task_id)
        if not t or t.status != "active":
            return False
        st = t.current_stage
        if st and st.get("kind") == "collect":
            have = manager.inventory.get(st["item"], 0)
            if have >= st["count"]:
                t.advance()
                self._skip_talk(t)
                return True
        return False

    def try_deliver(self, manager, task_id, location):
        """Kuluttaa deliver-vaiheen tavarat jos ollaan oikeassa paikassa."""
        t = self.tasks.get(task_id)
        if not t or t.status != "active":
            return False
        st = t.current_stage
        if st and st.get("kind") == "deliver" and st.get("to") == location:
            have = manager.inventory.get(st["item"], 0)
            if have >= st["count"]:
                manager.inventory[st["item"]] = have - st["count"]
                if manager.inventory[st["item"]] <= 0:
                    del manager.inventory[st["item"]]
                t.advance()
                self._skip_talk(t)
                return True
        return False

    def notify_reach(self, task_id, location):
        """Merkitsee reach-vaiheen suoritetuksi kun saavutaan paikkaan."""
        t = self.tasks.get(task_id)
        if not t or t.status != "active":
            return False
        st = t.current_stage
        if st and st.get("kind") == "reach" and st.get("target") == location:
            t.advance()
            self._skip_talk(t)
            return True
        return False

    def _skip_talk(self, t):
        # Talk-vaiheet ovat pelkkää dialogia; ohitetaan automaattisesti
        # edistymislaskennassa (dialogi näyttää tekstin erikseen).
        while (t.status == "active" and t.current_stage
               and t.current_stage.get("kind") == "talk"):
            t.advance()

    def complete(self, manager, task_id):
        """Lunastaa palkinnot ja merkitsee tehtävän tehdyksi."""
        t = self.tasks.get(task_id)
        if not t or t.status != "ready_turnin":
            return None
        r = t.rewards
        gained = self._grant_rewards(manager, r)
        t.status = "done"
        # Kylä muistaa urotyön (näkyy myöhemmin dialogeissa)
        if hasattr(manager, "record_deed"):
            manager.record_deed(f"task_{t.id}",
                                t.deed_text or f"completed '{t.title}'")
        return gained

    def _grant_rewards(self, manager, r):
        gained = []
        if r.get("gold"):
            manager.gold += int(r["gold"])
            gained.append(f"+{int(r['gold'])} Gold")
        if r.get("reputation"):
            try:
                from quest_system import quest_manager
                if quest_manager:
                    quest_manager.add_reputation(int(r["reputation"]))
                    manager.reputation = quest_manager.reputation
                else:
                    manager.reputation += int(r["reputation"])
            except Exception:
                manager.reputation += int(r["reputation"])
            gained.append(f"+{int(r['reputation'])} Rep")
        if r.get("xp"):
            manager.grant_hero_xp(int(r["xp"]))
            gained.append(f"+{int(r['xp'])} XP")
        if r.get("material"):
            for name, cnt in r["material"].items():
                manager.add_material(name, cnt)
                gained.append(f"+{cnt} {name}")
        if r.get("item"):
            try:
                from items.item_registry import create_item
                item = create_item(r["item"])
                if item:
                    manager.equipment_bag.append(item)
                    gained.append(f"Item: {getattr(item, 'name', r['item'])}")
            except Exception:
                pass
        if r.get("fighter"):
            fighter = self._create_fighter(r["fighter"])
            if fighter:
                manager.my_team.add(fighter)
                if hasattr(manager, "_restore_unit_ai"):
                    manager._restore_unit_ai(fighter)
                manager.update_all_groups()
                gained.append(f"New fighter: {fighter.name}")
                # Seppä liittyi -> tiimi saa seppä-perkin
                if getattr(fighter, "is_smith", False):
                    manager.has_smith = True
        if r.get("flag"):
            setattr(manager, r["flag"], True)
        return gained

    def _create_fighter(self, spec):
        from settings import PLAYER_TEAM
        race = spec.get("race", "Human")
        name = spec.get("name", "Recruit")
        try:
            if race == "Human":
                from units.human import Human
                return Human(name, 0, 0, PLAYER_TEAM, spec.get("quality", "Common"))
            if race == "Orc":
                from units.orc import Orc
                return Orc(name, 0, 0, PLAYER_TEAM)
            if race == "Elf":
                from units.elf import Elf
                return Elf(name, 0, 0, PLAYER_TEAM, spec.get("quality", "Common"))
            if race == "Goblin":
                from units.goblin import Goblin
                return Goblin(name, 0, 0, PLAYER_TEAM)
            if race == "Frogfolk":
                from units.frog_smith import FrogSmith
                return FrogSmith(name, 0, 0, PLAYER_TEAM)
        except Exception as e:
            print(f"[VillageTasks] fighter create failed: {e}")
        return None

    # --- Tallennus ---
    def to_dict(self):
        return {tid: t.to_dict() for tid, t in self.tasks.items()}

    def from_dict(self, data):
        for tid, d in (data or {}).items():
            if tid in self.tasks:
                self.tasks[tid].from_dict(d)
