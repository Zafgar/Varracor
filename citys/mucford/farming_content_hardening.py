"""Final integration guards for the expanded Muckford farm content."""

from __future__ import annotations

import re

import pygame

from items.farm_potions import IronstemFortifier


_INSTALLED = False
MIN_FARM_WORKERS = 6


# Four columns leave a clear corridor beside the farm's eastern apple trees.
SAFE_PLOT_LAYOUT = (
    ("Carrot", 0, 0),
    ("Potato", 1, 0),
    ("Onion", 2, 0),
    ("Carrot", 3, 0),
    ("Potato", 0, 1),
    ("Cabbage", 1, 1),
    ("Turnip", 2, 1),
    ("Onion", 3, 1),
    ("Cabbage", 0, 2),
    ("Turnip", 1, 2),
    ("Bitterleaf", 2, 2),
    ("Marsh Mint", 3, 2),
    ("Yarrow", 0, 3),
    ("Siltroot", 1, 3),
    ("Sunleaf", 2, 3),
    ("Moonpetal", 3, 3),
    ("Ironstem", 0, 4),
    ("Bitterleaf", 1, 4),
    ("Marsh Mint", 2, 4),
    ("Yarrow", 3, 4),
)


def _set_farmer_job(npc):
    ai = getattr(npc, "ai_controller", None)
    if ai is None:
        return False
    ai.job = "Farmer"
    base_name = re.sub(r"\s*\([^)]*\)\s*$", "", str(getattr(npc, "name", "Villager")))
    npc.name = f"{base_name} (Farmer)"
    return True


def install_farming_content_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    import citys.mucford.farming_expansion as farming
    import citys.mucford.farming_content as content
    from ai.villager_ai import VillagerAI

    farming.PLOT_LAYOUT = SAFE_PLOT_LAYOUT
    content.EXPANDED_PLOT_LAYOUT = SAFE_PLOT_LAYOUT

    # Every named herb now participates in at least one real potion recipe.
    content.POTION_RECIPES["Ironstem Fortifier"] = {
        "ingredients": {"Ironstem": 2, "Marsh Mint": 1, "Potato": 1},
        "description": "Restores health and stamina for battered fighters.",
        "factory": IronstemFortifier,
    }

    FarmingSystem = farming.FarmingSystem
    if not getattr(FarmingSystem, "_minimum_farmers_installed", False):
        previous_equip_farmers = FarmingSystem._equip_farmer_npcs

        def _equip_farmer_npcs(self):
            villagers = [
                npc for npc in getattr(self.city, "npcs", [])
                if isinstance(getattr(npc, "ai_controller", None), VillagerAI)
                and not getattr(npc, "rival_info", None)
                and npc is not getattr(self.city, "bram", None)
                and npc is not getattr(self.city, "hamo", None)
                and npc is not getattr(self.city, "farmer_gus", None)
            ]
            farmers = [npc for npc in villagers
                       if getattr(npc.ai_controller, "job", None) == "Farmer"]
            needed = max(0, MIN_FARM_WORKERS - len(farmers))
            if needed:
                candidates = [npc for npc in villagers if npc not in farmers]
                candidates.sort(
                    key=lambda npc: (
                        getattr(npc.ai_controller, "work_ethic", 0.0),
                        getattr(npc, "name", ""),
                    ),
                    reverse=True,
                )
                for npc in candidates[:needed]:
                    if _set_farmer_job(npc):
                        farmers.append(npc)

            previous_equip_farmers(self)

            state = self.manager.npc_state.setdefault("farming", {})
            state["farm_worker_count"] = len([
                npc for npc in villagers
                if getattr(npc.ai_controller, "job", None) == "Farmer"
            ])

        FarmingSystem._equip_farmer_npcs = _equip_farmer_npcs
        FarmingSystem._minimum_farmers_installed = True

    CropPlot = farming.CropPlot

    # Harvest tracking is optional bookkeeping. The actual crop reward must not
    # depend on a fully initialized GameManager, because tests, editor previews
    # and future map tools may use lightweight manager objects.
    if not getattr(CropPlot, "_safe_harvest_ledger_installed", False):
        previous_harvest = CropPlot.harvest

        def harvest(self, manager, harvester, to_storage=False, npc=False):
            if not hasattr(manager, "npc_state") or manager.npc_state is None:
                manager.npc_state = {
                    "global": {"reputation": 0, "flags": {}},
                }
            return previous_harvest(
                self,
                manager,
                harvester,
                to_storage=to_storage,
                npc=npc,
            )

        CropPlot.harvest = harvest
        CropPlot._safe_harvest_ledger_installed = True

    # The animated/official crop layer is drawn after the first-pass progress
    # bar. Draw the bar once more so future full-size art cannot hide growth.
    if not getattr(CropPlot, "_progress_bar_hardening_installed", False):
        previous_draw = CropPlot.draw_on_screen

        def draw_on_screen(self, screen, offset):
            previous_draw(self, screen, offset)
            x = self.rect.x - offset[0]
            y = self.rect.y - offset[1]
            if (x > screen.get_width() or y > screen.get_height()
                    or x + self.WIDTH < 0 or y + self.HEIGHT < 0):
                return
            bar = pygame.Rect(x + 12, y + self.HEIGHT - 12,
                              self.WIDTH - 24, 6)
            pygame.draw.rect(screen, (35, 28, 22), bar, border_radius=3)
            fill = bar.copy()
            fill.w = int(bar.w * self.growth_pct)
            if fill.w > 0:
                color = (85, 180, 90) if self.ready else (110, 155, 80)
                pygame.draw.rect(screen, color, fill, border_radius=3)

        CropPlot.draw_on_screen = draw_on_screen
        CropPlot._progress_bar_hardening_installed = True

    _INSTALLED = True
