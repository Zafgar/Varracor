# npc/npc_registry.py

# Import NPC classes
try:
    from npc.dwarf_league_manager import DwarfLeagueManager
    from npc.griznak_quest_giver import GriznakQuestGiver
    from npc.grand_mortarch import GrandMortarch
    from npc.mnemonic_devourer_npc import MnemonicDevourerNPC
    from npc.commander_npc import CommanderNPC
    from npc.marda_shant_npc import MardaShantNPC
    from npc.gambler_npc import GamblerNPC
    from npc.hamo_npc import HamoNPC
    from npc.school_keeper import KeeperPure, KeeperHoly, KeeperDruid, KeeperManip
    from npc.vortex_mentor import VortexMentor
except ImportError as e:
    print(f"NPC Registry Import Error: {e}")

NPC_DB = {
    "dwarf_league_manager": DwarfLeagueManager if 'DwarfLeagueManager' in locals() else None,
    "griznak_quest_giver": GriznakQuestGiver if 'GriznakQuestGiver' in locals() else None,
    "grand_mortarch": GrandMortarch if 'GrandMortarch' in locals() else None,
    "mnemonic_devourer": MnemonicDevourerNPC if 'MnemonicDevourerNPC' in locals() else None,
    "commander_self": CommanderNPC if 'CommanderNPC' in locals() else None,
    "marda_shant": MardaShantNPC if 'MardaShantNPC' in locals() else None,
    "gambler": GamblerNPC if 'GamblerNPC' in locals() else None,
    "hamo": HamoNPC if 'HamoNPC' in locals() else None,
    "keeper_pure": KeeperPure if 'KeeperPure' in locals() else None,
    "keeper_holy": KeeperHoly if 'KeeperHoly' in locals() else None,
    "keeper_druid": KeeperDruid if 'KeeperDruid' in locals() else None,
    "keeper_manip": KeeperManip if 'KeeperManip' in locals() else None,
    "vortex_mentor": VortexMentor if 'VortexMentor' in locals() else None,
}

def get_npc_class(npc_id):
    return NPC_DB.get(npc_id)