from dataclasses import dataclass

KINDS = ("block", "flower", "koopa", "fireball")
PARTS = ("", "roof", "left_wall", "right_wall")


@dataclass
class Sprite:
    kind: str
    x: int
    y: int
    width: int
    height: int
    vx: int = 0
    vy: int = 0
    facing: int = 1
    bounces: int = 0
    bump: int = 0
    part: str = ""
    order: int = -1
    seq: int = -1
    removed: bool = False


# Fixed number of active sprites, like on the SNES: when every slot is taken,
# the oldest sprite gives way to the new one.
class SpriteTable:
    def __init__(self, size):
        self.size = size
        self.slots = [None] * size
        self.next_seq = 0

    def spawn(self, sprite):
        sprite.seq = self.next_seq
        sprite.removed = False
        self.next_seq += 1
        evicted = None
        index = next((i for i, slot in enumerate(self.slots) if slot is None), None)
        if index is None:
            index = min(range(self.size), key=lambda i: self.slots[i].seq)
            evicted = self.slots[index]
            evicted.removed = True
        self.slots[index] = sprite
        return evicted

    def remove(self, sprite):
        sprite.removed = True
        for index, slot in enumerate(self.slots):
            if slot is sprite:
                self.slots[index] = None
                return

    def active(self, kind=None):
        return [sprite for sprite in self.slots
                if sprite is not None and not sprite.removed
                and (kind is None or sprite.kind == kind)]

    def free_count(self):
        return self.slots.count(None)
