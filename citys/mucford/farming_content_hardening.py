"""Final integration guards for the expanded Muckford farm content."""

from __future__ import annotations

import pygame

from items.farm_potions import IronstemFortifier


_INSTALLED = False


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


def install_farming_content_hardening():
    global _INSTALLED
    if _INSTALLED:
        return

    import citys.mucford.farming_expansion as farming
    import citys.mucford.farming_content as content

    farming.PLOT_LAYOUT = SAFE_PLOT_LAYOUT
    content.EXPANDED_PLOT_LAYOUT = SAFE_PLOT_LAYOUT

    # Every named herb now participates in at least one real potion recipe.
    content.POTION_RECIPES["Ironstem Fortifier"] = {
        "ingredients": {"Ironstem": 2, "Marsh Mint": 1, "Potato": 1},
        "description": "Restores health and stamina for battered fighters.",
        "factory": IronstemFortifier,
    }

    # The animated/official crop layer is drawn after the first-pass progress
    # bar. Draw the bar once more so future full-size art cannot hide growth.
    CropPlot = farming.CropPlot
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
