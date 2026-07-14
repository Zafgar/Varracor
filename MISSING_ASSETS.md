# Puuttuvat assetit

Generoitu komennolla `python tools/asset_scan.py` — aja uudelleen
aina kun lisäät tiedostoja, niin lista pysyy ajan tasalla.

- Koodissa viitattuja tiedostoja: **211**
- Löytyy levyltä: **0**
- Puuttuu: **211**

Laita tiedosto täsmälleen alla olevaan polkuun (suhteessa pelin
juurikansioon), niin peli löytää sen automaattisesti — koodia ei
tarvitse muuttaa. Peli toimii myös ilman näitä (procedural fallback).

## assets/gear/ (45 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/gear/axes/axe_1.wav` | ääni | sound_manager.py, tests/test_asset_studio.py |
| `assets/gear/axes/axe_2.wav` | ääni | sound_manager.py |
| `assets/gear/axes/axe_3.wav` | ääni | sound_manager.py |
| `assets/gear/axes/axe_4.wav` | ääni | sound_manager.py |
| `assets/gear/axes/scrap_axe.png` | kuva | items/axes/scrap_axe.py, tests/test_asset_studio.py |
| `assets/gear/axes/weak_axe.png` | kuva | items/axes/weak_axe.py, tests/test_asset_studio.py |
| `assets/gear/books/scrap_book.png` | kuva | items/books/scrap_book.py |
| `assets/gear/books/weak_book.png` | kuva | items/books/weak_book.py |
| `assets/gear/bows/scrap_bow.png` | kuva | items/bows/scrap_bow.py |
| `assets/gear/bows/weak_bow.png` | kuva | items/bows/weak_bow.py |
| `assets/gear/crossbows/scrap_crossbow.png` | kuva | items/crossbows/scrap_crossbow.py |
| `assets/gear/crossbows/weak_crossbow.png` | kuva | items/crossbows/weak_crossbow.py |
| `assets/gear/daggers/scrap_dagger.png` | kuva | items/daggers/scrap_dagger.py |
| `assets/gear/daggers/weak_dagger.png` | kuva | items/daggers/weak_dagger.py |
| `assets/gear/frames/item_frame.png` | kuva | menus/shop_menu.py |
| `assets/gear/maces/scrap_mace.png` | kuva | items/maces/scrap_mace.py |
| `assets/gear/maces/weak_mace.png` | kuva | items/maces/weak_mace.py |
| `assets/gear/shields/scrap_shield.png` | kuva | items/shields/scrap_shield.py |
| `assets/gear/shields/weak_shield.png` | kuva | items/shields/weak_shield.py |
| `assets/gear/spears/scrap_spear.png` | kuva | items/spears/scrap_spear.py |
| `assets/gear/spears/weak_spear.png` | kuva | items/spears/weak_spear.py |
| `assets/gear/staves/scrap_staff.png` | kuva | items/staves/scrap_staff.py |
| `assets/gear/staves/weak_staff.png` | kuva | items/staves/weak_staff.py |
| `assets/gear/swords/scrap_sword.png` | kuva | items/swords/scrap_sword.py |
| `assets/gear/swords/vortex_blade_artifact.png` | kuva | items/swords/vortex_blade.py |
| `assets/gear/swords/vortex_blade_attack_1.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_blade_attack_2.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_blade_attack_3.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_blade_attack_4.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_wave_fly_1.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_wave_impact.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_wave_load.wav` | ääni | sound_manager.py |
| `assets/gear/swords/vortex_wave_release.wav` | ääni | sound_manager.py |
| `assets/gear/swords/weak_sword.png` | kuva | items/swords/weak_sword.py |
| `assets/gear/tools/bucket_empty.png` | kuva | items/tools/bucket.py, units/villager.py |
| `assets/gear/tools/bucket_milk.png` | kuva | items/tools/bucket.py, units/villager.py |
| `assets/gear/tools/bucket_water.png` | kuva | items/tools/bucket.py, units/villager.py |
| `assets/gear/tools/crude_harvest_sickle.png` | kuva | items/tools/harvest_tools.py |
| `assets/gear/tools/fishing_rod.png` | kuva | items/tools/fishing_rod.py |
| `assets/gear/tools/guild_harvest_scythe.png` | kuva | items/tools/harvest_tools.py |
| `assets/gear/tools/iron_harvest_sickle.png` | kuva | items/tools/harvest_tools.py |
| `assets/gear/tools/lute.png` | kuva | items/tools/bard_instrument.py |
| `assets/gear/tools/weak_lumberaxe.png` | kuva | items/tools/weak_lumberaxe.py, items/tools/woodcutters_axe.py |
| `assets/gear/tools/weak_pickaxe.png` | kuva | items/tools/weak_pickaxe.py |
| `assets/gear/tools/woodcutters_axe.png` | kuva | items/tools/woodcutters_axe.py |

