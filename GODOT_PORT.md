# Varracor → Godot 4 -portti (top-down 3D)

Kaksi versiota elävät rinnakkain samassa repossa:

```
/            py-versio (pygame-ce)  = PELILOGIIKAN TOTUUSLÄHDE + testit
/godot       Godot 4 -versio (3D, top-down) = tuleva pääversio
/godot/data  JSON-data, EXPORTATTU py-versiosta (älä muokkaa käsin)
```

**Peilausperiaate:** kaikki pelidata (statikäyrä, loitsu- ja
varustekatalogit, skill-puut, muodot, koulutus) määritellään Pythonissa
ja exportataan `python tools/export_gamedata.py` -komennolla. Godot lukee
samat JSONit (`Catalogs`-autoload). Kaavat (esim. `stat_target`,
`scaled_damage`) on toteutettu molemmissa ja testit vahtivat että
py-arvot = exportatut arvot.

## Miksi 3D top-down
- GPU-renderöinti: hehkut/valot/partikkelit (Environment glow on jo
  päällä prototyypissä) ilman CPU-blittausta
- Syvyys + valaistus antavat ilmaista näyttävyyttä placeholdereillekin
- Kamera ylhäältä ~55° säilyttää py-version pelituntuman

## Lapsentaudit jotka Godot-versio korjaa (alusta asti oikein)

| # | PY-version valuvika | Godot-ratkaisu |
|---|---|---|
| 1 | `game_manager.py` on ~3000+ rivin jumalaolio (talous, questit, UI, VFX, save...) | Erilliset autoloadit: `GameState`, `EventBus` (signaalit), `Catalogs`, `QuestSystem`, `Economy` |
| 2 | Merkkijonopohjainen tilakone `main.py`:ssä (60+ tilaa dictissä) | Scene-vaihdot + yksi ohut `SceneRouter`; valikot ovat scenejä |
| 3 | UI pollaa hiirtä (`SpriteButton.update()` lukee `mouse.get_pressed`) → klikkivuodot (pause-bugi!) | Control-nodet + signaalit; modaalisuus ilmaiseksi |
| 4 | Data, logiikka ja piirto sekaisin unit-luokissa (`Gladiator` piirtää, laskee JA omistaa datan) | Resource (data) + Node-komponentit (logiikka) + View (mesh/anim) erikseen |
| 5 | Runtime-monkeypatch (muckford_opening patchaa menuluokkia importissa) | Kompositio ja signaalit; ei luokkien uudelleenkirjoitusta ajossa |
| 6 | Frame-pohjaiset ajastimet (60 fps kovakoodattu: `timer % 60 == 0`) | `delta`-pohjainen aika kaikkialle; fysiikka `_physics_process` |
| 7 | Kovakoodattu 1920x1080 kaikissa valikoissa | Viewport-stretch + ankkuroidut Controlit |
| 8 | Myöhäis-importit kiertämässä sykliriippuvuuksia (`from x import y` funktioiden sisällä sadoissa kohdissa) | Selkeä riippuvuusgraafi: data ← systeemit ← scenet |
| 9 | Save = käsin tehty dict-serialisointi | Versioidut Resource-savet + migraatiot |
| 10 | VFX CPU-blittauksella (glow-kehät pinnoille) | GPUParticles3D + emission-materiaalit + WorldEnvironment glow |

## Vaiheet (kohde: pelattava Godot-versio alusta loppuun)

- **Vaihe 0 – Perusta (TEHTY)**
  - Godot 4 -projekti `godot/`, top-down 3D -prototyyppi: areena,
    WASD+dash-pelaaja, seurauskamera, dummy-viholliset, glow-ympäristö
  - Data-putki: `tools/export_gamedata.py` → `godot/data/*.json` +
    `Catalogs`-autoload + py-testit jotka vahtivat peilin tuoreutta
