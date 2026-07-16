# progression/stat_curve.py
"""Statien kasvukäyrä (pelaajan linjaus, siistitty kaavaksi).

Tavoite: kymmeniä lvl 5, ~50-80 lvl 10, ~250 lvl 15, 500-600 lvl 20,
1000+ lvl 30. Tasot antavat KYKYJÄ (skill pointit), mutta statit tulevat
pääosin VARUSTEISTA - tämä käyrä on kokonaisbudjetti jota vasten varusteet,
koulutus ja viholliset mitoitetaan. Skill tree antaa PROSENTTEJA päälle.

Kaava: potenssikäyrä  stat_target(L) = 8 + 0.15 * L^2.7
  L5 ~ 20   L10 ~ 83   L15 ~ 243   L20 ~ 505   L25 ~ 900   L30 ~ 1470
Sileä (ei porrashyppyjä), helppo virittää kahdesta luvusta (kerroin,
eksponentti)."""

BASE = 8.0
COEF = 0.15
POWER = 2.7


def stat_target(level):
    """Hahmon kokonaisstatin tavoite tasolla (kaikista lähteistä yhteensä)."""
    lvl = max(1, int(level))
    return max(5, int(BASE + COEF * (lvl ** POWER)))


def gear_stat_budget(level):
    """Varusteiden osuus tavoitteesta (~70% - statit tulevat gearista)."""
    return max(3, int(stat_target(level) * 0.70))


def daily_training_gain(level, tier_mult=1.0):
    """Koulutuspäivän statihyöty: ~3% tason tavoitteesta, koulutustason
    kerroin päälle. Skaalautuu automaattisesti käyrän mukana."""
    return max(1, int(stat_target(level) * 0.03 * float(tier_mult)))