## assets/icons/ (4 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/icons/materials/egg.png` | kuva | units/villager.py |
| `assets/icons/materials/meat.png` | kuva | units/villager.py |
| `assets/icons/materials/rat_tail.png` | kuva | items/material_registry.py |
| `assets/icons/materials/scrap_iron.png` | kuva | units/villager.py |

## assets/images/ (2 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/images/hub_background.png` | kuva | menus/town_hub.py |
| `assets/images/menu_background.png` | kuva | menus/main_menu.py |

## assets/items/ (6 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/items/potions/bitterleaf_tonic.png` | kuva | items/farm_potions.py |
| `assets/items/potions/ironstem_fortifier.png` | kuva | items/farm_potions.py |
| `assets/items/potions/marshmint_draught.png` | kuva | items/farm_potions.py |
| `assets/items/potions/moonpetal_elixir.png` | kuva | items/farm_potions.py |
| `assets/items/potions/siltroot_antidote.png` | kuva | items/farm_potions.py |
| `assets/items/potions/sunleaf_restorative.png` | kuva | items/farm_potions.py |

## assets/music/ (14 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/music/city_theme.mp3` | musiikki | citys/rattlebridge/rattlebridge_city_menu.py |
| `assets/music/crypt_theme.mp3` | musiikki | citys/mucford/mine_cave_menu.py |
| `assets/music/crypt_theme.wav` | ääni | maps/bog_1/mission.py, maps/crypt_1/mission.py |
| `assets/music/menu_theme.mp3` | musiikki | menus/main_menu.py |
| `assets/music/menu_theme.wav` | ääni | menus/main_menu.py |
| `assets/music/mnemonic_battle.wav` | ääni | citys/mucford/forest_road_menu.py |
| `assets/music/muckford_intro.wav` | ääni | menus/muckford_intro_screen.py |
| `assets/music/rat_boss_theme.wav` | ääni | bosses/rat_king/mission.py, maps/rat_sewer/mission.py |
| `assets/music/swamp_loop.mp3` | musiikki | maps/bog_1/mission.py |
| `assets/music/swamp_loop.wav` | ääni | maps/bog_1/mission.py |
| `assets/music/swamp_theme.mp3` | musiikki | citys/mucford/forest_road_menu.py, citys/mucford/mine_road_menu.py, citys/mucford/muckford_city_menu.py (+3 muuta) |
| `assets/music/swamp_theme.wav` | ääni | maps/bog_1/mission.py |
| `assets/music/tavern_theme.mp3` | musiikki | citys/rattlebridge/the_span_menu.py |
| `assets/music/town_hub.wav` | ääni | menus/town_hub.py |

## assets/narrator/ (4 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/narrator/intro_1.mp3` | musiikki | menus/intro_screen.py |
| `assets/narrator/intro_2.mp3` | musiikki | menus/muckford_intro_screen.py |
| `assets/narrator/intro_music.wav` | ääni | menus/intro_screen.py |
| `assets/narrator/muckford_intro.wav` | ääni | menus/muckford_intro_screen.py |

## assets/portraits/ (1 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/portraits/goblin/neutral.png` | kuva | npc/gambler_npc.py |

## assets/races/ (2 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/races/human/human_idle_1.png` | kuva | tests/test_asset_studio.py |
| `assets/races/orc/orc_idle_1.png` | kuva | tests/test_asset_studio.py |

