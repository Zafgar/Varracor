# Asebalanssi — muistiinpanot

Balansointi tehty simuloimalla: identtiset Human-yksiköt, ase A vs ase B,
jokainen pari molemmilta aloituspuolilta, tyhjä kenttä (ei esteitä).
Simulaattori: `tests/conftest.py` → `run_duel`.

## Tavoitteet (pelin designin mukaan)

1. **Tier-progressio**: korkeamman tierin ase voittaa saman luokan
   matalamman tierin aseen — parempiin aseisiin pääsy on areenapalkinto.
2. **Tierin sisällä** saman kategorian (melee/ranged) aseet ovat
   karkeasti tasavertaisia, eri pelityyleillä.

## Tehdyt muutokset

### Bugikorjaukset (eivät balanssia, mutta estivät sen)
- **WeakBow**: puuttui `weapon_group="bow"` → AI ei osannut käyttää
  latausmekaniikkaa lainkaan (hävisi jopa ScrapBow'lle)
- **WeakSpear**: charge-kentät puuttuivat `__init__`istä vaikka
  syöksymekaniikka oli toteutettu → ei koskaan aktivoitunut
- Varsijousien AI-latauslogiikka korjattu (ks. commit "Fix combat and AI bugs")

### Numerot

| Ase | Ennen | Jälkeen | Syy |
|---|---|---|---|
| ScrapBow | dmg 8, rng 300 | dmg 6, rng 270 | dominoi tieriä 100 % voitoilla |
| WeakBow | dmg 6, rng 280, spd -0.1 | dmg 9, rng 300, spd 0 | oli joka statiltaan huonompi kuin scrap-versio |
| ScrapCrossbow | dmg 14, lataus 90f | dmg 11, lataus 70f | tier-järjestys nurin |
| WeakCrossbow | dmg 9, lataus 80f | dmg 15, lataus 55f | tier-järjestys nurin + liian hidas käyttää |
| ScrapSpear | dmg 4 | dmg 6 | tierin pohja |
| WeakSpear | dmg 7 | dmg 11 | hävisi kaikille charge-korjauksen jälkeenkin |
| ScrapDagger | dmg 3 | dmg 5 | tierin pohja |
| WeakDagger | dmg 5 | dmg 7 | tierin pohja |
| ScrapBook | dmg 5 | dmg 6 | tierin pohja |
| WeakBook | dmg 7, rng 260 | dmg 6, rng 245 | dominoi tieriä 100 % voitoilla |
| ScrapStaff | dmg 6 | dmg 5 | 87-100 % voitoista |
| WeakStaff | dmg 9 | dmg 8 | 87 % voitoista |
| WeakAxe | dmg 9, rng 34 | dmg 11, rng 38 | tierin pohja |

## Tulokset muutosten jälkeen

- **Tier-etu: 17/18** — weak voittaa scrapin samassa aseluokassa
  (keihäs 1/2, syöksyn satunnaisuus).
- **Melee tierin sisällä**: 19–50 % voittohaarukka (oli 12–62 %).
- **Ranged voittaa avokentällä melee-aseet** lähes aina. Tämä on
  odotettua: simulaatiossa ei ole esteitä eikä tiimejä. Oikeissa
  areenoissa seinät katkaisevat näköyhteyden (LOS-tarkistus on jo
  koodissa) ja wave-taisteluissa meleet suojaavat ampujia.

## Jatkoa varten

- Aja matriisi uudelleen: muokkaa `tests/conftest.py`-apuria tai pyydä
  Claudea ajamaan balanssiraportti — muutosten vaikutuksen näkee heti.
- Kun uusia tierejä (rat/epic/vortex...) tulee lisää, sama sääntö:
  saman luokan ase seuraavassa tierissä voittaa edellisen ~2/2,
  tierin sisällä 30–70 % haarukka.
- Varsinainen ranged vs melee -balanssi kannattaa mitata oikeassa
  areenassa esteiden kanssa, ei tyhjällä kentällä.
- Stamina on tarkoituksella rajoittava resurssi: varsijousen lataus
  syö ~0.7/frame ja AI aloittaa latauksen vain kun stamina riittää
  koko lataukseen (`ai/base_ai.py`).
