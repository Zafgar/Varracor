import os
import random
from .base_npc import BaseNPC, DialogueNode, DialogueChoice

class DwarfLeagueManager(BaseNPC):
    def __init__(self):
        super().__init__(npc_id="dwarf_league_manager")
        self.name = "Bram 'Mudhand' Carrow"
        
        # ASSETS
        self.portrait_folder = "assets/portraits/dwarf_league_manager"
        self.voice_folder = "assets/voices/dwarf_league_manager"

    def get_portrait_path(self, emotion: str) -> str:
        if not emotion: emotion = "serious"
        return os.path.join(self.portrait_folder, f"{emotion.lower()}.png")

    def get_voice_path(self, emotion: str) -> str:
        if not emotion: emotion = "serious"
        return os.path.join(self.voice_folder, f"{emotion.lower()}.wav")

    def get_dialogue_root(self, context: dict) -> str:
        npc_data = context.get("memory", {}).get(self.npc_id, {})
        flags = npc_data.get("flags", {})

        if not flags.get("intro_done"):
            return "intro_start"
            
        # Tarkista henkilökohtainen maine (Mudhand Rep)
        rep = npc_data.get("relationship", 0)
        
        if rep < -10:
            return "hub_hated"
        elif rep >= 50:
            return "hub_friendly"
        
        return "hub_start"

    def _analyze_roster(self, roster: list) -> tuple:
        """Etsii parhaan yksikön ja antaa siitä kommentin."""
        if not roster: return None, ""
        
        # Etsi eniten tappoja saanut (jos stats-kenttä on olemassa)
        try:
            mvp = max(roster, key=lambda u: getattr(u, "stats", {}).get("kills", 0))
            kills = mvp.stats.get("kills", 0)
            
            if kills > 15:
                return mvp, f"I see {mvp.name} on the kill list again. {kills} confirmed? Good. That brings in the crowd."
            elif kills > 5:
                return mvp, f"{mvp.name} is surviving. That's rare around here."
        except Exception:
            pass # Jos statsit puuttuu tai lista tyhjä
            
        return None, ""

    def get_nodes(self, context: dict) -> dict:
        # Haetaan LeagueEngine ja Roster contextista (jos saatavilla)
        le = context.get("league_engine")
        roster = context.get("player_roster", [])
        reputation = context.get("reputation", 0)
        completed_quests = context.get("completed_quests", [])
        
        # Varmuuskopio jos engine ei ole contextissa (vanha game_manager)
        if not le:
            # Fallback yksinkertaiseen tilaan
            return self._get_fallback_nodes(context)

        # Perustiedot Enginestä
        tier = le.tier
        current_tier_name = le.get_tier_name("1v1")
        
        # Season info (turvallinen haku)
        if hasattr(le, "get_season_info"):
            s_info = le.get_season_info()
            season_num = s_info["number"]
            season_theme = s_info["theme"]
        else:
            season_num = 1
            season_theme = "Spring"

        rank = le.get_player_rank()
        grand_data = le.get_grand_score("PLAYER")
        score = grand_data.get("score", 0)
        
        # Lasketaan pelatut pelit vs vaaditut
        season_done = False
        if hasattr(le, "is_season_complete"):
            season_done = le.is_season_complete()
            
        eligible, reason, _ = le.check_promotion_eligibility()
        
        # State & Flags
        npc_data = context.get("memory", {}).get(self.npc_id, {})
        flags = npc_data.get("flags", {})
        my_rep = npc_data.get("relationship", 0)
        was_rude = flags.get("was_rude", False)
        
        # Tallenna aloituskausi jos ei ole (jotta voidaan laskea kauanko pelaaja jumittaa)
        if "start_season" not in flags:
            flags["start_season"] = season_num
        
        seasons_stuck = season_num - flags.get("start_season", season_num)

        nodes = {}

        # =================================================================
        # 1. INTRO (Päivitetty Season-tiedolla)
        # =================================================================
        team_name = context.get("player", {}).get("team_name", "Mercenaries")
        
        # Määritetään intro-teksti maineen perusteella
        intro_text = ""
        intro_emotion = "serious"
        
        if reputation < 200:
            # Tuntematon keltanokka
            intro_text = f"The dwarf wipes his greasy hands on a leather apron and opens a small, battered ledger. \"'{team_name}'... Right. Another batch of meat for the grinder. I'm Bram. They call me Mudhand. I run the Rookie Circuit.\""
            intro_emotion = "serious"
        else:
            # Tunnettu sankari
            intro_text = f"The dwarf looks up from his ledger, squinting. \"'{team_name}'? I've heard that name. You're the one making noise out in the wilds. I'm Bram Carrow. If you want to fight in my pits, you follow my rules.\""
            intro_emotion = "encouraging"
            # Tunnistaako Rat Kingin tapon? (Quest ID: hunt_01)
            if "hunt_01" in completed_quests:
                intro_text += " Word is you cleared out the Rat King. Impressive work. Let's see if you can handle real warriors."

        nodes["intro_start"] = DialogueNode(
            id="intro_start",
            speaker=self.name,
            emotion="serious",
            text=intro_text,
            choices=[
                DialogueChoice(text="Who are we fighting?", next_node_id="intro_reaction"),
                DialogueChoice(text="Nice to meet you.", next_node_id="intro_reaction")
            ]
        )

        nodes["intro_reaction"] = DialogueNode(
            id="intro_reaction",
            speaker=self.name,
            emotion=intro_emotion,
            text=intro_text,
            choices=[
                DialogueChoice(text="We are here to work and get paid.", next_node_id="intro_good", effects=["rep_plus_5"]),
                DialogueChoice(text="Uh... I think I'm in the wrong room.", next_node_id="intro_bad", effects=["rep_minus_5"]),
                DialogueChoice(text="Just explain the rules, dwarf.", next_node_id="intro_rude"), 
            ]
        )

        nodes["intro_good"] = DialogueNode(
            id="intro_good",
            speaker=self.name,
            emotion="serious",
            text="Good answer. Legends die young. Professionals get rich. Keep your head down, pay your fees, and we'll get along.",
            choices=[DialogueChoice(text="How does the league work?", next_node_id="intro_rules")]
        )
        
        nodes["intro_bad"] = DialogueNode(
            id="intro_bad",
            speaker=self.name,
            emotion="frustrated", 
            text="Lost? The exit is that way. But if you owe money to the wrong people, this is the only place that pays enough to clear it. Your choice.",
            choices=[DialogueChoice(text="Tell me the rules.", next_node_id="intro_rules")]
        )

        nodes["intro_rules"] = DialogueNode(
            id="intro_rules",
            speaker=self.name,
            emotion="serious",
            text="Simple. You fight in 1v1, 3v3, and 5v5 matches. I track the points in this book. Top 2 teams get a shot at the Boss. Win that, and Sera Quench buys your contract for Tier 1. Lose, and you stay in the mud.",
            choices=[DialogueChoice(text="Understood. I'm ready.", next_node_id="intro_end")]
        )

        nodes["intro_rude"] = DialogueNode(
            id="intro_rude",
            speaker=self.name,
            emotion="serious",
            text="In a hurry to die? Fine. Fight, win points, don't cause trouble. Top 2 promote. Everyone else rots.",
            on_enter_effects=["set_flag_was_rude"],
            choices=[DialogueChoice(text="Understood.", next_node_id="intro_end")]
        )
        
        nodes["intro_end"] = DialogueNode(
            id="intro_end",
            speaker=self.name,
            emotion="serious",
            text=f"One last thing: I don't care about your politics or your gods. In the Shanty Yard, the only law is the Ledger. Don't make me write your name in red.",
            on_enter_effects=["set_flag_intro_done"],
            choices=[DialogueChoice(text="Open League", next_node_id=None, effects=["enter_league"])]
        )

        # =================================================================
        # 2. HUB LOGIC (Älykäs tilannetaju)
        # =================================================================
        
        greeting = ""
        emotion = "serious"
        
        # Töykeän pelaajan tervehdys
        if was_rude:
            greeting = "You again. My ledger says you're still breathing. Make it quick."
            emotion = "frustrated"
        
        # A) ONKO KAUSI OHI?
        elif season_done:
            if eligible:
                # Pelaaja on Top 2 -> Mene finaaliin!
                greeting = f"Well, look at that. The numbers don't lie. You qualified. Sera's scouts are watching. Don't embarrass me out there."
                emotion = "encouraging"
            else:
                # Pelaaja pelasi kaiken, mutta ei päässyt (Rank > 2)
                greeting = f"Season's closed. You're Rank {rank}. Not good enough. I need winners, not space-fillers. Reset and try again."
                emotion = "frustrated"
        
        # B) ONKO KAUSI KESKEN, MUTTA TILANNE KRIITTINEN?
        elif not season_done:
            # Tarkista onko mahdollista enää nousta (yksinkertaistettu logiikka)
            games_played_total = sum(grand_data["games"].values())
            # Jos pelejä on pelattu jo jonkin verran ja rank on huono
            if games_played_total >= 4 and rank >= 6:
                greeting = f"I'm looking at your numbers... Rank {rank}? You're bleeding points. Fix it, or find a new line of work."
                emotion = "thinking"
            elif rank <= 2 and games_played_total > 0:
                greeting = f"Rank {rank}. You're making me money. Keep it up, and you might get out of Muckford."
                emotion = "serious"
            else:
                # Normitilanne
                greeting = f"Season {season_num}. Ledger says you're Rank {rank}. The Shanty Yard is open."

        # C) JUMITUKSEN TARKISTUS (Jos ei ole kausi ohi -tilassa)
        if not season_done and seasons_stuck > 2:
            greeting = f"You've been in my circuit for {seasons_stuck} seasons. You're starting to smell like the furniture. Promote or quit."
            emotion = "frustrated"

        # D) ROSTERIN KEHU (Lisätään perään jos on)
        mvp_unit, mvp_msg = self._analyze_roster(roster)
        if mvp_unit and random.random() < 0.4: # 40% mahis että kehuu yksikköä tervehdyksen sijaan/lisäksi
            greeting += f" And hey... {mvp_msg}"
            emotion = "encouraging"

        # E) LIIGAN JOHTAJAN KOMMENTOINTI (Jos ei olla töykeitä)
        if not was_rude and not season_done:
            standings = le.get_grand_slam_standings()
            # Etsi paras tiimi joka EI ole pelaaja
            top_rival = next((t for t in standings if t['team_id'] != "PLAYER"), None)
            
            if top_rival and top_rival['score'] > score:
                diff = top_rival['score'] - score
                greeting += f" Watch out for {top_rival['team_name']}. They're {diff} points ahead. I hate their manager, so beat them."

        # Päävalikko
        nodes["hub_start"] = DialogueNode(
            id="hub_start",
            speaker=self.name,
            emotion=emotion,
            text=greeting,
            choices=[
                DialogueChoice(text="Let me fight.", next_node_id=None, effects=["enter_league"]),
                DialogueChoice(text="Any news from the upper tiers?", next_node_id="gossip_tiers"),
                DialogueChoice(text="Who are you really?", next_node_id="lore_bram"),
                DialogueChoice(text="See you later.", next_node_id=None),
            ]
        )

        # Friendly Hub (High Rep)
        nodes["hub_friendly"] = DialogueNode(
            id="hub_friendly",
            speaker=self.name,
            emotion="encouraging",
            text=f"Ah, my reliable earner. The books look good when you're fighting. What do you need?",
            choices=[
                DialogueChoice(text="Let me fight.", next_node_id=None, effects=["enter_league"]),
                DialogueChoice(text="Any tips for the arena?", next_node_id="give_advice"),
                DialogueChoice(text="See you later.", next_node_id=None),
            ]
        )

        # Hated Hub (Low Rep)
        nodes["hub_hated"] = DialogueNode(
            id="hub_hated",
            speaker=self.name,
            emotion="frustrated",
            text=f"You're a liability. You cause trouble and you lose matches. Turn it around, or I'll have the guards throw you in the river.",
            choices=[
                DialogueChoice(text="I'll win the next one.", next_node_id=None, effects=["enter_league"]),
                DialogueChoice(text="[Leave]", next_node_id=None),
            ]
        )

        # Gossip
        nodes["gossip_tiers"] = DialogueNode(
            id="gossip_tiers",
            speaker=self.name,
            emotion="serious",
            text="Sera Quench is looking for flash and style. I just want you to survive. If you promote, you're her problem. Until then, you're mine.",
            choices=[DialogueChoice(text="Back to business.", next_node_id="hub_start")]
        )

        # Vinkit
        tips = [
            "Don't trust the 'Unclaimed Five'. They fight dirty. I hate cleaning up their mess.",
            "If you need cheap healing, go see Sister Rhea. I have an arrangement with her.",
            "Hamo the Goblin pays well for monster parts. It keeps the streets clean and my pockets full.",
            "Heavy armor is good for 3v3, but in a duel? Speed kills.",
            "Pay your debts. That's the only rule that matters.",
            f"You're currently Rank {rank}. Only the Top 2 matter. Second place is the first loser, but it still qualifies.",
        ]
        if mvp_unit:
            tips.append(f"Keep {mvp_unit.name} alive at all costs. They are carrying your team.")

        nodes["give_advice"] = DialogueNode(
            id="give_advice",
            speaker=self.name,
            emotion="serious",
            text=random.choice(tips),
            choices=[DialogueChoice(text="Thanks.", next_node_id="hub_start")]
        )
        
        # Lore: Bram
        nodes["lore_bram"] = DialogueNode(
            id="lore_bram",
            speaker=self.name,
            emotion="serious",
            text="I used to fight in these pits. I know what mud tastes like. Now I make sure the gates stay open and the gold stays counted. I'm a realist, Commander. Not a hero.",
            choices=[DialogueChoice(text="Fair enough.", next_node_id="hub_start")]
        )

        return nodes

    def _get_fallback_nodes(self, context):
        """Vanha logiikka siltä varalta että Engineä ei löydy."""
        nodes = {}
        nodes["hub_start"] = DialogueNode(
            id="hub_start", speaker=self.name, emotion="serious",
            text="The league is waiting. Go fight.",
            choices=[DialogueChoice(text="Open League", next_node_id=None, effects=["enter_league"])]
        )
        return nodes