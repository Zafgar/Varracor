# Muckford farming art contract

The farming code works without external images. It draws procedural soil,
crops, flowers, moving leaves, pollen and water sparkles until final artwork is
added.

## Crop stage images

Optional crop art belongs in:

```text
assets/tiles/farm/crops/<crop>_stage_<stage>.png
```

Each image is scaled to **220 × 138 px** and should use a transparent
background. Stages are:

- `stage_0`: planted soil / first sprouts
- `stage_1`: young crop
- `stage_2`: half-grown crop
- `stage_3`: nearly mature crop
- `stage_4`: harvest-ready crop

Supported crop slugs:

```text
carrot
potato
onion
cabbage
turnip
bitterleaf
marsh_mint
yarrow
siltroot
sunleaf
moonpetal
ironstem
```

Example:

```text
assets/tiles/farm/crops/moonpetal_stage_4.png
```

The growth bar is drawn by code over the final image, so official artwork does
not need to contain UI.

## Potion icons

Optional potion art belongs in `assets/items/potions/`:

```text
bitterleaf_tonic.png
marshmint_draught.png
siltroot_antidote.png
moonpetal_elixir.png
sunleaf_restorative.png
ironstem_fortifier.png
```

Square transparent images are recommended. The inventory UI scales them to the
slot size. Procedural coloured bottles are used when files are missing.

## Harvesting tools

Optional equipped/inventory art paths:

```text
assets/gear/tools/crude_harvest_sickle.png
assets/gear/tools/iron_harvest_sickle.png
assets/gear/tools/guild_harvest_scythe.png
```

Transparent, vertically oriented tool images work best. The code currently
scales them to approximately 24 × 42 px while equipped and draws a procedural
sickle when the image is missing.

## Gameplay notes for art production

- Crop plots are non-blocking and arranged as a 4 × 5 grid.
- The eastern side of the farm remains open for apple trees and NPC travel.
- Herbs use visible blossoms at higher growth stages.
- Wind and storm weather increase procedural leaf sway.
- Watered soil receives small blue highlights until the crop is ready.
- NPC farmers use the same crop objects and harvesting effects as the player.
