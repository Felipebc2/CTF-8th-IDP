import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rectangle:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class TowerMap:
    width: int
    height: int
    solids: tuple
    platforms: tuple
    spawn: tuple
    goal: Rectangle
    coin: Rectangle | None = None
    rendered_platforms: tuple = ()


def load(path):
    root = ET.parse(Path(path)).getroot()
    groups = {group.attrib["name"]: group for group in root.findall("objectgroup")}

    def rects(name):
        return tuple(
            Rectangle(*(int(float(obj.attrib[key])) for key in ("x", "y", "width", "height")))
            for obj in groups.get(name, ())
        )

    spawn_object = next(iter(groups["spawn"]))
    spawn = (int(float(spawn_object.attrib["x"])), int(float(spawn_object.attrib["y"])))
    first_platforms = rects("one_way_a")
    second_platforms = rects("one_way_b")
    platforms = tuple(sorted(first_platforms + second_platforms,
                             key=lambda platform: (-platform.y, platform.x)))
    coins = rects("coin")
    return TowerMap(
        int(root.attrib["width"]) * int(root.attrib["tilewidth"]),
        int(root.attrib["height"]) * int(root.attrib["tileheight"]),
        rects("solid"), platforms, spawn, rects("goal")[0], coins[0] if coins else None,
        tuple(index for index, platform in enumerate(platforms) if platform in first_platforms),
    )
