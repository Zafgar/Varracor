# Varracor — projektin opas

Pygame-ce-pohjainen gladiaattori-tycoon/action-RPG. Pelaaja (Commander/Hero)
etenee areenatiereissä 0→5 kohti Abyssal Vortexia. Yksinpeli, 1920×1080
(pygame.SCALED skaalaa).

## Käynnistys ja testit

```bash
pip install -r requirements.txt   # pygame-ce
python main.py                    # normaali peli (aloituskulta 500)
python main.py --cheat            # cheat-tila: 100k kultaa, karttaeditori (F8), debug-näppäimet
python -m pytest tests/ -q        # 21+ testiä, ~2 min (kaupunkisimulaatio mukana)
python tools/asset_scan.py        # päivittää MISSING_ASSETS.md
```

Cheat-tilan kehitystyökalut pelin sisällä: **F8** karttaeditori,
**F10** Asset Studio (menus/asset_studio_menu.py + systems/asset_studio.py):
pudota kuvat/äänet asset_inbox/-kansioon, valitse asset-paikka + tiedosto →
ASSIGN kopioi ja nimeää oikeaan polkuun; HITBOX-välilehti tallentaa propien
törmäyslaatikot assets/hitbox_overrides.json:iin (Prop.__init__ soveltaa).

Headless-ajo (testit/simulaatiot): `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`.
Kuvat/äänet/musiikki EIVÄT ole repossa (tekijän koneella) — peli toimii ilman
niitä procedural-fallbackeilla. `MISSING_ASSETS.md` listaa polut joihin
tiedostot kuuluu pudottaa.

## Tärkeät dokumentit

- **docs/LORE.md** — maailmanraamattu (valtakunnat, tierit, kaupungit,
  resurssit, magiakoulut). Kanoninen lore-lähde.
- **lore/world_data.py** — sama koneluettavana; pelikoodi käyttää tätä
  (esim. LeagueEnginen tier-nimet). Pidä synkassa LORE.md:n kanssa.
- **BALANCE_NOTES.md** — asebalanssin menetelmä, muutokset ja säännöt
  (korkeampi tier voittaa saman luokan ~2/2; tierin sisällä 30–70 %).
- **MISSING_ASSETS.md** — generoitu lista puuttuvista asseteista.

## Arkkitehtuuri

- **main.py** — pelisilmukka + datavetoinen tilakone: uusi valikko lisätään
  MENU_FACTORIES/RECREATE_ALWAYS/CALL_ON_ENTER-tauluihin, EI if-ketjuun.
- **game_manager.py** — keskusolio: talous, joukkue, taistelu (update_match),
  dialogit (handle_dialogue_event, eventtipohjainen), pause-menu, HUD,
  grant_hero_xp (kaupunkityöt → Commander XP).
- **gladiator.py** — yksiköiden pohjaluokka (statsit, varusteet, combat,
  stamina, dash, charge-aseet). _nearby_obstacles = välimuistitettu
  törmäysesisuodatus (ÄLÄ iteroi kaikkia esteitä suoraan — perf).
