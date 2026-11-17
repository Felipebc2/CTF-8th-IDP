import hashlib
import struct
from dataclasses import dataclass

from game.engine.constants import (
    DUCK_SIZE,
    ACCELERATION, BOUNCE_SPEED, BOUNCE_SPEED_HELD, BRAKE, BUMP_TICKS, DEATH_TICKS,
    FIRE_SIZE, FIREBALL_BOUNCE_SPEED, FIREBALL_BOUNCES, FIREBALL_COOLDOWN,
    FIREBALL_SIZE, FIREBALL_SPEED, FLOWER_SIZE, FRICTION, GRAVITY,
    INVULNERABLE_TICKS, JUMP_SPEEDS, KOOPA_SIZE, KOOPA_SPEED, MAX_FALL_SPEED,
    MAX_SPRITES, P_METER_MAX, RUN_SPEED, SCALE, SESSION_TICKS, SMALL_SIZE,
    SPRINT_SPEED, WALK_SPEED,
)
from game.engine.sprites import KINDS, PARTS, Sprite, SpriteTable
from game.map_loading.tilemap import Rectangle

POWERS = ("small", "fire")
JUMP_KEYS = {"jump", "w", "up"}
RUN_KEYS = {"run", "z", "fire", "x"}
DOWN_KEYS = {"down", "s"}


@dataclass
class Player:
    x: int
    y: int
    vx: int = 0
    vy: int = 0
    power: str = "small"
    facing: int = 1
    grounded: bool = False
    dead: bool = False
    won: bool = False
    invulnerable: int = 0
    fire_cooldown: int = 0
    p_meter: int = 0
    ducking: bool = False

    @property
    def size(self):
        if self.ducking:
            return DUCK_SIZE
        return FIRE_SIZE if self.power == "fire" else SMALL_SIZE

    @property
    def width(self):
        return self.size[0]

    @property
    def height(self):
        return self.size[1]


def overlaps(first, second):
    return (first.x < second.x + second.width and first.x + first.width > second.x
            and first.y < second.y + second.height and first.y + first.height > second.y)