## assets/sfx/ (35 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/sfx/animals/moo.wav` | ääni | sound_manager.py |
| `assets/sfx/click.wav` | ääni | ui_kit.py |
| `assets/sfx/fist/fist_1.wav` | ääni | sound_manager.py |
| `assets/sfx/fist/fist_2.wav` | ääni | sound_manager.py |
| `assets/sfx/fist/fist_3.wav` | ääni | sound_manager.py |
| `assets/sfx/fist/fist_4.wav` | ääni | sound_manager.py |
| `assets/sfx/houses/fireplace_loop.wav` | ääni | sound_manager.py |
| `assets/sfx/houses/tavern_ambient.wav` | ääni | sound_manager.py |
| `assets/sfx/hover.wav` | ääni | sound_manager.py, ui_kit.py |
| `assets/sfx/mining/mining_break.wav` | ääni | sound_manager.py |
| `assets/sfx/mining/mining_hit.wav` | ääni | sound_manager.py |
| `assets/sfx/mining/mining_success.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/Close_thunder_crack_1.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/Close_thunder_crack_2.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/Close_thunder_crack_3.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/Close_thunder_crack_4.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/rain_medium.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/wind_loop_gentle.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/wind_loop_outside_normal.wav` | ääni | sound_manager.py |
| `assets/sfx/nature/wind_outside_medium.wav` | ääni | sound_manager.py |
| `assets/sfx/spells/commander/vortex_slash.wav` | ääni | sound_manager.py |
| `assets/sfx/spells/commander/vortex_warp.wav` | ääni | sound_manager.py |
| `assets/sfx/undead/undead_attack_1.wav` | ääni | sound_manager.py |
| `assets/sfx/undead/undead_attack_2.wav` | ääni | sound_manager.py |
| `assets/sfx/undead/undead_attack_3.wav` | ääni | sound_manager.py |
| `assets/sfx/undead/undead_attack_4.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/devourer_scream_loop.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_blast.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_end.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_explosion.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_loop.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_missile_loop.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_shout.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_spawn.wav` | ääni | sound_manager.py |
| `assets/sfx/vortex/vortex_suction.wav` | ääni | sound_manager.py |

## assets/sounds/ (11 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/sounds/battle_theme.mp3` | musiikki | main.py |
| `assets/sounds/boss_roar.wav` | ääni | sound_manager.py |
| `assets/sounds/bow_shoot.wav` | ääni | sound_manager.py |
| `assets/sounds/click.wav` | ääni | sound_manager.py |
| `assets/sounds/coin.wav` | ääni | sound_manager.py |
| `assets/sounds/error.wav` | ääni | sound_manager.py |
| `assets/sounds/heal.wav` | ääni | sound_manager.py |
| `assets/sounds/hit_hurt.wav` | ääni | sound_manager.py |
| `assets/sounds/sewer_ambience.wav` | ääni | bosses/rat_king/mission.py |
| `assets/sounds/sword_swing.wav` | ääni | sound_manager.py |
| `assets/sounds/win_fanfare.wav` | ääni | sound_manager.py |

## assets/tiles/ (15 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/tiles/barracks/desk.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/barracks/hearth.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/barracks/long_table.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/barracks/plans_board.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/barracks/training_dummy.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/barracks/trophy_shelf.png` | kuva | citys/mucford/barracks_interior_arena.py |
| `assets/tiles/farm/manure.png` | kuva | units/villager.py |
| `assets/tiles/floors/muckford_forest.png` | kuva | citys/mucford/forest_road_arena.py |
| `assets/tiles/floors/road_brick_horizontal.png` | kuva | citys/mucford/forest_road_arena.py |
| `assets/tiles/houses/floor_wood_poor.png` | kuva | citys/mucford/tavern_menu.py |
| `assets/tiles/interiors/bench.png` | kuva | citys/mucford/city_interiors.py |
| `assets/tiles/interiors/counter.png` | kuva | citys/mucford/city_interiors.py |
| `assets/tiles/interiors/odds_board.png` | kuva | citys/mucford/city_interiors.py |
| `assets/tiles/interiors/trophy_case.png` | kuva | citys/mucford/city_interiors.py |
| `assets/tiles/muckford/barrel.png` | kuva | units/villager.py |

