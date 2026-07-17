# ai/undead_ai.py
"""Epäkuolleiden tekoäly - BaseAI:n päälle rakennettu (yksi AI-kehys).

AIEMMIN tämä oli täysin erillinen toteutus omalla chase/separation/
väistölogiikallaan, joka ohitti kaikki BaseAI:n parannukset (anti-kite,
kiertoliike, jumiutumisen purku, reitinhaku). Nyt epäkuolleet ajaa sama
kehys kuin kaikkia muitakin - vain "luonne" on eri:

- Epäkuolleet EIVÄT pakene matalilla HP:illa (no_retreat) - ne ovat
  tahdottomia ja painavat päälle kuolemaansa asti.
- Ne eivät syöksy (dash) - hidas vääjäämätön eteneminen on niiden
  identiteetti. Zombie-lauma joka blinkkaa ympäriinsä näyttäisi väärältä.
- Jousiluuranko käyttää BaseAI:n normaalia ranged-logiikkaa (WeakBow
  lataus + panic shot), joten se toimii kuten muutkin ampujat.
"""
from ai.base_ai import BaseAI


class UndeadAI(BaseAI):
    def __init__(self, unit):
        super().__init__(unit)
        # Tahdoton: ei koskaan vetäydy, vaikka HP olisi lopussa
        self.no_retreat = True
        # Epäkuolleet eivät syöksy - vääjäämätön marssi on niiden pelote
        # (BaseAI tarkistaa tämän lipun kaikissa perform_dash-kohdissaan)
        self.allow_dash = False
