import argparse
import os
import select
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game.engine.constants import BUMP_TICKS, P_METER_MAX, SCALE, SESSION_TICKS, WALK_SPEED
from game.engine.simulation import Game
from game.map_loading.tilemap import load
from game.network import connect, recv_packet, send_packet

MAP_PATH = Path(__file__).parent / "resources" / "maps" / "level.tmx"
SPRITES = Path(__file__).parent / "resources" / "sprites"
SOUNDS = Path(__file__).parent / "resources" / "sounds"
WIDTH, HEIGHT = 960, 640
TILE = 32
PIXEL = 2
DEFAULT_PORT = 23197
GOAL_SOUND_TICKS = 606
FLAT_TICKS = 30
THROW_TICKS = 8
TURN_TICKS = 8
SMOKE_TICKS = 6
COIN_HOLD_TICKS = 4
BUSTED_TICKS = 600
BUSTED_MESSAGE = "CHEATER DETECTED!!!\nNice try, but no flag for you!\nClosing in {}.."

MARIO_FRAMES = {
    "small": ("stand", "duck", "walk_0", "walk_1", "walk_2", "run_0", "run_1", "run_2",
              "jump", "fall", "death"),
    "fire": ("stand", "duck", "walk_0", "walk_1", "walk_2", "run_0", "run_1", "run_2",
             "jump", "fall", "throw"),
}
KOOPA_FRAMES = ("walk_0", "walk_1", "turn", "flat")
EVENT_SOUNDS = {
    "jump": "jump",
    "fire": "fireball",
    "stomp": "kill",
    "koopa_killed": "kill",
    "powerup": "powerup",
    "powerdown": "powerdown",
    "goal": "coin",
}


def load_image(name, scale=PIXEL):
    image = pygame.image.load(SPRITES / f"{name}.png").convert_alpha()
    if scale != 1:
        image = pygame.transform.scale(image, (image.get_width() * scale, image.get_height() * scale))
    return image