## assets/ui/ (54 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/ui/btn_boss_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_boss_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_boss_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_exit_hover.png` | kuva | game_manager.py, menus/main_menu.py, menus/mission_prepare_menu.py (+2 muuta) |
| `assets/ui/btn_exit_idle.png` | kuva | game_manager.py, menus/main_menu.py, menus/mission_prepare_menu.py (+2 muuta) |
| `assets/ui/btn_exit_pressed.png` | kuva | game_manager.py, menus/main_menu.py, menus/mission_prepare_menu.py (+2 muuta) |
| `assets/ui/btn_guild_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_guild_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_guild_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hospital_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hospital_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hospital_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hub_hover.png` | kuva | game_manager.py |
| `assets/ui/btn_hub_idle.png` | kuva | game_manager.py |
| `assets/ui/btn_hub_pressed.png` | kuva | game_manager.py |
| `assets/ui/btn_hunt_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hunt_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_hunt_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_league_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_league_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_league_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_load_hover.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_load_idle.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_load_pressed.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_mage_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_mage_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_mage_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_manager_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_manager_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_manager_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_options_hover.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_options_idle.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_options_pressed.png` | kuva | game_manager.py, menus/main_menu.py |
| `assets/ui/btn_recruit_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_recruit_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_recruit_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_resume_hover.png` | kuva | game_manager.py |
| `assets/ui/btn_resume_idle.png` | kuva | game_manager.py |
| `assets/ui/btn_resume_pressed.png` | kuva | game_manager.py |
| `assets/ui/btn_save_hover.png` | kuva | game_manager.py |
| `assets/ui/btn_save_idle.png` | kuva | game_manager.py |
| `assets/ui/btn_save_pressed.png` | kuva | game_manager.py |
| `assets/ui/btn_shop_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_shop_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_shop_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_start_hover.png` | kuva | menus/main_menu.py, menus/mission_prepare_menu.py, menus/prepare_menu.py |
| `assets/ui/btn_start_idle.png` | kuva | menus/main_menu.py, menus/mission_prepare_menu.py, menus/prepare_menu.py |
| `assets/ui/btn_start_pressed.png` | kuva | menus/main_menu.py, menus/mission_prepare_menu.py, menus/prepare_menu.py |
| `assets/ui/btn_workshop_hover.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_workshop_idle.png` | kuva | menus/town_hub.py |
| `assets/ui/btn_workshop_pressed.png` | kuva | menus/town_hub.py |
| `assets/ui/esc.png` | kuva | game_manager.py |
| `assets/ui/inventory/panel_bg.png` | kuva | units/commander.py |
| `assets/ui/inventory/slot_frame.png` | kuva | units/commander.py |

## assets/ui player/ (2 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/ui player/grid_9_11.png` | kuva | units/commander.py |
| `assets/ui player/inventory_main.png` | kuva | units/commander.py |

## assets/videos/ (1 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/videos/mainmenu/main.mp4` | video | menus/main_menu.py |

## assets/voices/ (15 kpl)

| Tiedosto | Tyyppi | Käytetään tiedostossa |
|---|---|---|
| `assets/voices/human/marda/annoyed.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/arrogant.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/casual.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/laughing.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/pissed.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/rude.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/shouting.wav` | ääni | sound_manager.py |
| `assets/voices/human/marda/thinking.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/death.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/enrage.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/hurt.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/intro.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/spit.wav` | ääni | sound_manager.py |
| `assets/voices/rat_king/summon.wav` | ääni | sound_manager.py |
| `assets/voices/vortex/MnemonicDevourer/laughing.wav` | ääni | sound_manager.py |

## Dynaamiset polut

Nämä polut rakennetaan koodissa muuttujista (esim. framet 1..N),
joten tarkkaa tiedostolistaa ei voi päätellä automaattisesti.
Katso viittaava koodi nähdäksesi mitä nimiä odotetaan:

