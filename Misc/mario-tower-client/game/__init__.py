"""Game modules."""
from pathlib import Path

CHARACTER = "mario"
MAPS = Path(__file__).parent / "resources" / "maps"


def map_path(character=CHARACTER):
    return MAPS / f"{character}.tmx"
