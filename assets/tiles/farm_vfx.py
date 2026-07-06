import random

class FarmVFX:
    """
    Käsittelee maatilan objektien (kuten lannan) visuaaliset efektit.
    """
    
    @staticmethod
    def process_object(prop, manager):
        """
        Tarkistaa objektin tyypin ja luo efektejä (kärpäset, höyry) tarvittaessa.
        """
        # Tunnistetaan tyyppi luokan nimen perusteella
        obj_type = prop.__class__.__name__
        
        if obj_type == "Manure":
            # Yksittäinen lanta: Vähän kärpäsiä ja höyryä
            if random.random() < 0.05:
                manager.vfx.create_flies(prop.rect.centerx, prop.rect.centery)
            if random.random() < 0.01:
                manager.vfx.create_steam(prop.rect.centerx, prop.rect.centery)
                
        elif obj_type == "ManurePile":
            # Lantakasa: Paljon kärpäsiä ja höyryä
            if random.random() < 0.2:
                # Satunnainen sijainti kasan päällä (levitetään koko alueelle)
                w_spread = prop.rect.width // 2 - 10
                h_spread = prop.rect.height // 2 - 10
                x = prop.rect.centerx + random.randint(-w_spread, w_spread)
                y = prop.rect.centery + random.randint(-h_spread, h_spread)
                manager.vfx.create_flies(x, y)
                
            if random.random() < 0.05:
                x = prop.rect.centerx + random.randint(-40, 40)
                manager.vfx.create_steam(x, prop.rect.centery - 20)