- `assets/crafting/swamp/nightcap` — crafting/swamp/nightcap_fungus.py
- `assets/crafting/swamp/scrap` — crafting/swamp/scrap_pile.py
- `assets/crafting/swamp/swamp_tree` — crafting/swamp/swamp_tree.py
- `assets/crafting/swamp/void_iron` — crafting/swamp/void_iron_node.py
- `assets/gear/books/book_{i}.wav` — sound_manager.py
- `assets/gear/bows/bow_{i}.wav` — sound_manager.py
- `assets/gear/crossbows/crossbow_{i}.wav` — sound_manager.py
- `assets/gear/staves/staff_{i}.wav` — sound_manager.py
- `assets/gear/{folder}/{w_type}_{i}.wav` — sound_manager.py
- `assets/portraits/bards` — npc/bard_npc.py
- `assets/portraits/commander` — npc/commander_npc.py
- `assets/portraits/dwarf_league_manager` — npc/dwarf_league_manager.py
- `assets/portraits/goblin` — npc/gambler_npc.py
- `assets/portraits/goblin/{emotion}.png` — npc/griznak_quest_giver.py
- `assets/portraits/hamo` — npc/hamo_npc.py
- `assets/portraits/mardashant` — npc/marda_shant_npc.py
- `assets/portraits/mortarch` — npc/grand_mortarch.py
- `assets/portraits/vortex/MnemonicDevourer` — npc/mnemonic_devourer_npc.py
- `assets/portraits/vortex_mentor` — npc/vortex_mentor.py
- `assets/portraits/{self.npc_id}/{emotion}.png` — npc/base_npc.py
- `assets/portraits/{self.school_key}` — npc/school_keeper.py
- `assets/races/animals` — units/farm_animals.py
- `assets/races/animals/chicken_{act}.png` — systems/asset_studio.py
- `assets/races/animals/cow_1_{act}.png` — systems/asset_studio.py
- `assets/races/cave/broodmother/broodmother` — units/cave_spider.py
- `assets/races/dwarf/dwarf` — units/dwarf.py
- `assets/races/dwarf/dwarf_{act}_1.png` — systems/asset_studio.py
- `assets/races/elf` — units/elf_bard.py
- `assets/races/elf/elf_{act}_1.png` — systems/asset_studio.py
- `assets/races/forest/troll/troll` — units/troll.py
- `assets/races/forest/troll/troll_{act}_1.png` — systems/asset_studio.py
- `assets/races/gnome/gnome` — units/gnome.py
- `assets/races/gnome/gnome_{act}_1.png` — systems/asset_studio.py
- `assets/races/goblin/goblin` — units/goblin.py
- `assets/races/goblin/goblin_{act}_1.png` — systems/asset_studio.py
- `assets/races/human/human` — units/human.py
- `assets/races/human/human_{act}_1.png` — systems/asset_studio.py
- `assets/races/human/mardashant` — units/marda_shant.py
- `assets/races/orc/orc` — units/orc.py
- `assets/races/orc/orc_{act}_1.png` — systems/asset_studio.py
- `assets/races/rat/giant_rat_{act}.png` — systems/asset_studio.py
- `assets/races/rat/rat_king_{act}.png` — systems/asset_studio.py
- `assets/races/swamp/frog/attack_{i}.wav` — sound_manager.py
- `assets/races/swamp/frog/attack{i}.wav` — sound_manager.py
- `assets/races/swamp/frog/frog` — units/giant_frog.py
- `assets/races/swamp/frog/hurt_{i}.wav` — sound_manager.py
- `assets/races/swamp/frog/hurt{i}.wav` — sound_manager.py
- `assets/races/swamp/frog/jump_{i}.wav` — sound_manager.py
- `assets/races/swamp/frog/jump{i}.wav` — sound_manager.py
- `assets/races/swamp/frog_smith/smith` — units/frog_smith.py
- `assets/races/swamp/leech/attack_{i}.wav` — sound_manager.py
- `assets/races/swamp/leech/attack{i}.wav` — sound_manager.py
- `assets/races/swamp/leech/hurt_{i}.wav` — sound_manager.py
- `assets/races/swamp/leech/hurt{i}.wav` — sound_manager.py
- `assets/races/swamp/leech/leech` — units/bog_leech.py
- `assets/races/tortle/tortle` — units/tortle.py
- `assets/races/tortle/tortle_{act}_1.png` — systems/asset_studio.py
- `assets/races/undead/skeleton/skeleton` — units/undead_skeleton.py
- `assets/races/undead/skeleton/skeleton_{act}.png` — systems/asset_studio.py
- `assets/races/undead/skeleton_archer/skeleton_archer` — units/undead_skeleton_archer.py
- `assets/races/undead/zombie/zombie` — units/undead_zombie.py
- `assets/races/undead/zombie/zombie_{act}.png` — systems/asset_studio.py
- `assets/races/vortex/Mnemonicdevourer` — units/mnemonic_devourer.py
- `assets/races/werewolf/werewolf` — units/werewolf.py
- `assets/races/werewolf/werewolf_{act}_1.png` — systems/asset_studio.py
- `assets/sfx/bard/bard_song_{i}.wav` — sound_manager.py
- `assets/sfx/nature/grass_moving_loop_{i}.wav` — sound_manager.py
- `assets/sfx/nature/tree_loop_windy_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/angry_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/belching_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/booing_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/cheer_competition_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/cheering_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/drink_loop_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/eat_loop_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/laugh_loop_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/loop_clapping_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/loop_snore_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/reaction_{i}.wav` — sound_manager.py
- `assets/sfx/sounds/sneeze_{i}.wav` — sound_manager.py
- `assets/sfx/talking/talking_loop_{i}.wav` — sound_manager.py
- `assets/tiles/barracks/bunk_q{quality}.png` — citys/mucford/barracks_interior_arena.py
- `assets/tiles/farm/crops/{slug}_stage_{stage}.png` — citys/mucford/farming_content.py
- `assets/tiles/gambling/` — minigames/crown_knives.py, sound_manager.py
- `assets/tiles/gamling/` — minigames/crown_knives.py, sound_manager.py
- `assets/voices/dwarf_league_manager` — npc/dwarf_league_manager.py
- `assets/voices/goblin/hamo` — npc/hamo_npc.py
- `assets/voices/human/marda` — npc/marda_shant_npc.py
- `assets/voices/mortarch` — npc/grand_mortarch.py
- `assets/voices/vortex/MnemonicDevourer` — npc/mnemonic_devourer_npc.py
