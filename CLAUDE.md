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

- **Kaivosluola** (mine_cave_*.py) — kaivostien perältä (E suuaukolla, tie
  raivattava ensin). Pimeys + soihtuvalo pelaajan ympärillä, 8 rautaa,
  4 hiiltä, 2 rubiinisuonta, vahvistetut epäkuolleet leashilla (heräävät
  vasta pelaajan lähellä). Taontaketju: malmi+hiili → sulatto → Iron Bar →
  sepän Iron-sarja (BLUEPRINTS loot_data.py).
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
