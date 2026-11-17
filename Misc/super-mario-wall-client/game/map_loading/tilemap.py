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
class BlockSpec:
    rect: Rectangle
    order: int
    part: str


@dataclass(frozen=True)
class KoopaSpec:
    rect: Rectangle
    direction: str


@dataclass(frozen=True)
class Level:
    width: int
    height: int
    ground: tuple
    blocks: tuple
    spawn: tuple
    flower: Rectangle
    koopa: KoopaSpec
    goal: Rectangle


def _rect(obj):
    return Rectangle(*(int(float(obj.attrib.get(key, 0)))
                       for key in ("x", "y", "width", "height")))


def _properties(obj):
    return {prop.attrib["name"]: prop.attrib.get("value", "")
            for prop in obj.iter("property")}


def load(path):
    root = ET.parse(Path(path)).getroot()
    groups = {group.attrib["name"]: list(group.findall("object"))
              for group in root.findall("objectgroup")}

    def single(name):
        objects = groups.get(name, [])
        if len(objects) != 1:
            raise ValueError(f"map must contain exactly one {name} object")
        return objects[0]

    blocks = []
    for obj in groups.get("blocks", []):
        props = _properties(obj)
        blocks.append(BlockSpec(_rect(obj), int(props["order"]), props.get("part", "roof")))
    blocks.sort(key=lambda block: block.order)
    spawn = _rect(single("spawn"))
    koopa = single("koopa")
    return Level(
        int(root.attrib["width"]) * int(root.attrib["tilewidth"]),
        int(root.attrib["height"]) * int(root.attrib["tileheight"]),
        tuple(_rect(obj) for obj in groups.get("ground", [])),
        tuple(blocks),
        (spawn.x, spawn.y),
        _rect(single("flower")),
        KoopaSpec(_rect(koopa), _properties(koopa).get("direction", "right")),
        _rect(single("goal")),
    )
