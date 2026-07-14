# world_clock.py
"""
Maailmankello, kalenteri ja sää.

- Vuosi 3 A.V. (After the Vortex) — repeämä aukesi 3 vuotta sitten (docs/LORE.md).
- Vuodessa 4 vuodenaikaa x 28 päivää.
- Yksi pelipäivä kestää ~15 min reaaliaikaa (60 fps).
- Sää: clear / wind / rain / storm, vaihtuu muutaman pelitunnin välein.

Käyttö:
    clock = WorldClock()
    clock.update()                    # joka frame (ulkotiloissa)
    clock.draw_overlays(screen)       # yö-tummennnus + sääefektit
    clock.get_date_string()           # "Day 5 of Thaw, Year 3 A.V."
"""
import math
import random
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT

SEASONS = ["Thaw", "Sun", "Harvest", "Frost"]
DAYS_PER_SEASON = 28
DAYS_PER_YEAR = DAYS_PER_SEASON * len(SEASONS)

# 1 pelipäivä = 15 min reaaliaikaa -> 1440 pelimin / (15*60*60) framea
MINUTES_PER_FRAME = 1440.0 / (15 * 60 * 60)

WEATHER_TYPES = ["clear", "cloudy", "wind", "rain", "storm"]
# Painot: selkeä yleisin, myrsky harvinainen (pelitesti 14: + pilvinen)
WEATHER_WEIGHTS = [42, 16, 18, 19, 5]


