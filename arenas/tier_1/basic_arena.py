import pygame
import random
import math
from settings import *
from arenas.base_arena import BaseArena, ArenaObstacle

class BasicArena(BaseArena):
    def __init__(self):
        super().__init__("Grand Colosseum")
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # Väripaletti
        self.floor_color = (194, 178, 128)
        self.sand_dark = (170, 155, 110)
        self.sand_light = (220, 205, 155)
        self.stone_dark = (55, 55, 60)
        self.stone_mid = (90, 90, 100)
        self.stone_light = (130, 130, 145)
        self.crowd_base = (95, 80, 80)

        # --- Layout ---
        self.ring_thick = max(52, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.05))
        self.inner_pad = self.ring_thick + max(10, int(min(SCREEN_WIDTH, SCREEN_HEIGHT) * 0.012))

        # Pelialue (spawnia varten)
        self.play_rect = pygame.Rect(
            self.inner_pad + 40,
            self.inner_pad + 60,
            SCREEN_WIDTH - (self.inner_pad + 40) * 2,
            SCREEN_HEIGHT - (self.inner_pad + 60) * 2,
        )

        # --- FAILSAFE BOUNDS ---
        # Ehdoton raja, jonka yli ei pääse.
        # Hieman tiukempi (margin 8) jotta ei näytä menevän kiven sisään.
        bounds_margin = 8
        self.bounds_rect = pygame.Rect(
            self.inner_pad + bounds_margin,
            self.inner_pad + bounds_margin,
            SCREEN_WIDTH - (self.inner_pad + bounds_margin) * 2,
            SCREEN_HEIGHT - (self.inner_pad + bounds_margin) * 2,
        )

        # --- SEINÄT (Collision) ---
        self.obstacles.empty()
        wall_thick = 100 

        # Yläreuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, -wall_thick,
            SCREEN_WIDTH + wall_thick * 2, self.inner_pad + wall_thick,
            "wall"
        ))
        # Alareuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, SCREEN_HEIGHT - self.inner_pad,
            SCREEN_WIDTH + wall_thick * 2, self.inner_pad + wall_thick,
            "wall"
        ))
        # Vasen reuna
        self.obstacles.add(ArenaObstacle(
            -wall_thick, 0,
            self.inner_pad + wall_thick, SCREEN_HEIGHT,
            "wall"
        ))
        # Oikea reuna
        self.obstacles.add(ArenaObstacle(
            SCREEN_WIDTH - self.inner_pad, 0,
            self.inner_pad + wall_thick, SCREEN_HEIGHT,
            "wall"
        ))

        # 4 Pylvästä
        pillar_size = max(56, int(min(self.play_rect.w, self.play_rect.h) * 0.09))
        px1 = self.play_rect.x + int(self.play_rect.w * 0.28)
        px2 = self.play_rect.x + int(self.play_rect.w * 0.72)
        py1 = self.play_rect.y + int(self.play_rect.h * 0.30)
        py2 = self.play_rect.y + int(self.play_rect.h * 0.70)

        cols = [(px1, py1), (px2, py1), (px1, py2), (px2, py2)]
        for x, y in cols:
            self.obstacles.add(ArenaObstacle(x - pillar_size // 2, y - pillar_size // 2, pillar_size, pillar_size, "wall"))

        # Cache pinnat
        self._bg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._fg_cache = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._build_static_background()
        self._build_static_foreground()

        # VFX
        self.dust = []
        for _ in range(42 if SCREEN_WIDTH >= 1600 else 32):
            self._spawn_dust(initial=True)

        self._heat_phase = 0.0
        self.heat = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self._bursts = []
        self._hit_puffs = []
        self._last_attack_cd = {}
        self._last_hp = {}

        self._dust_sprites = []
        for a in range(0, 136, 16):
            s = pygame.Surface((12, 7), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (210, 195, 145, a), (0, 0, 12, 7))
            self._dust_sprites.append(s)

    def enforce_bounds(self, all_units):
        """Kutsutaan GameManagerista loopin lopussa."""
        self._failsafe_keep_units_in_bounds(all_units)

    def _failsafe_keep_units_in_bounds(self, all_units):
        if not all_units: return
        br = self.bounds_rect
        for u in all_units:
            if not hasattr(u, "rect"): continue
            
            # Clamp rect
            before = u.rect.topleft
            u.rect.clamp_ip(br)
            
            # Jos rect muuttui (osui seinään), synkkaa float-koordinaatit
            if u.rect.topleft != before:
                if hasattr(u, "x"): u.x = float(u.rect.x)
                if hasattr(u, "y"): u.y = float(u.rect.y)
                if hasattr(u, "pos"):
                    try:
                        u.pos.x = float(u.rect.x)
                        u.pos.y = float(u.rect.y)
                    except Exception: pass
                
                # AI Reset jos juuttuu
                ai = getattr(u, "ai_controller", None)
                if ai and hasattr(ai, "escape_mode"):
                    ai.escape_mode = False

    def update(self, all_units):
        self._heat_phase += 0.02
        
        # Dust update
        for p in self.dust:
            p[0] += p[2]
            p[1] += p[3] + math.sin(p[0] * 0.028) * 0.16
            p[4] -= 1
        self.dust = [p for p in self.dust if p[4] > 0 and p[0] < SCREEN_WIDTH + 70]
        while len(self.dust) < (42 if SCREEN_WIDTH >= 1600 else 32):
            self._spawn_dust()

        # Bursts & Puffs
        self._bursts = [b for b in self._bursts if b[3] > 0]
        for b in self._bursts: b[2] += 1.35; b[3] -= 1
        
        self._hit_puffs = [h for h in self._hit_puffs if h[3] > 0]
        for h in self._hit_puffs: h[2] += 1.10; h[3] -= 1

        # Unit effects
        for u in all_units:
            uid = id(u)
            cd = float(getattr(u, "attack_cooldown", 0) or 0)
            if cd > float(self._last_attack_cd.get(uid, cd)) + 0.5:
                self._spawn_burst(*u.rect.center, big=False)
            self._last_attack_cd[uid] = cd

            hp = float(getattr(u, "current_hp", 0) or 0)
            if hp < float(self._last_hp.get(uid, hp)) - 0.1:
                self._spawn_hit_puff(*u.rect.center)
            self._last_hp[uid] = hp

        # AJETAAN MYÖS TÄSSÄ, MUTTA TÄRKEINTÄ ON GAME MANAGERIN KUTSU
        self._failsafe_keep_units_in_bounds(all_units)

    # --- DRAW METHODS (Samat kuin ennen) ---
    def _build_static_background(self):
        bg = self._bg_cache
        bg.fill((0,0,0,0))
        cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        max_r = int(math.hypot(cx, cy))
        for r in range(max_r, 0, -max(14, int(min(SCREEN_WIDTH,SCREEN_HEIGHT)*0.012))):
            p = r/max_r
            c = (
                int(self.sand_light[0]*(1-p) + self.sand_dark[0]*p),
                int(self.sand_light[1]*(1-p) + self.sand_dark[1]*p),
                int(self.sand_light[2]*(1-p) + self.sand_dark[2]*p)
            )
            pygame.draw.circle(bg, c, (cx,cy), r)
        
        # Ring
        rt = self.ring_thick
        ip = self.inner_pad
        col = self.stone_dark
        pygame.draw.rect(bg, col, (0,0,SCREEN_WIDTH,rt))
        pygame.draw.rect(bg, col, (0,SCREEN_HEIGHT-rt,SCREEN_WIDTH,rt))
        pygame.draw.rect(bg, col, (0,0,rt,SCREEN_HEIGHT))
        pygame.draw.rect(bg, col, (SCREEN_WIDTH-rt,0,rt,SCREEN_HEIGHT))
        
        # Edge
        ec = self.stone_mid
        ew = max(6, int(rt*0.12))
        pygame.draw.rect(bg, ec, (ip, ip, SCREEN_WIDTH-ip*2, ew))
        pygame.draw.rect(bg, ec, (ip, SCREEN_HEIGHT-ip-ew, SCREEN_WIDTH-ip*2, ew))
        pygame.draw.rect(bg, ec, (ip, ip, ew, SCREEN_HEIGHT-ip*2))
        pygame.draw.rect(bg, ec, (SCREEN_WIDTH-ip-ew, ip, ew, SCREEN_HEIGHT-ip*2))
        
        self._draw_stands(bg)

    def _draw_stands(self, surf):
        top_h = max(68, int(SCREEN_HEIGHT*0.06))
        pygame.draw.rect(surf, self.stone_mid, (0,0,SCREEN_WIDTH,top_h))
        pygame.draw.rect(surf, self.stone_mid, (0,SCREEN_HEIGHT-top_h,SCREEN_WIDTH,top_h))
        
    def _build_static_foreground(self):
        fg = self._fg_cache
        fg.fill((0,0,0,0))
        for obs in self.obstacles:
            if getattr(obs,"type","")=="wall" and obs.rect.w < 300:
                sh = pygame.Surface((obs.rect.w+34, obs.rect.h+34), pygame.SRCALPHA)
                pygame.draw.rect(sh, (0,0,0,78), (18,18,obs.rect.w,obs.rect.h), border_radius=12)
                fg.blit(sh, (obs.rect.x-10, obs.rect.y-10))

    def _spawn_dust(self, initial=False):
        x = random.uniform(0, SCREEN_WIDTH) if initial else random.uniform(-60, 0)
        y = random.uniform(self.ring_thick+40, SCREEN_HEIGHT-self.ring_thick-40)
        self.dust.append([x, y, random.uniform(1.8,4.2), random.uniform(-0.35,0.35), random.randint(44,90), random.uniform(0.85,1.35)])

    def _spawn_burst(self, x, y, big=False):
        self._bursts.append([float(x), float(y), 10.0 if not big else 18.0, 22 if not big else 30, 22 if not big else 30])

    def _spawn_hit_puff(self, x, y):
        self._hit_puffs.append([float(x), float(y), 9.0, 18, 18])

    def draw_background(self, screen):
        screen.blit(self._bg_cache, (0,0))
        a = 14 + int(6*(0.5+0.5*math.sin(self._heat_phase)))
        self.heat.fill((255,170,80,a))
        screen.blit(self.heat, (0,0))

    def draw_foreground(self, screen):
        screen.blit(self._fg_cache, (0,0))
        for obs in self.obstacles:
            if getattr(obs,"type","")=="wall" and obs.rect.w < 300:
                self._draw_stone_pillar(screen, obs.rect)
        
        # VFX render
        for x,y,r,l,m in self._bursts:
            s = pygame.Surface((int(r*2+6), int(r*2+6)), pygame.SRCALPHA)
            pygame.draw.circle(s, (230,215,165, int(140*(l/m))), (s.get_width()//2, s.get_height()//2), int(r), 2)
            screen.blit(s, (int(x-s.get_width()//2), int(y-s.get_height()//2)))
            
        for x,y,r,l,m in self._hit_puffs:
            s = pygame.Surface((int(r*2+6), int(r*2+6)), pygame.SRCALPHA)
            pygame.draw.circle(s, (210,190,140, int(120*(l/m))), (s.get_width()//2, s.get_height()//2), int(r), 0)
            screen.blit(s, (int(x-s.get_width()//2), int(y-s.get_height()//2)))

        for x,y,vx,vy,l,sc in self.dust:
            idx = max(0, min(len(self._dust_sprites)-1, int((l/90)*(len(self._dust_sprites)-1))))
            spr = self._dust_sprites[idx]
            w = max(6, int(spr.get_width()*sc))
            h = max(4, int(spr.get_height()*sc))
            screen.blit(pygame.transform.smoothscale(spr, (w,h)), (int(x), int(y)))

    def _draw_stone_pillar(self, screen, r):
        pygame.draw.rect(screen, self.stone_mid, r, border_radius=12)
        pygame.draw.rect(screen, self.stone_dark, r, 3, border_radius=12)
        pygame.draw.rect(screen, self.stone_light, (r.x+6, r.y+7, 9, r.h-14), border_radius=8)