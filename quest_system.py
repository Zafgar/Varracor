# quest_system.py
import pygame

# Haetaan tehtävät rekisteristä
try:
    from quest_registry import get_all_quest_definitions
except ImportError:
    # Fallback, jos tiedostoa ei vielä ole
    print("Warning: quest_registry.py not found. Quests will be empty.")
    def get_all_quest_definitions(): return []

class QuestState:
    """
    Pitää kirjaa yksittäisen questin tilasta (tallennusdata).
    Erottaa "Static Data" (QuestDefinition) ja "Runtime Data" (tämä luokka).
    """
    def __init__(self, definition):
        self.definition = definition
        self.id = definition.id
        self.status = "locked" # locked, available, active, completed
        self.is_finished = False # Onko palkinnot lunastettu (loppudialogi käyty)
        self.progress = 0 # Esim. kerätyt kakat

    # Oikopolkuja, jotta vanha koodi (esim menu) toimii ilman suuria muutoksia
    @property
    def title(self): return self.definition.title
    @property
    def description(self): return self.definition.description
    @property
    def rep_req(self): return self.definition.rep_req
    @property
    def reward_text(self): return self.definition.reward_text
    @property
    def boss_id(self): return self.definition.boss_id
    @property
    def rewards(self): return self.definition.rewards
    @property
    def category(self): return getattr(self.definition, "category", "side")
    @property
    def objectives(self): return getattr(self.definition, "objectives", [])
    @property
    def giver(self): return getattr(self.definition, "giver", None)
    @property
    def required_amount(self):
        return int(getattr(self.definition, "required_amount", 0) or 0)

    @property
    def completed(self): return self.status == "completed" or self.is_finished
    @completed.setter
    def completed(self, val): 
        if val: self.status = "completed"

    @property
    def unlocked(self): return self.status != "locked"
    @unlocked.setter
    def unlocked(self, val):
        if val and self.status == "locked": self.status = "available"