def to_rect(x, y, width, height):
    return Rectangle(x // SCALE, -(-y // SCALE), width, height)


def sprite_rect(sprite):
    return to_rect(sprite.x, sprite.y, sprite.width, sprite.height)


class Game:
    def __init__(self, level):
        self.level = level
        self.tick_count = 0
        self.events = []
        self.reset()

    def reset(self):
        level = self.level
        self.player = Player(level.spawn[0] * SCALE, level.spawn[1] * SCALE)
        self.sprites = SpriteTable(MAX_SPRITES)
        for block in level.blocks:
            rect = block.rect
            self.sprites.spawn(Sprite("block", rect.x * SCALE, rect.y * SCALE,
                                      rect.width, rect.height, part=block.part,
                                      order=block.order))
        flower = level.flower
        self.sprites.spawn(Sprite("flower", flower.x * SCALE, flower.y * SCALE, *FLOWER_SIZE))
        koopa = level.koopa.rect
        self.sprites.spawn(Sprite("koopa", koopa.x * SCALE, koopa.y * SCALE, *KOOPA_SIZE,
                                  facing=-1 if level.koopa.direction == "left" else 1))
        self.jump_held = False
        self.fire_held = False
        self.death_ticks = 0
        self.player.grounded = self._standing_on_solid()

    @property
    def session_over(self):
        return self.tick_count >= SESSION_TICKS

    def player_rect(self):
        p = self.player
        return to_rect(p.x, p.y, p.width, p.height)

    def _solids(self):
        solids = [(rect, None) for rect in self.level.ground]
        solids.extend((sprite_rect(block), block) for block in self.sprites.active("block"))
        return solids

    def _standing_on_solid(self):
        rect = self.player_rect()
        return any(
            rect.y + rect.height == solid.y and
            rect.x < solid.x + solid.width and rect.x + rect.width > solid.x
            for solid, _ in self._solids()
        )

    def _set_ducking(self, ducking):
        p = self.player
        height = p.height
        p.ducking = ducking
        p.y += (height - p.height) * SCALE
        if not ducking:
            rect = self.player_rect()
            if any(overlaps(rect, solid) for solid, _ in self._solids()):
                p.ducking = True
                p.y -= (height - p.height) * SCALE

    def _set_power(self, power):
        p = self.player
        height = p.height
        p.power = power
        # Keep the feet where they were.
        p.y += (height - p.height) * SCALE
        rect = self.player_rect()
        if not p.ducking and any(overlaps(rect, solid) for solid, _ in self._solids()):
            # No room to grow: crouch until there is.
            self._set_ducking(True)

    def die(self):
        self.player.dead = True
        self.player.vx = 0
        self.player.vy = 0
        self.player.grounded = False
        self.death_ticks = 0
        self.events.append("death")

    def _move_horizontal(self, amount, solids):
        p = self.player
        p.x += amount
        rect = self.player_rect()
        for solid, _ in solids:
            if overlaps(rect, solid):
                if amount > 0:
                    p.x = (solid.x - rect.width) * SCALE
                else:
                    p.x = (solid.x + solid.width) * SCALE
                p.vx = 0
                rect = self.player_rect()
        # The level edges stop the player only; enemies and fireballs walk off.
        limit = (self.level.width - p.width) * SCALE
        if p.x < 0 or p.x > limit:
            p.x = max(0, min(limit, p.x))
            p.vx = 0

    def _move_vertical(self, amount, solids):
        p = self.player
        p.y += amount
        rect = self.player_rect()
        p.grounded = False
        for solid, block in solids:
            if overlaps(rect, solid):
                if amount > 0:
                    p.y = (solid.y - rect.height) * SCALE
                    p.grounded = True
                else:
                    p.y = (solid.y + solid.height) * SCALE
                    if block is not None:
                        block.bump = BUMP_TICKS
                p.vy = 0
                rect = self.player_rect()

    def _update_player(self, keys):
        p = self.player
        direction = int("right" in keys or "d" in keys) - int("left" in keys or "a" in keys)
        if p.grounded:
            ducking = bool(keys & DOWN_KEYS)
            if ducking != p.ducking:
                self._set_ducking(ducking)
            if p.ducking:
                direction = 0
        if direction:
            p.facing = direction
        running = bool(keys & RUN_KEYS)
        if p.grounded:
            if running and direction and p.vx * direction >= RUN_SPEED:
                p.p_meter = min(P_METER_MAX, p.p_meter + 2)
            elif p.p_meter:
                p.p_meter -= 1
        if not running:
            speed = WALK_SPEED
        elif p.p_meter == P_METER_MAX:
            speed = SPRINT_SPEED
        else:
            speed = RUN_SPEED
        target = direction * speed
        if direction and p.vx * direction < 0:
            change = BRAKE
        else:
            change = ACCELERATION
        if p.vx < target:
            p.vx = min(target, p.vx + change)
        elif p.vx > target:
            p.vx = max(target, p.vx - change)
        if not direction and p.vx:
            friction = min(abs(p.vx), FRICTION)
            p.vx -= friction if p.vx > 0 else -friction
        jump_held = bool(keys & JUMP_KEYS)
        if p.grounded and jump_held and not self.jump_held:
            p.vy = JUMP_SPEEDS[min(abs(p.vx) // (2 * SCALE), len(JUMP_SPEEDS) - 1)]
            p.grounded = False
            self.events.append("jump")
        self.jump_held = jump_held
        solids = self._solids()
        self._move_horizontal(p.vx, solids)
        p.vy = min(MAX_FALL_SPEED, p.vy + GRAVITY)
        falling = p.vy > 0
        self._move_vertical(p.vy, solids)
        return falling

    def _touch_koopa(self, old_bottom, falling, jump_held):
        p = self.player
        for koopa in self.sprites.active("koopa"):
            if not overlaps(self.player_rect(), sprite_rect(koopa)):
                continue
            if falling and old_bottom <= koopa.y:
                koopa.removed = True
                p.y = koopa.y - p.height * SCALE
                p.vy = BOUNCE_SPEED_HELD if jump_held else BOUNCE_SPEED
                p.grounded = False
                self.events.extend(("stomp", "koopa_killed"))
            elif not p.invulnerable:
                if p.power == "fire":
                    self._set_power("small")
                    p.invulnerable = INVULNERABLE_TICKS
                    self.events.append("powerdown")
                else:
                    self.die()
                    return

    def _touch_flower(self):
        p = self.player
        for flower in self.sprites.active("flower"):
            if overlaps(self.player_rect(), sprite_rect(flower)):
                flower.removed = True
                if p.power == "small":
                    self._set_power("fire")
                self.events.append("powerup")

    def _shoot(self, keys):
        p = self.player
        fire_held = bool(keys & RUN_KEYS)
        if (fire_held and not self.fire_held and p.power == "fire" and not p.fire_cooldown
                and not p.ducking):
            width, height = FIREBALL_SIZE
            x = p.x + p.width * SCALE if p.facing > 0 else p.x - width * SCALE
            y = p.y + (p.height - height) // 2 * SCALE
            ball = Sprite("fireball", x, y, width, height,
                          vx=p.facing * FIREBALL_SPEED, facing=p.facing)
            if self.sprites.spawn(ball) is not None:
                self.events.append("evicted")
            p.fire_cooldown = FIREBALL_COOLDOWN
            self.events.append("fire")
        self.fire_held = fire_held

    def _outside(self, sprite):
        return (sprite.x + sprite.width * SCALE <= 0 or sprite.x >= self.level.width * SCALE
                or sprite.y >= self.level.height * SCALE)

    def _update_koopas(self):
        solids = self._solids()
        for koopa in self.sprites.active("koopa"):
            koopa.x += koopa.facing * KOOPA_SPEED
            rect = sprite_rect(koopa)
            for solid, _ in solids:
                if overlaps(rect, solid):
                    if koopa.facing > 0:
                        koopa.x = (solid.x - koopa.width) * SCALE
                    else:
                        koopa.x = (solid.x + solid.width) * SCALE
                    koopa.facing = -koopa.facing
                    rect = sprite_rect(koopa)
            koopa.vy = min(MAX_FALL_SPEED, koopa.vy + GRAVITY)
            koopa.y += koopa.vy
            rect = sprite_rect(koopa)
            for solid, _ in solids:
                if overlaps(rect, solid):
                    if koopa.vy > 0:
                        koopa.y = (solid.y - koopa.height) * SCALE
                    else:
                        koopa.y = (solid.y + solid.height) * SCALE
                    koopa.vy = 0
                    rect = sprite_rect(koopa)
            if self._outside(koopa):
                koopa.removed = True

    def _update_fireballs(self):
        solids = self._solids()
        for ball in self.sprites.active("fireball"):
            ball.x += ball.vx
            rect = sprite_rect(ball)
            if any(overlaps(rect, solid) for solid, _ in solids):
                ball.removed = True
                continue
            ball.vy = min(MAX_FALL_SPEED, ball.vy + GRAVITY)
            ball.y += ball.vy
            rect = sprite_rect(ball)
            landed = False
            for solid, _ in solids:
                if overlaps(rect, solid):
                    if ball.vy > 0:
                        ball.y = (solid.y - ball.height) * SCALE
                        landed = True
                    else:
                        ball.y = (solid.y + solid.height) * SCALE
                        ball.vy = 0
                    rect = sprite_rect(ball)
            if landed:
                ball.vy = FIREBALL_BOUNCE_SPEED
                ball.bounces += 1
            for koopa in self.sprites.active("koopa"):
                if overlaps(rect, sprite_rect(koopa)):
                    koopa.removed = True
                    ball.removed = True
                    self.events.append("koopa_killed")
                    break
            if ball.bounces >= FIREBALL_BOUNCES or self._outside(ball):
                ball.removed = True

    def _flush_removed(self):
        for index, sprite in enumerate(self.sprites.slots):
            if sprite is not None and sprite.removed:
                self.sprites.slots[index] = None

    def _tick_counters(self):
        p = self.player
        if p.invulnerable:
            p.invulnerable -= 1
        if p.fire_cooldown:
            p.fire_cooldown -= 1
        for block in self.sprites.active("block"):
            if block.bump:
                block.bump -= 1
        self.tick_count += 1

    def step(self, keys=()):
        self.events = []
        keys = {key for key in keys if isinstance(key, str)}
        if "r" in keys:
            self.reset()
            self.tick_count += 1
            return
        p = self.player
        if p.dead:
            self.death_ticks += 1
            if self.death_ticks >= DEATH_TICKS:
                self.reset()
            self.tick_count += 1
            return
        jump_held = bool(keys & JUMP_KEYS)
        old_bottom = p.y + p.height * SCALE
        falling = self._update_player(keys)
        self._touch_koopa(old_bottom, falling, jump_held)
        if p.dead:
            self.tick_count += 1
            return
        self._touch_flower()
        self._shoot(keys)
        self._update_koopas()
        self._update_fireballs()
        self._flush_removed()
        if not p.won and overlaps(self.player_rect(), self.level.goal):
            p.won = True
            self.events.append("goal")
        self._tick_counters()

    def state_hash(self):
        p = self.player
        table = self.sprites
        digest = hashlib.blake2b(digest_size=16)
        digest.update(struct.pack(
            ">qqqqBb???qqq???qqqq",
            p.x, p.y, p.vx, p.vy, POWERS.index(p.power), p.facing,
            p.grounded, p.dead, p.won, p.invulnerable, p.fire_cooldown,
            p.p_meter, p.ducking,
            self.jump_held, self.fire_held, self.death_ticks, self.tick_count,
            table.next_seq, table.size,
        ))
        for sprite in table.slots:
            if sprite is None:
                digest.update(b"\x00")
                continue
            digest.update(struct.pack(
                ">BBqqqqqqqbqqBq?",
                1, KINDS.index(sprite.kind), sprite.seq, sprite.x, sprite.y,
                sprite.vx, sprite.vy, sprite.width, sprite.height, sprite.facing,
                sprite.bounces, sprite.bump, PARTS.index(sprite.part), sprite.order,
                sprite.removed,
            ))
        return digest.hexdigest()
