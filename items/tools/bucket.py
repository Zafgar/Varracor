from items.item import Item
import pygame
import os

class BucketEmpty(Item):
    def __init__(self):
        super().__init__("Empty Bucket", "Tool", 10, "A sturdy wooden bucket.")
        self.image_path = "assets/gear/tools/bucket_empty.png"
        self.stackable = False
        self.slot_type = "main_hand"
        self.image = None
        self._load_image()

    def _load_image(self):
        if os.path.exists(self.image_path):
            try:
                img = pygame.image.load(self.image_path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 24))
            except Exception: pass

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        if self.image:
            _draw_bucket_sprite(surface, self.image, unit_rect, facing_right)
        else:
            _draw_bucket(surface, unit_rect, facing_right, None)

class BucketMilk(Item):
    def __init__(self):
        super().__init__("Bucket of Milk", "Tool", 50, "Fresh milk from a cow.")
        self.image_path = "assets/gear/tools/bucket_milk.png"
        self.stackable = False
        self.slot_type = "main_hand"
        self.image = None
        self._load_image()

    def _load_image(self):
        if os.path.exists(self.image_path):
            try:
                img = pygame.image.load(self.image_path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 24))
            except Exception: pass

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        if self.image:
            _draw_bucket_sprite(surface, self.image, unit_rect, facing_right)
        else:
            _draw_bucket(surface, unit_rect, facing_right, (240, 240, 230)) # Valkoinen maito

class BucketWater(Item):
    def __init__(self):
        super().__init__("Bucket of Water", "Tool", 20, "Fresh water from a well.")
        self.image_path = "assets/gear/tools/bucket_water.png"
        self.stackable = False
        self.slot_type = "main_hand"
        self.image = None
        self._load_image()

    def _load_image(self):
        # Yritetään ladata oikealla nimellä
        if os.path.exists(self.image_path):
            try:
                img = pygame.image.load(self.image_path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 24))
                return
            except Exception: pass
        
        # Fallback: Yritetään ladata kirjoitusvirheellisellä nimellä (bucekt) jos alkuperäinen puuttuu
        typo_path = self.image_path.replace("bucket", "bucekt")
        if os.path.exists(typo_path):
            try:
                img = pygame.image.load(typo_path).convert_alpha()
                self.image = pygame.transform.smoothscale(img, (24, 24))
            except Exception: pass

    def draw_equipped(self, surface, unit_rect, facing_right, attack_cooldown):
        if self.image:
            _draw_bucket_sprite(surface, self.image, unit_rect, facing_right)
        else:
            _draw_bucket(surface, unit_rect, facing_right, (100, 150, 255)) # Sininen vesi

def _draw_bucket_sprite(surface, image, unit_rect, facing_right):
    """Piirtää ladatun kuvan hahmon käteen."""
    offset_x = 5 if facing_right else -5
    hand_x = unit_rect.centerx + offset_x
    hand_y = unit_rect.centery + 10
    
    img = image
    if not facing_right:
        img = pygame.transform.flip(image, True, False)
    
    rect = img.get_rect(center=(hand_x, hand_y))
    surface.blit(img, rect)

def _draw_bucket(surface, unit_rect, facing_right, content_color):
    """Yhteinen piirtofunktio ämpäreille."""
    offset_x = 5 if facing_right else -5
    hand_x = unit_rect.centerx + offset_x
    hand_y = unit_rect.centery + 10
    
    # Ämpärin runko (ruskea)
    bucket_rect = pygame.Rect(hand_x - 5, hand_y, 10, 12)
    pygame.draw.rect(surface, (100, 70, 40), bucket_rect)
    pygame.draw.rect(surface, (60, 40, 20), bucket_rect, 1) # Reuna
    
    # Sisältö
    if content_color:
        pygame.draw.rect(surface, content_color, (hand_x - 4, hand_y + 2, 8, 8))
        
    # Kahva (harmaa kaari)
    pygame.draw.arc(surface, (150, 150, 150), (hand_x - 5, hand_y - 5, 10, 10), 0, 3.14, 1)
