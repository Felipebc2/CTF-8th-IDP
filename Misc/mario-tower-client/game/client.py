import argparse
import os
import select
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from game import CHARACTER, map_path
from game.engine.simulation import Game, SCALE
from game.map_loading.tilemap import load
from game.network import connect, recv_packet, send_packet

SPRITES = Path(__file__).parent / "resources" / "sprites"
SOUNDS = Path(__file__).parent / "resources" / "sounds"
WIDTH, HEIGHT = 960, 640
GOAL_SOUND_TICKS = 606
FALL_SOUND_TICKS = 315
REJECTED_TICKS = 600
REJECTED_MESSAGE = "You can't do that.\nClosing in {}.."
DEFAULT_SESSION_SECONDS = 120


class Client:
    def __init__(self, host=None, port=None, character=CHARACTER):
        self.character = character
        self.game = Game(load(map_path(character)))
        pygame.init()
        self.window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption(f"{character.capitalize()} Tower")
        self.clock = pygame.time.Clock()
        self.images = self.load_character_images()
        self.status_font = pygame.font.Font(None, 36)
        self.load_environment()
        self.timer_images = self.load_timer_images()
        self.session_ticks = DEFAULT_SESSION_SECONDS * 60
        self.timeout_death_ticks = None
        self.timeout_death_position = None
        self.timeout_death_start_y = 0
        self.goal_coins = [
            pygame.transform.scale(
                pygame.image.load(SPRITES / f"goal_coin_{index}.png").convert_alpha(), (42, 66))
            for index in range(4)
        ]
        self.coins = [
            pygame.transform.scale(
                pygame.image.load(SPRITES / f"common_coin_{index}.png").convert_alpha(), (42, 56))
            for index in range(4)
        ]
        self.sounds = self.load_sounds()
        self.direction_sign = pygame.transform.scale(
            pygame.image.load(SPRITES / "direction_sign.png").convert_alpha(), (48, 48))
        self.rendered_platforms = ()
        self.connection = None
        self.rejected_ticks = None
        if host:
            self.show_status("Connecting...")
            self.connection = connect(host, port)
            self.show_status("Starting session...")
            initial = recv_packet(self.connection)
            if initial.get("character", self.character) != self.character:
                raise SystemExit(f"{host}:{port} is not a {character.capitalize()} Tower server")
            self.rendered_platforms = tuple(
                index for index in initial.get("rendered_platforms", ())
                if isinstance(index, int) and 0 <= index < len(self.game.world.platforms)
            )
            if isinstance(initial.get("session_ticks"), int) and initial["session_ticks"] > 0:
                self.session_ticks = initial["session_ticks"]
            self.show_status("Connected")
            pygame.time.delay(300)
        self.play_theme()

    def load_character_images(self):
        return {
            name: pygame.image.load(SPRITES / f"{self.character}_{name}.png").convert_alpha()
            for name in ("stand", "run", "run_1", "run_2", "jump", "fall", "death")
        }

    def load_environment(self):
        background = pygame.image.load(SPRITES / f"{self.character}_background.png").convert()
        self.background = pygame.transform.smoothscale(background, (WIDTH, HEIGHT))
        self.wall_tile = pygame.transform.smoothscale(
            pygame.image.load(SPRITES / f"{self.character}_stone.png").convert_alpha(), (32, 32))
        self.platform_cloud = pygame.transform.scale(
            pygame.image.load(SPRITES / f"{self.character}_platform_cloud.png").convert_alpha(), (32, 32))
        self.ground_tiles = [
            pygame.transform.smoothscale(
                pygame.image.load(SPRITES / f"{self.character}_ground_{index}.png").convert_alpha(), (32, 32))
            for index in range(6)
        ]

    def load_sounds(self):
        try:
            pygame.mixer.init()
            sounds = {
                name: pygame.mixer.Sound(SOUNDS / f"{name}.ogg")
                for name in ("jump", "fall", "coin", "goal", "powerdown")
            }
            for sound in sounds.values():
                sound.set_volume(0.35)
            return sounds
        except (pygame.error, FileNotFoundError):
            return {}

    def load_timer_images(self):
        images = {}
        for character in "0123456789":
            image = pygame.image.load(SPRITES / f"timer_{character}.png").convert_alpha()
            images[character] = pygame.transform.scale(image, (24, 24))
        return images

    def play_theme(self):
        if not pygame.mixer.get_init():
            return
        pygame.mixer.music.load(SOUNDS / f"{self.character}_theme.ogg")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

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
        if pressed[pygame.K_w] or pressed[pygame.K_UP] or pressed[pygame.K_SPACE]:
            keys.append("jump")
        if pressed[pygame.K_z] or pressed[pygame.K_LSHIFT]:
            keys.append("run")
        if pressed[pygame.K_r]:
            keys.append("r")
        return keys

    def camera_y(self):
        desired = self.game.player.y // SCALE - HEIGHT // 2
        return max(0, min(desired, self.game.world.height - HEIGHT))

    def draw_solid(self, rect, camera):
        is_ground = rect.y >= self.game.world.height - 64
        tile = self.wall_tile
        screen_rect = pygame.Rect(rect.x, rect.y - camera, rect.width, rect.height)
        old_clip = self.screen.get_clip()
        self.screen.set_clip(screen_rect)
        for x in range(rect.x, rect.x + rect.width, 32):
            for y in range(rect.y - (rect.y % 32), rect.y + rect.height, 32):
                if is_ground:
                    column = (x - rect.x) // 32
                    row = (y - rect.y) // 32
                    last_column = (rect.width - 1) // 32
                    if row == 0:
                        index = 0 if column == 0 else 2 if column == last_column else 1
                    else:
                        index = 3 if column == 0 else 5 if column == last_column else 4
                    image = self.ground_tiles[index]
                else:
                    image = tile
                self.screen.blit(image, (x, y - camera))
        self.screen.set_clip(old_clip)

    def draw_platform(self, rect, camera):
        x_offset = 0
        for solid in self.game.world.solids:
            if solid.x + solid.width == rect.x:
                x_offset = -2
            elif solid.x == rect.x + rect.width:
                x_offset = 2
        for x in range(rect.x, rect.x + rect.width, 32):
            self.screen.blit(self.platform_cloud, (x + x_offset, rect.y - camera))

    def draw_direction_sign(self, camera):
        spawn_x, spawn_y = self.game.world.spawn
        sign = self.direction_sign
        if self.game.goal.x < spawn_x:
            sign = pygame.transform.flip(sign, True, False)
        self.screen.blit(sign, (spawn_x + 32, spawn_y - camera - 20))

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

    def draw_timeout_death(self):
        sprite = pygame.transform.scale(self.images["death"], (40, 56))
        self.screen.blit(sprite, self.timeout_death_position)

    def start_timeout_death(self):
        camera = self.camera_y()
        self.timeout_death_ticks = 0
        self.timeout_death_position = [
            self.game.player.x // SCALE - 10,
            self.game.player.y // SCALE - camera - 28,
        ]
        self.timeout_death_start_y = self.timeout_death_position[1]
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.play_sound("fall")

    def draw(self):
        camera = self.camera_y()
        self.screen.blit(self.background, (0, 0))
        for solid in self.game.world.solids:
            self.draw_solid(solid, camera)
        for index in self.rendered_platforms:
            self.draw_platform(self.game.world.platforms[index], camera)
        self.draw_direction_sign(camera)
        self.draw_timer()
        goal_coin = self.goal_coins[(self.game.tick_count // 8) % len(self.goal_coins)]
        goal = self.game.goal
        x = goal.x + (goal.width - goal_coin.get_width()) // 2
        y = goal.y + (goal.height - goal_coin.get_height()) // 2 - camera
        self.screen.blit(goal_coin, (x, y))
        if self.game.coin and not self.game.coin_collected:
            coin = self.coins[(self.game.tick_count // 8) % len(self.coins)]
            area = self.game.coin
            x = area.x + (area.width - coin.get_width()) // 2
            y = area.y + (area.height - coin.get_height()) // 2 - camera
            self.screen.blit(coin, (x, y))
        if self.timeout_death_ticks is not None:
            self.draw_timeout_death()
        elif not self.game.player.dead:
            if not self.game.player.grounded:
                sprite = self.images["jump" if self.game.player.vy < 0 else "fall"]
            elif self.game.player.vx:
                frames = ("run", "run_1", "run_2", "run_1")
                sprite = self.images[frames[(self.game.tick_count // 6) % len(frames)]]
            else:
                sprite = self.images["stand"]
            sprite = pygame.transform.smoothscale(sprite, (40, 56))
            if self.game.player.facing > 0:
                sprite = pygame.transform.flip(sprite, True, False)
            self.screen.blit(sprite, (self.game.player.x // SCALE - 10,
                                      self.game.player.y // SCALE - camera - 28))
        if self.rejected_ticks is not None:
            seconds = -(-self.rejected_ticks // 60)
            self.draw_message(REJECTED_MESSAGE.format(seconds), (255, 210, 60))
        self.present()

    def step(self, keys):
        was_grounded = self.game.player.grounded
        was_won = self.game.player.won
        was_dead = self.game.player.dead
        had_coin = self.game.coin_collected
        self.game.step(keys)
        if was_grounded and not self.game.player.grounded and self.game.player.vy < 0:
            self.play_sound("jump")
        if not was_won and self.game.player.won:
            self.play_sound("goal")
        if not had_coin and self.game.coin_collected:
            self.play_sound("coin")
        if not was_dead and self.game.player.dead:
            self.play_sound("fall")
        if self.connection:
            try:
                send_packet(self.connection, {"keys": keys, "state": self.game.state_hash()})
            except OSError:
                self.read_result()
                return
            if self.game.player.won or select.select([self.connection], [], [], 0)[0]:
                self.read_result()

    def read_result(self):
        try:
            packet = recv_packet(self.connection)
        except (OSError, ValueError):
            packet = {}
        self.connection.close()
        self.connection = None
        print(packet)
        if packet.get("u_cheat"):
            self.rejected_ticks = REJECTED_TICKS
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            self.play_sound("powerdown")

    def run(self):
        running = True
        goal_ticks = None
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            if self.rejected_ticks is not None:
                self.rejected_ticks -= 1
                if self.rejected_ticks <= 0:
                    running = False
            elif goal_ticks is not None:
                goal_ticks += 1
                if goal_ticks >= GOAL_SOUND_TICKS:
                    running = False
            elif self.timeout_death_ticks is not None:
                self.timeout_death_ticks += 1
                progress = min(1, 2 * self.timeout_death_ticks / FALL_SOUND_TICKS)
                self.timeout_death_position[1] = (
                    self.timeout_death_start_y
                    + (HEIGHT + 56 - self.timeout_death_start_y) * progress * progress
                )
                if self.timeout_death_ticks >= FALL_SOUND_TICKS:
                    running = False
            else:
                self.step(self.keys())
                if self.rejected_ticks is None and self.game.player.won:
                    goal_ticks = 0
                elif self.rejected_ticks is None and self.game.tick_count >= self.session_ticks:
                    self.start_timeout_death()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("host", nargs="?")
    parser.add_argument("port", type=int, nargs="?")
    args = parser.parse_args()
    if args.host and args.port is None:
        parser.error("the port is required when a server is given")
    Client(args.host, args.port).run()


if __name__ == "__main__":
    main()