- **Vaihe 0.5 – Kuori: ohjain, valikot, intro, audio (TEHTY)**
  - PS5 DualSense POHJANA: vasen tatti = liike (analoginen), Cross =
    dash/valinta (+ DualSense-tärinä dashissa), Options = pause, Circle =
    takaisin. Actionit rekisteröidään koodissa (input_setup.gd);
    näppäimistö toimii rinnalla.
  - UI-teema koodilla (ui_theme.gd): tumma paneeli + kultakorostus,
    selkeä fokustyyli ohjainnavigointiin. Ei asseteja.
  - Valikot scene-pohjaisina + Router-feidit: päävalikko (New Game/
    Continue/Options/Quit), optiot (Master/Music/SFX-väylät + fullscreen,
    säilyy user://settings.cfg), pause-overlay areenassa (MODAALINEN -
    ei klikkivuotoja).
  - Alkuintro: samat 10 narraatiokohtausta kuin py-versiossa, feidit +
    tunnelmapartikkelit per kohtaus, skip Crossilla.
  - Audio KOKONAAN syntetisoitu koodilla (audio_director.gd): pad-
    musiikki sointukierroilla per näkymä (menu/intro/arena) +
    SFX (click/confirm/back/whoosh/hit). Oikeat äänet vaihdetaan
    tilalle myöhemmin - rajapinta (Audio.sfx / Audio.play_music) pysyy.
- **Vaihe 0.75 – Commander pelattavaksi (TEHTY)**
  - MOLEMMAT ohjaustavat täysin rinnakkain: PS5 (vasen tatti liike,
    oikea tatti tähtäys, R2 lyönti, Square/Triangle/L1 loitsut) JA
    WASD+hiiri (hiiritähtäys raycastilla lattiatasoon, LMB lyönti,
    1/2/3 loitsut). Twin-stick: hahmo katsoo tähtäyssuuntaan.
  - Commander (player.gd): statit stat_target-käyrästä, HP/mana/stamina,
    dash staminakustannuksella, lähitaistelu (8 + STR*0.6), 3 loitsu-
    paikkaa katalogista (mana tier_mana-taulusta, vahinko
    scaled_damage-kaavasta, cooldown arkkityypin mukaan).
  - Loitsuprojektiiili (bolt.gd, väri vahinkotyypistä + valo + purske)
    ja AOE-nova (laajeneva rengas). Viholliset (enemy.gd): jahtaus,
    kontaktivahinko, osumavälähdys, kuolinpurske.
  - HUD (hud.gd): HP/Mana/Stamina-palkit + loitsupaikat cooldown-
    verhoineen ja molempien ohjaustapojen näppäinvihjeet.
  - Save/load samalla idealla kuin optiot: SaveGame-autoload
    (user://save.json, versioitu), pause-valikon SAVE GAME,
    päävalikon CONTINUE aktiivinen vain jos tallennus on olemassa.
- **Vaihe 1 – Ydinsimulaatio**
  - Yksikködata Resourceina; statit käyrästä + gearista + puu-%
  - Vahinko/parannus, statukset (Burn/Poison/Regen/Slow), kuolema
  - Cast time / interrupt / counter (peilaa spells/casting.py)
- **Vaihe 2 – Taisteluprototyyppi**
  - Loitsut katalogista: TieredBolt 3D:nä (GPUParticles-vana, glow-osumat)
  - Viholliset + yksinkertainen AI (hae kohde, liiku, lyö)
  - Muodonmuutokset (karhu ensin) 3D-placeholder-meshinä
- **Vaihe 3 – Systeemit**
  - Questit + journal (tracker siirrettävänä Control-panelina)
  - Koulut ja kaupat (spell+gear samasta datasta), koulutuskoulu
  - Save/load (Resource + versiointi)
- **Vaihe 4 – Maailma**
  - Muckford 3D top-down: katu, talot, NPC:t, kartta
  - Metsäpolku-opastus, warrens
- **Vaihe 5 – Pariteetti ja vaihto**
  - Pariteettilista py-testisarjaa vasten (914 testiä = speksi)
  - Kun pariteetti riittää: py-versio jää referenssiksi, kehitys jatkuu
    Godotissa

## Työsäännöt
1. **Dataa muutetaan vain py-puolella** → aja export → molemmat päivittyvät.
2. Uudet pelisäännöt suunnitellaan/testataan ensin py:ssä (nopea
   iteraatio + pytest), portataan sitten Godot-vaiheen mukana.
3. Godot-puolella EI kopioida py:n arkkitehtuuria — vain säännöt.
   Lapsentautilista yllä on tarkistuslista jokaiseen porttaus-PR:ään.
4. `godot/.godot/` (import-cache) ei kuulu gitiin.

## Avaaminen
Avaa `godot/`-kansio Godot 4.3+:ssa → F5. Prototyyppi tulostaa
konsoliin data-putken savutestin (stat_target(20), Arcane Dart dmg).
