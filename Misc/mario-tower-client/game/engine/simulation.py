import hashlib
import struct
from dataclasses import dataclass

from game.map_loading.tilemap import Rectangle

SCALE = 256
PLAYER_WIDTH = 20 * SCALE
PLAYER_HEIGHT = 28 * SCALE
GRAVITY = 192
MAX_FALL_SPEED = 16 * SCALE
WALK_SPEED = 5 * SCALE
RUN_SPEED = 6 * SCALE
ACCELERATION = 64
BRAKE = 154
FRICTION = 51
JUMP_SPEED = -16 * SCALE
FALL_SOUND_TICKS = 315


@dataclass
class Player:
    x: int
    y: int
    vx: int = 0
    vy: int = 0
    grounded: bool = False
    won: bool = False
    dead: bool = False
    facing: int = 1


class Game:
    def __init__(self, world):
        self.world = world
        self.player = Player(world.spawn[0] * SCALE, world.spawn[1] * SCALE)
        self.player.grounded = self._standing_on_solid()
        self.tick_count = 0
        self.jump_held = False
        self.death_ticks = 0
        self.coin_collected = False

    @property
    def goal(self):
        return self.world.goal

    @property
    def coin(self):
        return self.world.coin

    @property
    def rect(self):
        y = -(-self.player.y // SCALE)
        return Rectangle(self.player.x // SCALE, y,
                         PLAYER_WIDTH // SCALE, PLAYER_HEIGHT // SCALE)

    def reset(self):
        self.player = Player(self.world.spawn[0] * SCALE, self.world.spawn[1] * SCALE)
        self.player.grounded = self._standing_on_solid()
        self.jump_held = False
        self.death_ticks = 0
        self.coin_collected = False

    def die(self):
        self.player.dead = True
        self.player.vx = 0
        self.player.vy = 0
        self.player.grounded = False
        self.death_ticks = 0

    def _standing_on_solid(self):
        rect = self.rect
        return any(
            rect.y + rect.height == solid.y and
            rect.x < solid.x + solid.width and rect.x + rect.width > solid.x
            for solid in self.world.solids
        )

    @staticmethod
    def overlaps(first, second):
        return (first.x < second.x + second.width and first.x + first.width > second.x
                and first.y < second.y + second.height and first.y + first.height > second.y)

    def _move_horizontal(self, amount):
        self.player.x += amount
        rect = self.rect
        for solid in self.world.solids:
            if self.overlaps(rect, solid):
                if amount > 0:
                    self.player.x = (solid.x - rect.width) * SCALE
                else:
                    self.player.x = (solid.x + solid.width) * SCALE
                self.player.vx = 0
                rect = self.rect

    def _move_vertical(self, amount, old_bottom):
        self.player.y += amount
        rect = self.rect
        self.player.grounded = False
        for solid in self.world.solids:
            if self.overlaps(rect, solid):
                if amount > 0:
                    self.player.y = (solid.y - rect.height) * SCALE
                    self.player.grounded = True
                else:
                    self.player.y = (solid.y + solid.height) * SCALE
                self.player.vy = 0
                rect = self.rect
        if amount > 0:
            for platform in self.world.platforms:
                if (old_bottom <= platform.y * SCALE and
                        self.player.y + PLAYER_HEIGHT >= platform.y * SCALE and
                        rect.x < platform.x + platform.width and
                        rect.x + rect.width > platform.x):
                    self.player.y = (platform.y - rect.height) * SCALE
                    self.player.vy = 0
                    self.player.grounded = True
                    rect = self.rect

    def step(self, keys=()):
        keys = set(keys)
        if "r" in keys:
            self.reset()
            self.tick_count += 1
            return
        if self.player.dead:
            self.death_ticks += 1
            if self.death_ticks >= FALL_SOUND_TICKS:
                self.reset()
            self.tick_count += 1
            return
        direction = int("right" in keys or "d" in keys) - int("left" in keys or "a" in keys)
        if direction:
            self.player.facing = direction
        target = direction * (RUN_SPEED if "run" in keys or "z" in keys else WALK_SPEED)
        if direction and (self.player.vx * direction < 0):
            change = BRAKE
        else:
            change = ACCELERATION
        if self.player.vx < target:
            self.player.vx = min(target, self.player.vx + change)
        elif self.player.vx > target:
            self.player.vx = max(target, self.player.vx - change)
        if not direction and self.player.vx:
            friction = min(abs(self.player.vx), FRICTION)
            self.player.vx -= friction if self.player.vx > 0 else -friction
        jump_held = bool(keys.intersection({"jump", "w", "up"}))
        if self.player.grounded and jump_held and not self.jump_held:
            self.player.vy = JUMP_SPEED
            self.player.grounded = False
        old_bottom = self.player.y + PLAYER_HEIGHT
        self._move_horizontal(self.player.vx)
        self.player.vy = min(MAX_FALL_SPEED, self.player.vy + GRAVITY)
        self._move_vertical(self.player.vy, old_bottom)
        if self.player.y > self.world.height * SCALE:
            self.die()
        if self.overlaps(self.rect, self.goal):
            self.player.won = True
        elif (self.coin and not self.coin_collected
              and self.overlaps(self.rect, self.coin)):
            self.coin_collected = True
        self.jump_held = jump_held
        self.tick_count += 1

    def state_hash(self):
        p = self.player
        payload = struct.pack(">qqqq????QQ", p.x, p.y, p.vx, p.vy, p.won,
                              p.dead, self.jump_held, self.coin_collected,
                              self.death_ticks, self.tick_count)
        return hashlib.blake2b(payload, digest_size=16).hexdigest()