class WorldClock:
    def __init__(self):
        # Aloitus: Vuosi 3 A.V., Thaw'n 1. päivä, aamu klo 8
        self.year = 3
        self.day = 1  # 1..DAYS_PER_YEAR (kokonaispäivä vuoden sisällä)
        self.minutes = 8 * 60.0

        # Sää
        self.weather = "clear"
        self.weather_timer = self._roll_weather_duration()
        self.wind_dir = 1  # 1 = oikealle, -1 = vasemmalle

        # Efektien tila
        self._rain_drops = []
        self._lightning_flash = 0
        self._thunder_delay = 0
        self._overlay = None  # yö-tummennuksen jaettu pinta
        self._clouds = None   # pilvisen sään ajelehtivat pilvivarjot
        # Taivaan elämä: linnut päivällä, lepakot yöllä (ruutuavaruudessa)
        self._sky_life = []
        self._next_flock = 240

        # Ambient-luupit (sade/tuuli). Kanavat pidetään tallessa jotta
        # luuppi voidaan feidata pois sään vaihtuessa.
        self._ambient_channels = []
        self._ambient_weather = None  # mille säälle luupit soivat nyt

    # =========================================================
    # AIKA
    # =========================================================
    def update(self):
        self.minutes += MINUTES_PER_FRAME
        if self.minutes >= 1440.0:
            self.minutes -= 1440.0
            self.advance_day()

        # Sään eteneminen
        self.weather_timer -= 1
        if self.weather_timer <= 0:
            self._change_weather()

        if self._lightning_flash > 0:
            self._lightning_flash -= 1
        if self._thunder_delay > 0:
            self._thunder_delay -= 1
            if self._thunder_delay == 0:
                try:
                    from sound_manager import sound_system
                    # BUGIKORJAUS: ääniavaimet ovat thunder_1..thunder_4
                    sound_system.play_sound(random.choice(
                        ["thunder_1", "thunder_2", "thunder_3", "thunder_4"]))
                except Exception:
                    pass

        # Myrskyssä satunnaisia salamoita
        if self.weather == "storm" and random.random() < 0.002:
            self._lightning_flash = 6
            self._thunder_delay = random.randint(20, 60)

        # Ambient-luupit seuraavat säätä (myös latauksen/aloituksen jälkeen)
        if self._ambient_weather != self.weather:
            self._update_ambient_loops()

    def advance_day(self):
        self.day += 1
        if self.day > DAYS_PER_YEAR:
            self.day = 1
            self.year += 1

    @property
    def hour(self):
        return int(self.minutes // 60)

    @property
    def minute(self):
        return int(self.minutes % 60)

    @property
    def season(self):
        return SEASONS[(self.day - 1) // DAYS_PER_SEASON]

    @property
    def day_of_season(self):
        return (self.day - 1) % DAYS_PER_SEASON + 1

    @property
    def is_night(self):
        return self.hour >= 22 or self.hour < 6

    def get_date_string(self):
        return f"Day {self.day_of_season} of {self.season}, Year {self.year} A.V."

    def get_time_string(self):
        return f"{self.hour:02d}:{self.minute:02d}"

    # =========================================================
    # SÄÄ
    # =========================================================
    def _roll_weather_duration(self):
        # 2-5 pelituntia frameina
        game_hours = random.uniform(2.0, 5.0)
        return int(game_hours * 60.0 / MINUTES_PER_FRAME)

    def _change_weather(self):
        old = self.weather
        # Ei kahta myrskyä peräkkäin
        weights = list(WEATHER_WEIGHTS)
        if old == "storm":
            weights[WEATHER_TYPES.index("storm")] = 0
        self.weather = random.choices(WEATHER_TYPES, weights=weights)[0]
        self.weather_timer = self._roll_weather_duration()
        self.wind_dir = random.choice([-1, 1])

    def _update_ambient_loops(self):
        """Käynnistää/feidaa säätä vastaavat taustaluupit.
        Toimii hiljaa jos äänitiedostoja ei ole asennettu."""
        self._ambient_weather = self.weather
        try:
            from sound_manager import sound_system
        except Exception:
            return
        for ch in self._ambient_channels:
            try:
                ch.fadeout(1200)
            except Exception:
                pass
        self._ambient_channels = []
        loops = {
            "rain":  ["rain_medium", "wind_loop_gentle"],
            "storm": ["rain_medium", "wind_loop_normal"],
            "wind":  ["wind_loop_normal"],
            "clear": ["wind_loop_gentle"],
            "cloudy": ["wind_loop_gentle"],
        }.get(self.weather, [])
        for name in loops:
            try:
                ch = sound_system.play_sound(name, loops=-1)
                if ch:
                    self._ambient_channels.append(ch)
            except Exception:
                pass

    def stop_ambient(self):
        """Kutsu kun poistutaan ulkotiloista (sisätilat/valikot)."""
        for ch in self._ambient_channels:
            try:
                ch.fadeout(800)
            except Exception:
                pass
        self._ambient_channels = []
        self._ambient_weather = None

    # =========================================================
    # PIIRTO (yö + sää; kutsu kaiken maailman päälle, HUDin alle)
    # =========================================================
    def night_alpha(self):
        """0 (keskipäivä) .. 160 (keskiyö), pehmeät siirtymät."""
        h = self.minutes / 60.0
        # Etäisyys keskipäivästä (12) tunteina, 0..12
        dist = abs(((h - 12) + 24) % 24)
        if dist > 12:
            dist = 24 - dist
        # Päivä (dist < 6) = 0, yö (dist > 9) = max, välissä ramppi
        if dist <= 6.0:
            t = 0.0
        elif dist >= 9.0:
            t = 1.0
        else:
            t = (dist - 6.0) / 3.0
        return int(160 * t)

    def draw_overlays(self, screen):
        self._draw_weather(screen)
        self._draw_sky_life(screen)
        self._draw_night(screen)

    def _draw_night(self, screen):
        alpha = self.night_alpha()
        # Myrsky ja sade tummentavat päivääkin hieman
        if self.weather == "storm":
            alpha = max(alpha, 70)
        elif self.weather == "rain":
            alpha = max(alpha, 40)
        elif self.weather == "cloudy":
            alpha = max(alpha, 24)
        if alpha <= 0:
            return
        if self._overlay is None:
            self._overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._overlay.fill((10, 10, 40, alpha))
        screen.blit(self._overlay, (0, 0))

        # Salama valaisee koko ruudun
        if self._lightning_flash > 0:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 230, 90))
            screen.blit(flash, (0, 0))

    def _draw_weather(self, screen):
        if self.weather == "cloudy":
            self._draw_clouds(screen)
        if self.weather in ("rain", "storm"):
            self._update_and_draw_rain(screen)
        elif self.weather == "wind":
            # Tuuli näkyy lehtinä/pölynä jotka viilettävät ruudun poikki
            if random.random() < 0.3:
                self._rain_drops.append({
                    "x": -10 if self.wind_dir > 0 else SCREEN_WIDTH + 10,
                    "y": random.uniform(0, SCREEN_HEIGHT),
                    "vx": self.wind_dir * random.uniform(6, 12),
                    "vy": random.uniform(-1, 1),
                    "leaf": True,
                    "life": 300,
                })
            self._update_and_draw_rain(screen, wind_only=True)

    def _draw_clouds(self, screen):
        """Pilvinen päivä: suuria pehmeitä pilvivarjoja jotka ajelehtivat
        hitaasti ruudun poikki tuulen suuntaan."""
        if self._clouds is None:
            rng = random.Random(17)
            self._clouds = [{
                "x": rng.uniform(-400, SCREEN_WIDTH + 400),
                "y": rng.uniform(-120, SCREEN_HEIGHT - 120),
                "w": rng.randint(420, 900),
                "h": rng.randint(180, 320),
                "v": rng.uniform(0.25, 0.6),
                "a": rng.randint(26, 44),
            } for _ in range(5)]
        for c in self._clouds:
            c["x"] += c["v"] * self.wind_dir
            if self.wind_dir > 0 and c["x"] > SCREEN_WIDTH + 500:
                c["x"] = -c["w"] - 100
            elif self.wind_dir < 0 and c["x"] < -c["w"] - 500:
                c["x"] = SCREEN_WIDTH + 100
            shadow = pygame.Surface((c["w"], c["h"]), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (18, 20, 30, c["a"]),
                                shadow.get_rect())
            pygame.draw.ellipse(shadow, (18, 20, 30, c["a"] // 2),
                                (c["w"] * 0.15, -c["h"] * 0.2,
                                 c["w"] * 0.7, c["h"]))
            screen.blit(shadow, (int(c["x"]), int(c["y"])))

    def _draw_sky_life(self, screen):
        """Linnut lentävät taivaalla päivisin, lepakot lepattavat öisin.
        Piirretään ruutuavaruudessa maailman päälle (pelitesti 14)."""
        night = self.is_night
        bad_weather = self.weather in ("rain", "storm")
        self._next_flock -= 1
        if self._next_flock <= 0 and not bad_weather:
            self._next_flock = random.randint(500, 1100)
            going_right = random.random() < 0.5
            n = random.randint(2, 5) if not night else random.randint(1, 3)
            base_y = random.uniform(40, SCREEN_HEIGHT * 0.45)
            for i in range(n):
                self._sky_life.append({
                    "x": (-30 - i * 34) if going_right
                         else (SCREEN_WIDTH + 30 + i * 34),
                    "y": base_y + random.uniform(-30, 30),
                    "vx": (1 if going_right else -1) *
                          random.uniform(2.2, 3.2) * (1.4 if night else 1.0),
                    "phase": random.uniform(0, 6.28),
                    "bat": night,
                })
        alive = []
        t = pygame.time.get_ticks() * 0.02
        for b in self._sky_life:
            b["x"] += b["vx"]
            if b["bat"]:
                # Lepakot lepattavat epävakaasti
                b["y"] += math.sin(t * 1.7 + b["phase"]) * 2.6
            else:
                b["y"] += math.sin(t * 0.6 + b["phase"]) * 0.8
            if b["x"] < -60 or b["x"] > SCREEN_WIDTH + 60:
                continue
            x, y = int(b["x"]), int(b["y"])
            flap = math.sin(t * (2.2 if b["bat"] else 1.4) + b["phase"])
            wing = int(5 + flap * 4)
            col = (26, 22, 30) if b["bat"] else (50, 46, 42)
            # Siivet "^"-muotoina, lepakolla sahalaitaisemmat
            pygame.draw.line(screen, col, (x - 7, y - wing), (x, y), 2)
            pygame.draw.line(screen, col, (x + 7, y - wing), (x, y), 2)
            if b["bat"]:
                pygame.draw.line(screen, col, (x - 7, y - wing),
                                 (x - 11, y - wing + 4), 2)
                pygame.draw.line(screen, col, (x + 7, y - wing),
                                 (x + 11, y - wing + 4), 2)
            pygame.draw.circle(screen, col, (x, y), 2)
            alive.append(b)
        self._sky_life = alive

    def _update_and_draw_rain(self, screen, wind_only=False):
        # Uusia pisaroita
        if not wind_only:
            intensity = 14 if self.weather == "storm" else 6
            for _ in range(intensity):
                self._rain_drops.append({
                    "x": random.uniform(-100, SCREEN_WIDTH + 100),
                    "y": random.uniform(-40, -5),
                    "vx": self.wind_dir * (2.5 if self.weather == "storm" else 1.0),
                    "vy": random.uniform(16, 24),
                    "leaf": False,
                    "life": 120,
                })

        alive = []
        for d in self._rain_drops:
            d["x"] += d["vx"]
            d["y"] += d["vy"]
            d["life"] -= 1
            if d["life"] <= 0 or d["y"] > SCREEN_HEIGHT + 20:
                continue
            if d["leaf"]:
                # Kellertävä lehti / pölyhiukkanen
                d["y"] += math.sin(d["x"] * 0.02) * 1.5
                pygame.draw.circle(screen, (180, 170, 90),
                                   (int(d["x"]), int(d["y"])), 2)
            else:
                # Sadepisara: lyhyt viiva putoamissuuntaan
                end_x = d["x"] - d["vx"] * 1.5
                end_y = d["y"] - d["vy"] * 0.6
                pygame.draw.line(screen, (150, 170, 210),
                                 (int(d["x"]), int(d["y"])),
                                 (int(end_x), int(end_y)), 1)
            alive.append(d)
        self._rain_drops = alive

    def draw_hud(self, screen, font, x=None, y=16):
        """Pieni kello/päivä/sää-näyttö aurinko/kuu-ikonilla."""
        # BUGIKORJAUS (pelitesti 21): "cloudy" puuttui -> KeyError kaatoi
        # piirron. .get-fallback suojaa myös tulevilta säätyypeiltä.
        weather_names = {"clear": "Clear", "wind": "Windy",
                         "rain": "Rain", "storm": "STORM",
                         "cloudy": "Cloudy"}
        w_name = weather_names.get(self.weather,
                                   str(self.weather).capitalize())
        text = f"{self.get_time_string()}  {w_name}"
        date = self.get_date_string()

        w_col = (150, 180, 255) if self.weather == "storm" else (230, 225, 200)
        surf1 = font.render(text, True, w_col)
        surf2 = font.render(date, True, (180, 175, 150))
        w = max(surf1.get_width(), surf2.get_width()) + 52
        if x is None:
            x = SCREEN_WIDTH - w - 16

        panel = pygame.Surface((w, 52), pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 12, 18, 180), panel.get_rect(),
                         border_radius=10)
        pygame.draw.rect(panel, (168, 134, 78, 190), panel.get_rect(), 1,
                         border_radius=10)
        screen.blit(panel, (x, y))

        # Aurinko päivällä, kuunsirppi yöllä
        cx, cy = x + 22, y + 26
        if not self.is_night and 6 <= self.hour < 20:
            col = (255, 205, 90)
            pygame.draw.circle(screen, col, (cx, cy), 8)
            for i in range(8):
                a = i * math.pi / 4
                pygame.draw.line(screen, col,
                                 (cx + math.cos(a) * 10, cy + math.sin(a) * 10),
                                 (cx + math.cos(a) * 14, cy + math.sin(a) * 14),
                                 2)
        else:
            pygame.draw.circle(screen, (205, 215, 255), (cx, cy), 8)
            pygame.draw.circle(screen, (12, 12, 18), (cx + 4, cy - 3), 7)

        screen.blit(surf1, (x + 42, y + 6))
        screen.blit(surf2, (x + 42, y + 28))

    # =========================================================
    # SAVE / LOAD
    # =========================================================
    def to_dict(self):
        return {"year": self.year, "day": self.day, "minutes": self.minutes,
                "weather": self.weather}

    def from_dict(self, data):
        self.year = int(data.get("year", 3))
        self.day = int(data.get("day", 1))
        self.minutes = float(data.get("minutes", 8 * 60))
        self.weather = data.get("weather", "clear")
        if self.weather not in WEATHER_TYPES:
            self.weather = "clear"
        self.weather_timer = self._roll_weather_duration()
