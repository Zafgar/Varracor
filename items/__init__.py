# items/__init__.py

# Tämä tiedosto varmistaa yhteensopivuuden.
# Gladiator-luokka hakee täältä panssarien statsit.

ARMOR = {
    'No Armor':     {'cost': 0,   'defense': 0,  'health_bonus': 0},
    'Cloth Tunic':  {'cost': 50,  'defense': 1,  'health_bonus': 10}, # Huom: Nimetty uusiksi vastaamaan luokkia
    'Tunic':        {'cost': 50,  'defense': 1,  'health_bonus': 10}, # Vanha nimi varalla
    'Leather Vest': {'cost': 100, 'defense': 3,  'health_bonus': 30},
    'Chainmail':    {'cost': 250, 'defense': 6,  'health_bonus': 60},
    'Plate Armor':  {'cost': 500, 'defense': 10, 'health_bonus': 100},
    'Robes':        {'cost': 75,  'defense': 2,  'health_bonus': 20},
    
    # Craftattavat (Loot Data)
    'Bone Armor':   {'cost': 0, 'defense': 5,  'health_bonus': 50},
    'Slime Shield': {'cost': 0, 'defense': 4,  'health_bonus': 40},
    'Dragon Plate': {'cost': 0, 'defense': 15, 'health_bonus': 200}
}

# WEAPONS on tyhjä, koska käytämme nyt item_registryä aseille
WEAPONS = {}