class Client:
    def __init__(self, host=None, port=DEFAULT_PORT, map_path=MAP_PATH):
        self.game = Game(load(map_path))
        self.level = self.game.level
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption("Super Mario Wall")
        self.clock = pygame.time.Clock()
        self.status_font = pygame.font.Font(None, 36)
        self.load_images()
        self.sounds = self.load_sounds()
        self.session_ticks = SESSION_TICKS
        self.message = None
        self.busted_ticks = None
        self.goal_ticks = None
        self.flat_koopas = []
        self.koopa_turns = {}
        self.koopa_facing = {}
        self.throw_ticks = 0
        self.connection = None
        if host:
            self.show_status("Connecting...")
            self.connection = connect(host, port)
            self.show_status("Starting session...")
            self.wait_for_server()
            initial = recv_packet(self.connection)
            if isinstance(initial.get("session_ticks"), int) and initial["session_ticks"] > 0:
                self.session_ticks = initial["session_ticks"]
            self.show_status("Connected")
            pygame.time.delay(300)
        self.play_theme()

    def load_images(self):
        background = pygame.image.load(SPRITES / "background.png").convert()
        width = background.get_width() * HEIGHT // background.get_height()
        self.background = pygame.transform.scale(background, (width, HEIGHT))
        self.ground_tiles = [
            pygame.transform.scale(load_image(f"ground_{index}", 1), (TILE, TILE))
            for index in range(6)
        ]
        self.block_tile = pygame.transform.scale(load_image("block", 1), (TILE, TILE))
        self.mario = {
            power: {name: load_image(f"mario_{power}_{name}") for name in names}
            for power, names in MARIO_FRAMES.items()
        }
        self.koopa = {name: load_image(f"koopa_{name}") for name in KOOPA_FRAMES}
        self.flower = [load_image(f"flower_{index}") for index in range(2)]
        self.fireball = [load_image(f"fireball_{index}") for index in range(4)]
        self.goal_coins = [load_image(f"goal_coin_{index}") for index in range(4)]
        self.smoke = [load_image(f"smoke_{index}") for index in range(4)]
        self.timer_images = {
            character: pygame.transform.scale(load_image(f"timer_{character}", 1), (24, 24))
            for character in "0123456789"
        }

    def load_sounds(self):
        try:
            pygame.mixer.init()
            sounds = {
                name: pygame.mixer.Sound(SOUNDS / f"{name}.ogg")
                for name in ("jump", "fireball", "kill", "powerup", "powerdown", "coin", "fall", "goal")
            }
            for sound in sounds.values():
                sound.set_volume(0.35)
            return sounds
        except (pygame.error, FileNotFoundError):
            return {}

    def play_theme(self):
        if not pygame.mixer.get_init():
            return
        pygame.mixer.music.load(SOUNDS / "overworld.ogg")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

    def stop_theme(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def wait_for_server(self):
        while not select.select([self.connection], [], [], 0.05)[0]:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
            self.show_status("Starting session...")

    def show_status(self, message):
        self.screen.blit(self.background, (0, 0))
        self.draw_message(message)
        pygame.event.pump()
        self.present()

    def draw_message(self, message, color=(255, 255, 255)):
        lines = message.split("\n")
        height = self.status_font.get_linesize()
        top = HEIGHT // 2 - height * (len(lines) - 1) // 2
        for index, line in enumerate(lines):
            text = self.status_font.render(line, True, color)
            shadow = self.status_font.render(line, True, (20, 20, 20))
            position = text.get_rect(center=(WIDTH // 2, top + index * height))
            self.screen.blit(shadow, position.move(2, 2))
            self.screen.blit(text, position)

    def present(self):
        window_width, window_height = self.window.get_size()
        scale = min(window_width / WIDTH, window_height / HEIGHT)
        size = (round(WIDTH * scale), round(HEIGHT * scale))
        frame = pygame.transform.scale(self.screen, size)
        self.window.fill((0, 0, 0))
        self.window.blit(frame, ((window_width - size[0]) // 2, (window_height - size[1]) // 2))
        pygame.display.flip()

    def keys(self):
        pressed = pygame.key.get_pressed()
        keys = []
        if pressed[pygame.K_a] or pressed[pygame.K_LEFT]:
            keys.append("left")
        if pressed[pygame.K_d] or pressed[pygame.K_RIGHT]:
            keys.append("right")
        if (pressed[pygame.K_w] or pressed[pygame.K_UP] or pressed[pygame.K_SPACE]
                or pressed[pygame.K_KP4]):
            keys.append("jump")
        if (pressed[pygame.K_z] or pressed[pygame.K_x]
                or pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]
                or pressed[pygame.K_KP5]):
            keys.append("run")
        if pressed[pygame.K_s] or pressed[pygame.K_DOWN]:
            keys.append("down")
        if pressed[pygame.K_r]:
            keys.append("r")
        return keys

    def camera_x(self):
        p = self.game.player
        desired = p.x // SCALE + p.width // 2 - WIDTH // 2
        return max(0, min(desired, self.level.width - WIDTH))

    def blit_on(self, image, rect, camera, flip=False, y_offset=0):
        if flip:
            image = pygame.transform.flip(image, True, False)
        x = rect.x + (rect.width - image.get_width()) // 2 - camera
        y = rect.y + rect.height - image.get_height() + y_offset
        self.screen.blit(image, (x, y))

    def draw_background(self, camera):
        width = self.background.get_width()
        x = -((camera // 2) % width)
        while x < WIDTH:
            self.screen.blit(self.background, (x, 0))
            x += width

    def draw_ground(self, rect, camera):
        old_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(rect.x - camera, rect.y, rect.width, rect.height))
        last_column = (rect.width - 1) // TILE
        first_x = max(rect.x, camera - camera % TILE)
        for x in range(first_x, min(rect.x + rect.width, camera + WIDTH + TILE), TILE):
            column = (x - rect.x) // TILE
            left = column == 0 and rect.x > 0
            right = column == last_column and rect.x + rect.width < self.level.width
            for y in range(rect.y, rect.y + rect.height, TILE):
                index = 0 if y == rect.y else 3
                index += 0 if left else 2 if right else 1
                self.screen.blit(self.ground_tiles[index], (x - camera, y))
        self.screen.set_clip(old_clip)

    def bump_offset(self, block):
        if not block.bump:
            return 0
        return -2 * min(block.bump, BUMP_TICKS - block.bump)

    def draw_block(self, block, camera):
        x0 = block.x // SCALE
        y0 = block.y // SCALE + self.bump_offset(block)
        for x in range(x0, x0 + block.width, TILE):
            for y in range(y0, y0 + block.height, TILE):
                self.screen.blit(self.block_tile, (x - camera, y))

    def draw_flower(self, flower, camera):
        frame = (self.game.tick_count // 8) % 4
        image = self.flower[frame % 2]
        self.blit_on(image, self.sprite_rect(flower), camera, flip=frame >= 2)

    def draw_koopa(self, koopa, camera):
        if self.koopa_turns.get(koopa.seq, 0) > 0:
            image = self.koopa["turn"]
        else:
            image = self.koopa[f"walk_{(self.game.tick_count // 8) % 2}"]
        self.blit_on(image, self.sprite_rect(koopa), camera, flip=koopa.facing > 0)

    def draw_fireball(self, ball, camera):
        image = self.fireball[(self.game.tick_count // 4) % len(self.fireball)]
        rect = self.sprite_rect(ball)
        x = rect.x + (rect.width - image.get_width()) // 2 - camera
        y = rect.y + (rect.height - image.get_height()) // 2
        self.screen.blit(pygame.transform.flip(image, ball.facing < 0, False), (x, y))

    def draw_goal(self, camera):
        if self.goal_ticks is not None and self.goal_ticks >= COIN_HOLD_TICKS:
            frame = (self.goal_ticks - COIN_HOLD_TICKS) // SMOKE_TICKS
            if frame >= len(self.smoke):
                return
            coin = self.smoke[frame]
        else:
            coin = self.goal_coins[(self.game.tick_count // 8) % len(self.goal_coins)]
        goal = self.level.goal
        x = goal.x + (goal.width - coin.get_width()) // 2 - camera
        y = goal.y + (goal.height - coin.get_height()) // 2
        self.screen.blit(coin, (x, y))

    def mario_frame(self):
        p = self.game.player
        frames = self.mario[p.power]
        if p.dead:
            return self.mario["small"]["death"]
        if p.ducking:
            return frames["duck"]
        if p.power == "fire" and self.throw_ticks:
            return frames["throw"]
        if not p.grounded:
            return frames["jump" if p.vy < 0 else "fall"]
        if p.vx:
            kind = "run" if p.p_meter == P_METER_MAX else "walk"
            step = 3 if kind == "run" else 4 if abs(p.vx) > WALK_SPEED else 6
            sequence = (0, 1, 2, 1)
            return frames[f"{kind}_{sequence[(self.game.tick_count // step) % 4]}"]
        return frames["stand"]

    def draw_mario(self, camera):
        p = self.game.player
        if p.invulnerable and (p.invulnerable // 4) % 2:
            return
        rect = self.game.player_rect()
        y_offset = 0
        if p.dead:
            ticks = self.game.death_ticks
            if ticks > 30:
                t = ticks - 30
                y_offset = -8 * t + t * t // 4
            self.blit_on(self.mario_frame(), rect, camera, y_offset=y_offset)
            return
        self.blit_on(self.mario_frame(), rect, camera, flip=p.facing > 0)

    def draw_timer(self):
        remaining = max(0, self.session_ticks - self.game.tick_count)
        total_seconds = (remaining + 59) // 60
        text = f"{total_seconds // 60}:{total_seconds % 60:02d}"
        width = sum(12 if character == ":" else self.timer_images[character].get_width()
                    for character in text)
        x = (WIDTH - width) // 2
        for character in text:
            if character == ":":
                for y in (19, 31):
                    pygame.draw.rect(self.screen, (20, 20, 20), (x + 3, y, 6, 6))
                    pygame.draw.rect(self.screen, (248, 248, 248), (x + 4, y + 1, 4, 4))
                x += 12
            else:
                image = self.timer_images[character]
                self.screen.blit(image, (x, 12))
                x += image.get_width()

    @staticmethod
    def sprite_rect(sprite):
        return pygame.Rect(sprite.x // SCALE, sprite.y // SCALE, sprite.width, sprite.height)

    def draw(self):
        camera = self.camera_x()
        self.draw_background(camera)
        for rect in self.level.ground:
            self.draw_ground(rect, camera)
        self.draw_goal(camera)
        for sprite in self.game.sprites.active():
            if sprite.kind == "block":
                self.draw_block(sprite, camera)
            elif sprite.kind == "flower":
                self.draw_flower(sprite, camera)
        for rect, ticks in self.flat_koopas:
            self.blit_on(self.koopa["flat"], rect, camera)
        for sprite in self.game.sprites.active("koopa"):
            self.draw_koopa(sprite, camera)
        self.draw_mario(camera)
        for sprite in self.game.sprites.active("fireball"):
            self.draw_fireball(sprite, camera)
        self.draw_timer()
        if self.busted_ticks is not None:
            seconds = -(-self.busted_ticks // 60)
            self.draw_message(BUSTED_MESSAGE.format(seconds), (255, 60, 60))
        elif self.message:
            self.draw_message(self.message)
        self.present()

    def update_effects(self, koopas_before):
        events = self.game.events
        self.flat_koopas = [(rect, ticks - 1) for rect, ticks in self.flat_koopas if ticks > 1]
        alive = {koopa.seq for koopa in self.game.sprites.active("koopa")}
        if "koopa_killed" in events:
            for seq, rect in koopas_before.items():
                if seq not in alive:
                    self.flat_koopas.append((rect, FLAT_TICKS))
        for koopa in self.game.sprites.active("koopa"):
            turn = self.koopa_turns.get(koopa.seq, 0)
            if self.koopa_facing.get(koopa.seq, koopa.facing) != koopa.facing:
                turn = TURN_TICKS
            self.koopa_turns[koopa.seq] = max(0, turn - 1)
            self.koopa_facing[koopa.seq] = koopa.facing
        if "fire" in events:
            self.throw_ticks = THROW_TICKS
        elif self.throw_ticks:
            self.throw_ticks -= 1

    def play_events(self, was_dead):
        events = self.game.events
        for name in dict.fromkeys(EVENT_SOUNDS[event] for event in events if event in EVENT_SOUNDS):
            if name != "coin" or self.busted_ticks is None:
                self.play_sound(name)
        if "death" in events:
            self.stop_theme()
            self.play_sound("fall")
        if "goal" in events and self.busted_ticks is None:
            self.stop_theme()
            self.play_sound("goal")
        if was_dead and not self.game.player.dead and self.busted_ticks is None:
            self.play_theme()

    def step(self, keys):
        koopas_before = {koopa.seq: self.sprite_rect(koopa)
                         for koopa in self.game.sprites.active("koopa")}
        was_dead = self.game.player.dead
        if "r" in keys:
            self.flat_koopas = []
        self.game.step(keys)
        self.update_effects(koopas_before)
        self.play_events(was_dead)
        if was_dead and not self.game.player.dead:
            self.flat_koopas = []
        if self.connection:
            try:
                send_packet(self.connection, {"keys": keys, "state": self.game.state_hash()})
            except OSError:
                self.read_result()
                return
            if self.game.player.won or select.select([self.connection], [], [], 0)[0]:
                self.read_result()
            elif self.game.tick_count >= self.session_ticks:
                self.connection.close()
                self.connection = None

    def read_result(self):
        try:
            self.show_result(recv_packet(self.connection))
        except (OSError, ValueError):
            self.message = "Connection closed"
        self.connection.close()
        self.connection = None

    def show_result(self, packet):
        print(packet)
        if "flag" in packet:
            self.message = str(packet["flag"])
        elif packet.get("u_cheat"):
            self.message = "u_cheat"
            self.busted_ticks = BUSTED_TICKS
            self.stop_theme()
            self.play_sound("powerdown")
        else:
            self.message = "Session over"

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            if self.busted_ticks is not None:
                self.busted_ticks -= 1
                if self.busted_ticks <= 0:
                    running = False
            if self.goal_ticks is not None and self.busted_ticks is None:
                if self.goal_ticks < COIN_HOLD_TICKS + SMOKE_TICKS * len(self.smoke):
                    # Let Mario land while the coin goes up in smoke.
                    self.step([])
                self.goal_ticks += 1
                if self.goal_ticks >= GOAL_SOUND_TICKS:
                    running = False
            elif self.game.tick_count >= self.session_ticks:
                if self.message is None:
                    self.message = "Time up"
                    self.stop_theme()
                    self.play_sound("fall")
            else:
                self.step(self.keys())
                if self.game.player.won and self.busted_ticks is None:
                    self.goal_ticks = 0
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", nargs="?")
    parser.add_argument("port", type=int, nargs="?", default=DEFAULT_PORT)
    args = parser.parse_args()
    client = Client(args.host, args.port)
    client.run()


if __name__ == "__main__":
    main()