class QuestManager:
    def __init__(self):
        self.reputation = 0
        self.quests = {} # id -> QuestState
        # Journal-seuranta (pelitesti 27): mitkä questit näkyvät HUD-
        # seurannassa. Untracked-setti - oletuksena kaikki aktiiviset
        # seurataan, ja pelaaja voi poistaa/lisätä seurannasta journalista.
        self.untracked = set()

        # --- TAISTELUN MUISTI ---
        self.pending_reaction = False
        self.last_battle_result = None # "win" tai "loss"
        
        self._load_quests()
        self.check_unlocks() # TÄRKEÄ: Tarkista heti alussa, mitkä questit aukeavat (esim. rep 0 questit)

    def _load_quests(self):
        """Lataa questit rekisteristä ja luo niille tilat"""
        defs = get_all_quest_definitions()
        for d in defs:
            self.quests[d.id] = QuestState(d)

    def add_reputation(self, amount):
        self.reputation += amount
        self.check_unlocks()

    def check_unlocks(self):
        """Tarkistaa aukeaako uusia tehtäviä maineen perusteella"""
        for q in self.quests.values():
            if q.status == "locked" and self.reputation >= q.rep_req:
                q.status = "available"
                print(f"Quest Unlocked: {q.title}")

    # --- UUSI: DIALOGIN YLIKIRJOITUS ---
    def get_npc_dialogue_override(self, npc_id):
        """
        Tarkistaa, onko jollain aktiivisella tai juuri valmistuneella 
        questilla erityistä sanottavaa tälle NPC:lle.
        """
        # 1. Tarkista Completed (mutta ei finished) - Pelaaja palauttaa tehtävää
        for q in self.quests.values():
            if q.status == "completed" and not q.is_finished:
                # Kysy QuestDefinitionilta dialogia tilalle "completed"
                dialogue = q.definition.get_dialogue_for_npc(npc_id, "completed")
                if dialogue: return dialogue

        # 2. Tarkista Active - Pelaaja on tehtävän aikana
        for q in self.quests.values():
            if q.status == "active":
                dialogue = q.definition.get_dialogue_for_npc(npc_id, "active")
                if dialogue: return dialogue

        # 3. Tarkista Available - Pelaaja on ottamassa tehtävää
        for q in self.quests.values():
            if q.status == "available":
                dialogue = q.definition.get_dialogue_for_npc(npc_id, "available")
                if dialogue: return dialogue

        return None

    def npc_has_actionable_quest(self, npc_id):
        """True jos NPC:llä on quest jonka voi OTTAA tai PALAUTTAA juuri
        nyt. Kojujen E-intercept käyttää tätä: active-tilassa (haku
        kesken) kojun kauppa saa aueta normaalisti, jotta pelaaja pääsee
        yhä ostoksille questin aikana."""
        for q in self.quests.values():
            if q.status == "completed" and not q.is_finished and \
                    q.definition.get_dialogue_for_npc(npc_id, "completed"):
                return True
        for q in self.quests.values():
            if q.status == "available" and \
                    q.definition.get_dialogue_for_npc(npc_id, "available"):
                return True
        return False

    # --- QUEST LOGIIKKA ---

    def accept_quest(self, quest_id):
        """Siirtää tehtävän 'active'-tilaan"""
        if quest_id in self.quests:
            self.quests[quest_id].progress = 0 # Nollaa progress
            self.quests[quest_id].status = "active"
            self.untracked.discard(quest_id)  # uusi quest oletuksena seurannassa
            print(f"Started quest: {quest_id}")

    # --- JOURNAL-SEURANTA (pelitesti 27) ---
    def is_tracked(self, quest_id):
        return quest_id not in self.untracked

    def set_tracked(self, quest_id, tracked):
        if tracked:
            self.untracked.discard(quest_id)
        else:
            self.untracked.add(quest_id)

    def toggle_tracked(self, quest_id):
        self.set_tracked(quest_id, quest_id in self.untracked)

    def finish_quest(self, quest_id):
        """Kutsutaan dialogista, kun palkinnot lunastetaan"""
        if quest_id in self.quests:
            q = self.quests[quest_id]
            if q.status == "completed":
                q.is_finished = True
                # Jaa palkinnot tässä
                if q.rewards:
                    # Huom: Tämä vaatisi pääsyn GameManageriin. 
                    # Nyt luotamme siihen että GameManager hoitaa palkinnot 'finish_quest' efektin kautta.
                    pass
                
                # Jos quest on toistettava (kuten manure), resetoi se
                if quest_id == "quest_manure_cleanup":
                    q.status = "available"
                    q.is_finished = False
                    q.progress = 0
                    
                print(f"Quest Finished: {quest_id}")
                return q.rewards
        return None

    def complete_quest_by_boss(self, boss_id):
        """Merkitsee tehtävän suoritetuksi bossin tapon jälkeen"""
        for q in self.quests.values():
            # Hyväksy aktiiviset tai 'available' (jos pelaaja unohti hyväksyä mutta tappoi bossin silti)
            if q.boss_id == boss_id and not q.completed:
                q.status = "completed"
                self.add_reputation(q.rewards.get("reputation", 0))
                print(f"QUEST COMPLETED: {q.title}!")
                print(f"Rewards: {q.reward_text}")
                return q
        return None
        
    def get_quest_status(self, quest_id):
        if quest_id in self.quests:
            return self.quests[quest_id].status
        return "locked"
        
    def get_quest(self, quest_id):
        return self.quests.get(quest_id)

    # --- UI & REAKTIOT ---

    def set_battle_result(self, result):
        self.last_battle_result = result
        self.pending_reaction = True 

    def clear_reaction(self):
        self.pending_reaction = False
        self.last_battle_result = None

    def any_available_quests(self):
        # Palauttaa tosi jos on tehtäviä jotka eivät ole finished
        return any(q.status != "locked" and not q.is_finished for q in self.quests.values())

    def get_goblin_dialogue(self):
        # Valikon pikkuteksti
        if self.pending_reaction:
            if self.last_battle_result == "loss":
                return "You look terrible. Did they beat you up?"
            elif self.last_battle_result == "win":
                return "Hmph. Not dead yet? Impressive."
        
        # Etsi aktiivisia tai available
        active = [q for q in self.quests.values() if q.status == "active"]
        if active:
            return f"Go deal with {active[0].title}. Then we talk."
            
        available = [q for q in self.quests.values() if q.status == "available"]
        if available:
            return "Pick a contract. I haven't got all day."

        return "Nothing for you right now. Scram."

    # Yhteensopivuus vanhan UI-koodin kanssa (listana)
    @property
    def quests_list(self):
        return list(self.quests.values())
    
    # Jotta quest_menu.py:n "quest_manager.quests" kutsu toimii (se odottaa listaa)
    def __iter__(self):
        return iter(self.quests.values())

# Globaali instanssi
quest_manager = QuestManager()