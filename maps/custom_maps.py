# maps/custom_maps.py
"""Kovakoodatut custom-kartat (pelitesti 29).

TYÖNKULKU: kartta rakennetaan pelin sisäisellä editorilla (F8),
nimetään (F7) ja viedään F9:llä yhdeksi JSON-riviksi (map_export.txt +
konsoli). Se rivi liitetään chattiin, ja se lisätään TÄHÄN tiedostoon
register(r'''...''')-kutsulla. Editorin System-valikko listaa täällä
olevat kartat "Load: <nimi>" -riveinä, joten kovakoodattua karttaa voi
jatkaa suoraan editorissa.

ÄLÄ muokkaa blob-merkkijonoja käsin - vie kartta editorista uudelleen.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from systems.map_document import import_blob

CUSTOM_MAPS: Dict[str, dict] = {}


def register(blob: str) -> dict:
    """Rekisteröi viedyn kartan. Kutsutaan moduulitasolla alla."""
    doc = import_blob(blob)
    CUSTOM_MAPS[doc["name"]] = doc
    return doc


def custom_map_names() -> List[str]:
    return sorted(CUSTOM_MAPS.keys())


def get_custom_map(name: str) -> Optional[dict]:
    return CUSTOM_MAPS.get(name)


# ---------------------------------------------------------------------
# REKISTERÖIDYT KARTAT (uusin ylimmäs; lisää register(r'''<blob>''') )
# ---------------------------------------------------------------------