- **ai/** — BaseAI (combat), VillagerAI (oikea työ + kynnysarvot jotka
  jättävät pelaajalle tekemistä; parikeskustelut), FarmAnimalAI (lehmät,
  kanat, munat, poikaset — populaatiokatto 12), BirdAI ym.
- **items/** — aseet tiereittäin: scrap (lvl 1) → weak (lvl 2) → rat/erikois
  → epic/vortex. Rekisteri: items/item_registry.py (create_item nimellä).
- **spells/**, **arenas/**, **maps/**, **npc/**, **quests/** — rekisterivetoisia.
- **save_manager.py** — JSON-tallennus: F5/F9, pause-menun SAVE, päävalikon
  LOAD, autosave taistelun jälkeen. Tallennukset saves/ (gitignored).
- **sound_manager.py** — master-volyymit (music/sfx), options tallentuu
  saves/options.json. Options-valikko: menus/options_menu.py.
- **citys/mucford/** — aloituskaupunki (villagerit, maatila, taverna, paja).
- **settings.py** — PLAYER_TEAM/ENEMY_TEAM-vakiot: käytä AINA näitä
  team_color-vertailuissa, ei kovakoodattuja värejä.

## Konventiot ja sudenkuopat

- Kommentit suomeksi, UI-tekstit englanniksi.
- Ei paljaita `except:` — vähintään `except Exception:`.
- Elämää simuloivat propit (lanta, munat) lisätään SEKÄ
  arena.props ETTÄ manager.all_units -ryhmään; poistettaessa molemmista.
- Props-update kutsutaan `p.update(None, manager)` — manager on TOINEN
  parametri (obstacles ensin).
- Uudet valikot perivät BaseMenu; tilasiirtymä = next_state-attribuutti.
- Balanssimuutokset: aja duel-matriisi (tests/conftest.py run_duel-apuri),
  katso BALANCE_NOTES.md.
- Kaupunkisimulaation voi ajaa headless: ks. tests/test_city.py.

## Kaupungin elävät järjestelmät (Muckford)

- **world_clock.py** — vuorokausi, kalenteri (Vuosi 3 A.V., 4 vuodenaikaa x
  28 pv), sää (clear/wind/rain/storm + salamat). Etenee kaupungissa,
  tallentuu saveen. Yö-tummennus + sade piirretään draw_overlays():lla.
- **Emännän velka** — intro: Marda vaatii 25 kultaa öistä; ovi-intercept
  jos ei ole puhuttu; maksu dialogista kun rahat riittävät (+3 rep).
  manager.innkeeper_debt, chat-efektit set_innkeeper_debt/pay_innkeeper_debt.
- **Markkinat** — MuckfordStall → "market"-tila (menus/market_menu.py).
  Hinnat lore/world_data.py MARKET_PRICES. Myy maito/munat/puu/romu/lanta,
  osta ämpäri yms.
- **Market-alue** — 5 nimettyä liikettä kentällä (citys/mucford/
  market_data.py + market_stalls.py), E kojulla → "district_shop"
  (menus/district_shop_menu.py). Hinnat korjataan PAIKKAKOHTAISELLA
  maineella (systems/faction_reputation.py: rep 0 → +15 %, 30 → listahinta,
  70+ → -20 %); jokainen ostos +1 rep sen liikkeen faktiolle
  (manager.reputations, tallentuu saveen).
- **Rat-raidit** — Rat King lähettää parvia ~2-3 pv välein (klo 9-20) kunnes
  quest hunt_01 on suoritettu. 3 vartijaa puolustaa; rotat perääntyvät 60 s
  jälkeen elleivät kuole. Pelaajan tapot → +5 rep, kultaa, XP:tä. Ilman
  pelaajaa rotat usein ehtivät paeta saaliineen (motivoi auttamaan).

- **Kaivostie** (citys/mucford/mine_road_*.py) — velan maksu Mardalle antaa
  avaimen (manager.mine_key_owned); portti kaupungin itäreunalla. Epäkuolleet
  saartavat tien ja malmit (IronOre-nodet) respawnaavat päivittäin. Louhinta
  vaatii hakun (myydään markkinoilla). HUOM: GameplayScreen-pohjaisilla
  kartoilla add_material menee round_rewardsiin - kaivostie tyhjentää sen
  reppuun joka frame.
- **Talouslore**: lore/world_data.py ECONOMY (valuutat SP/GP/PL/HC 100x-
  kertoimin, elinkustannukset, alueviennit, sponsorit/palkkiot/Oath of Debt).

- **Barracksin sisätila** (citys/mucford/barracks_interior_*.py, tila
  "barracks_interior") — E barracksin ovella kaupungissa. Gladiaattorit
  oleilevat sisällä (kevyt POI-wander), juttelu (RosterNPC-dialogi) antaa
  +8 moraalia kerran/pv, punkassa nukkuminen aamuun palauttaa tiimin.
  Tasot 1-3 (BUNKS_PER_LEVEL 6/8/10) rajaavat tiimikoon (Commander vie
  punkan; game_manager.has_free_bunk estää palkkauksen). Kehitys
  suunnitelmataululta (UPGRADE_COSTS: kultaa + Swamp Wood/Stone/Iron Bar).
  Moraali (gladiator.morale 0-100, neutraali 50) kertoo vahinkoa 0.9-1.1x;
  voitto +4, tappio -6; tallentuu saveen (barracks_level + morale).
- **Näyttöasetukset** (systems/display_settings.py) — windowed/borderless/
  fullscreen + resoluutio (AUTO tunnistaa työpöydän); looginen renderöinti
  aina 1920x1080 SCALED. Options-valikon DISPLAY-osio; tallentuu
  saves/options.json "display"-avaimeen, sovelletaan käynnistyksessä.
- **Arena Hall & Town Hall** (citys/mucford/city_interiors.py, tilat
  "arena_hall"/"town_hall") — Shanty Yardin portti vie käveltävään halliin:
  liigatiski (LEAGUE), Odds-Maker Vintin vedonlyönti (panos omaan seuraavaan
  liigamatsiin, x2; manager.active_bet, ratkeaa end_matchissa, tallentuu),
  vartijat ja RIVAL_GLADIATORS-edustajat loungessa (open_rival_dialogue).
  Town Hall: kirjuri (sponsors) + mainetaulu (reputation). Sisätiloista
  poistuttaessa pelaajan kaupunkisijainti palautetaan (_city_return_pos -
  rect jaetaan tilojen välillä!). Kello piirretään sisätiloissa
  draw_ui_overlayssa; HUD häivytetään kun hahmo jää sen taakse.
- **Save-slotit**: päävalikon LOAD avaa slottipaneelin (lataus + X-poisto
  kahdella klikillä, delete_slot); sama poisto pause-paneelissa.
- **NPC-sadonkorjuu**: CropPlotin being_worked_on-varaus raukeaa TTL:llä
  (~25 s) ja VillagerAI:n stuck-käsittely vapauttaa työkohteen - ilman
  näitä pellot lukkiutuvat pysyvästi eikä kukaan korjaa satoa.

- **Mudwater Pond + kalastus** — koodipiirretty vesi (assets/tiles/water.py:
  WaterBody = välimuistitettu pohja + animoidut aallot/kimallus/väreet/
  ajopilkut; carve_water/carve_pond upottaa areenaan, rebuild_water_blockers
  laskee esteet laituriaukkoineen; editorin Water-kategoria maalaa vesiä
  SHIFT+raahauksella). Kalastus systems/fishing.py: WAITING→BITE→REELING
  (väsytysminipeli: E pohjassa kelaa, kireys 100 = siima poikki, kala
  tempoo tierinsä mukaan), 10 kalaa tiereittäin + aarresivusaaliit
  (TREASURES, mm. Abyssal Droplet), vavat T1-5 tasovaatimuksin,
  kalareseptit keittiössä. E laiturilla = heitto/tartutus, liike keskeyttää.
- **Commander Paths** (systems/commander_progression.py) — jokainen
  tekeminen on OMA kykypuunsa omalla XP:llä: combat (tapot/voitot),
  Vortex-magia (loitsut; AVAA spell slotit 1-3 ja tierit I-IV
  tasovaatimusten takaa - Vortex on ehkä ainoa magia jonka Commander
  oppii), fishing (saaliit), mining (malmi-iskut), smithing (taonta;
  Sparing Hammer säästää materiaaleja), forestry (hakkuut), building
  (lukittu, House Building tulossa). Tasot 1-30, milestone-perkit
  vaikuttavat sankariin (_progression_effects, apply_to_hero kutsutaan
  XP:stä ja latauksessa). Seuranta: PATHS-nappi Manager-valikossa
  (menus/paths_menu.py). HUOM: farming/cooking EIVÄT ole Commander-
  polkuja. Aseiden level_required koskee Commanderia kuten muitakin
  (gladiator.can_equip_item_to_slot; cheat-tila ohittaa).
- **Kaivosluola** (mine_cave_*.py) — kaivostien perältä (E suuaukolla, tie
  raivattava ensin). Pimeys + soihtuvalo pelaajan ympärillä, 8 rautaa,
  4 hiiltä, 2 rubiinisuonta, vahvistetut epäkuolleet leashilla (heräävät
  vasta pelaajan lähellä). Taontaketju: malmi+hiili → sulatto → Iron Bar →
  sepän Iron-sarja (BLUEPRINTS loot_data.py).
- **Retkikunta** (systems/expedition.py) — COMMAND-puun Warband-haara
  (cap 2-10); ryhmä kootaan barracksin sotapöydältä (muster), kulkee
  mukana retkikartoilla (kaivostie/-luola, rift-alueet:
  enable_expedition + expedition_units GameplayScreenissä). Kenttä-
  komennot [T] + numero: FOLLOW ME/FREE FIGHT aina, KITE/DEFEND puusta
  (tactic_kite/defend); valikon aikana numerot EIVÄT casta hotbaria.
  Kaatunut retkeläinen pois kentältä + vammat (conditions); sairaana
  viety voi kuolla. Commanderin kaatuminen retkellä (rescue_on_death-
  lippu) -> commander_down: herää seuraavana aamuna Sunk Caskista
  (Marda perii 25 SP) tai barracksista jos tiimi pystyssä (toveri
  kertoo); pending_rescue-dialogi kohteen on_enterissä. Kokoonpano +
  käsky tallentuvat saveen.
- **HP-regen** (gladiator.py): kaikki yksiköt palautuvat passiivisesti
  (~0.8 %/s + unit.hp_regen); take_damage asettaa hp_regen_delay=300
  (5 s tauko osumasta).
- **Kaupungin vuorokausirytmi** (_city_phase muckford_city_menu.py):
  toriaikaan 9-17 simulaatio ohjaa väen kojuille (market_spots,
  _pick_spot hylkää ruuhkaiset paikat - EI rykelmiä), illalla oleskelua,
  yöllä 22-07 koteihin (pysyvä sim_home) nukkumaan. VillagerAI ei ota
  töitä yöllä. HUOM: _update_simulation oli luokassa KAHDESTI -
  duplikaatti poistettu, muokkaa vain jäljellä olevaa.
- **Muckford Warrens = reitti Rat Kingille** (citys/mucford/
  muckford_warrens.py) — PÄÄreitti bossille: E torin takana olevalla
  viemäriluukulla (CitySewerHatch) → 3600×2400 viemärikartta. Griznak
  aloittaa/seuraa (world_events), Hamo/Rinna antavat vaiheet. Linja
  (warrens_state.quest_stage 0-7): jäljitä 4 violettijälkeä → 4
  ruokavarastoa → tuhoa 4 jäteluolaa → pelasta 3 ratcatcheria → **vedä
  2 sulkuvipua (SluiceLever → +2 Rusted Sluice Cog/vipu) + tao Cistern
  Gate Crank sepällä (loot_data BLUEPRINTS, type key_item → craft_item
  reppuun) + kammea Royal Cistern -portti auki** → Rat King herää
  eeppisellä introdialogilla → kaato → hunt_01 valmis + raidit loppuvat.
  PELITESTI 25: alue rakennettu uusiksi OIKEILLA rottayksiköillä (ei enää
  koodipiirretty units/muckford_warrens_monsters.py — POISTETTU): lattia
  laattapohjainen (_load_floor_tiles lataa sewer_floors/floors kuten
  maps.rat_sewer, fallback kivilaatta); populaatio GiantRat/RatRider/
  BruteRat (units/rat.py; BruteRat = 420 HP Giant Rat tuplakokoon);
  boss = OIKEA units.rat_king.RatKing (sylky/summon/rage/superhyppy).
  Rat Kingin summonit menevät enemy_teamiin → _process_boss imee ne
  self.monstersiin; on_exit siivoaa enemy_team/all_units. Retkikunta
  mukaan (enable_expedition/expedition_units). Portin lippu: warrens_state
  gate_cranked/boss_unlocked; set_boss_gate riippuu näistä.
- **Rat King -areenajahti** (Griznakin urakkalista → start_boss_hunt →
  missions/boss_registry → maps/rat_sewer): VAIHTOEHTOINEN areenaversio.
  Boss valtaistuimella idässä, pelaajat viemärin suulla; is_boss →
  bossipalkki; sylky = vfx create_acid_glob (vihreä kaari).
  _position_units sietää spawn_points-LISTAN; mission lavastaa itse
  (manager.mission_handles_positioning); intro-dialogi
  (MissionLogic._begin_boss_intro).
- **Griznakin vankkurit** (systems/griznak_caravan.py) — Griznak on AINA
  kaupungissa vankkureineen (Muckford: torin laita, Rattlebridge:
  länsiportti; lisää tier-kaupunkeja samalla spawn()-helperillä).
  E → oikea ChatMenu-dialogi (open_chat asettaa return_staten +
  quests_return_staten); "[Show me the contracts]" = goto:quests
  (ChatMenu-efekti) ja urakkalistan sulku palaa kaupunkiin.
  world_events(manager) kokoaa kuulutukset (rottaparvet next_raid_day,
  rift-alueet, bossikontrahdit) → open_dialogue-kontekstin
  "world_events" → Griznakin "What's stirring out there?" -node.
- **Valuutta**: sisäinen yksikkö = SP (hopea). format_money muotoilee
  100x-portain (SP/GP/PL/HC). Kaupungin M-näppäin avaa kartan.
- **Potionit**: Potion.cast() parantaa ja kuluttaa pullon (usable-slotit
  näppäimet 4/7/8 + klikkaus).

## Pelin visio (tiivistetysti — koko kuva docs/LORE.md)

Hero menetti muistinsa Mnemonic Devourerille matkalla Vortexiin; alkaa
Muckfordista (Tier 0) tyhjästä. Areenaprogessio + wave-taistelu-eventit +
boss-eventit + yksilötehtävät (kaivos, keräily) + kaupunkielämä (NPC:t,
maatila, questit) → reputation avaa tierit, rodut, rekrytoinnit. Loppupeli:
Golden League ja Vortexin ydin.
