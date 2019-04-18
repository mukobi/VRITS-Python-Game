"""
game.py - Gabriel Mukobi - 2019 04 18
A simple pygame game where the player avoids larger polygons
to stay alive and eats smaller polygons to grow.
"""

import math
from math import sqrt, sin, cos
import sys
import random
from dataclasses import dataclass, field
from typing import List
import os
import time
import pygame

# constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FRAMERATE = 60
PLAYER_INIT_SIZE = 6
PLAYER_INIT_SIDES = 6
PLAYER_INIT_FRICTION = 0.875
PLAYER_ACC_LIMIT = 0.8
PLAYER_SPEED_LIMIT = 24
FRAMES_PER_ENEMY_SPAWN_INIT = 50
FRAMES_PER_ENEMY_SPAWN_MIN = 20
ENEMY_SIZE_SCALE = 5
ENEMY_ANGLE_VARIANCE = 0.85
ENEMY_SPEED_MIN = 20
ENEMY_SPEED_MAX = 200
ENEMY_BIG_COLOR_CODE = 4
ENEMY_SMALL_COLOR_CODE = 3
POLY_ROTATION_MAX = 1.0 * math.pi
POLY_MAX_SIDES = 10
FONT_SIZE = 32
FONT_PATH = os.path.dirname(os.path.realpath(__file__)) + "/res/fonts/zorque.ttf"
BOOM_PATH = os.path.dirname(os.path.realpath(__file__)) + "/res/sounds/boom.wav"
CRUNCH_PATH = os.path.dirname(os.path.realpath(__file__)) + "/res/sounds/crunch.wav"
MUSIC_PATH = os.path.dirname(os.path.realpath(__file__)) + "/res/sounds/music.ogg"


@dataclass
class MoveData:
    """Data class to encapsulate information about movement"""
    speed: List[float]
    position: List[float]
    acceleration: List[float]
    friction: float
    rotation: float = 0.0
    rotation_rate: float = 0.0


@dataclass
class SpriteData:
    """Data class to encapsulate information about a polygon sprite"""
    size: int
    num_sides: int
    outline_color: List[int] = field(default_factory=list)
    fill_color: List[int] = field(default_factory=list)
    verts: List[float] = field(default_factory=list)

def length(vec):
    """Get the length of a 2D vector"""
    return sqrt(vec[0] * vec[0] + vec[1] * vec[1])

class Actor:
    """Parent class for all game actors"""
    def __init__(self, move_data):
        self.move_data = move_data

    def accelerate(self):
        """Accelerate the actor"""

    def modify_speed(self):
        """Change the actor's speed"""
        self.move_data.speed[0] *= self.move_data.friction
        self.move_data.speed[1] *= self.move_data.friction

    def move(self):
        """Move the actor based on speed and acceleration"""
        self.accelerate()

        self.move_data.speed[0] += self.move_data.acceleration[0]
        self.move_data.speed[1] += self.move_data.acceleration[1]

        self.modify_speed()

        self.move_data.position[0] = self.move_data.position[0] + self.move_data.speed[0]
        self.move_data.position[1] = self.move_data.position[1] + self.move_data.speed[1]

        self.move_data.rotation += self.move_data.rotation_rate
        self.move_data.rotation %= 2.0 * math.pi

    def draw(self):
        """Must Draw the actor"""


class PolygonActor(Actor):
    """Parent class defining polygon geometry"""
    def __init__(self, move_data, sprite_data, screen):
        super().__init__(move_data)
        self.sprite_data = sprite_data
        self.sprite_data.outline_color = [255, 255, 255]  # default white outline
        self.screen = screen

    def generate_poly(self):
        """Populate the list verts with vertices of actor's polygon"""
        verts = []
        for i in range(0, self.sprite_data.num_sides):
            angle = 2.0 * math.pi / self.sprite_data.num_sides * i + self.move_data.rotation
            vert_x = self.sprite_data.size * cos(angle) + self.move_data.position[0]
            vert_y = self.sprite_data.size * sin(angle) + self.move_data.position[1]
            verts.append([vert_x, vert_y])
        self.sprite_data.verts = verts

    def draw(self):
        """Generate polygon geometry then draws shape accordingly"""
        self.generate_poly()
        pygame.draw.polygon(
            self.screen, self.sprite_data.fill_color, self.sprite_data.verts)
        pygame.draw.aalines(
            self.screen, self.sprite_data.outline_color, True, self.sprite_data.verts)


class PlayerActor(PolygonActor):
    """Defines player behavior"""
    def accelerate(self):
        keys = pygame.key.get_pressed()
        self.move_data.acceleration = [0.0, 0.0]
        if keys[pygame.K_LEFT]:
            self.move_data.acceleration[0] -= PLAYER_ACC_LIMIT
        if keys[pygame.K_RIGHT]:
            self.move_data.acceleration[0] += PLAYER_ACC_LIMIT
        if keys[pygame.K_UP]:
            self.move_data.acceleration[1] -= PLAYER_ACC_LIMIT
        if keys[pygame.K_DOWN]:
            self.move_data.acceleration[1] += PLAYER_ACC_LIMIT

        acc_mag = length(self.move_data.acceleration)
        if acc_mag > PLAYER_ACC_LIMIT:
            self.move_data.acceleration[0] *= PLAYER_ACC_LIMIT / acc_mag
            self.move_data.acceleration[1] *= PLAYER_ACC_LIMIT / acc_mag

    def modify_speed(self):
        speed_mag = length(self.move_data.speed)
        if speed_mag > PLAYER_SPEED_LIMIT:
            self.move_data.speed[0] = self.move_data.speed[0] / speed_mag * PLAYER_SPEED_LIMIT
            self.move_data.speed[1] = self.move_data.speed[1] / speed_mag * PLAYER_SPEED_LIMIT

        super().modify_speed()

    def move(self):
        super().move()
        if self.move_data.position[0] < self.sprite_data.size:
            self.move_data.position[0] = self.sprite_data.size
        if self.move_data.position[0] > WINDOW_WIDTH - self.sprite_data.size:
            self.move_data.position[0] = WINDOW_WIDTH - self.sprite_data.size
        if self.move_data.position[1] < self.sprite_data.size:
            self.move_data.position[1] = self.sprite_data.size
        if self.move_data.position[1] > WINDOW_HEIGHT - self.sprite_data.size:
            self.move_data.position[1] = WINDOW_HEIGHT - self.sprite_data.size

    def check_collision(self, enemies):
        """Checks for collisions between player and enemies
        Returns a string describing the resulting collision info"""
        # check all player points to see if on enemy pixel
        points_to_check = self.sprite_data.verts + [self.move_data.position]
        for i in range(0, 12):
            angle = 2.0 * math.pi / 12 * i
            vert = [0, 0]
            vert[0] = self.sprite_data.size / 2 * cos(angle) + self.move_data.position[0]
            vert[1] = self.sprite_data.size / 2 * sin(angle) + self.move_data.position[1]
            points_to_check.append(vert)
        for point in points_to_check:
            blue_code = self.screen.get_at((int(point[0]), int(point[1])))[2]
            if blue_code == ENEMY_BIG_COLOR_CODE:
                # hit a bigger enemy
                return "DEAD"
            if blue_code == ENEMY_SMALL_COLOR_CODE:
                # hit a smaller enemy, figure out which one
                closest_enemy = enemies[0]
                min_square_dist = sys.maxsize
                for enemy in enemies:
                    enemy.update_color()
                    x_diff = enemy.move_data.position[0] - point[0]
                    y_diff = enemy.move_data.position[1] - point[1]
                    square_dist = x_diff * x_diff + y_diff * y_diff
                    if square_dist < min_square_dist:
                        closest_enemy = enemy
                        min_square_dist = square_dist
                # assume rotation and sides of eaten enemy
                self.move_data.rotation_rate = closest_enemy.move_data.rotation_rate
                self.sprite_data.num_sides = closest_enemy.sprite_data.num_sides
                self.sprite_data.size += 1  # grow player
                enemies.remove(closest_enemy)
                return "EAT"
        return "NONE"


class EnemyActor(PolygonActor):
    """Defines enemy behavior"""
    def __init__(self, player_ref, screen):
        """Spawn in enemy from a random edge witg random speed"""
        pos = [0, 0]
        speed = [0, 0]
        size = random.randint(
            int(player_ref.sprite_data.size / ENEMY_SIZE_SCALE),
            int(player_ref.sprite_data.size * ENEMY_SIZE_SCALE))
        size = 4 if size < 4 else size
        # choose a random edge to spawn from
        edge = random.randint(0, 3)
        if edge == 0: # Left Edge
            pos = [-size, random.random() * WINDOW_HEIGHT]
            speed = [1, ENEMY_ANGLE_VARIANCE * (random.random() * 2 - 1)]
        elif edge == 1:  # Right Edge
            pos = [WINDOW_WIDTH + size, random.random() * WINDOW_HEIGHT]
            speed = [-1, ENEMY_ANGLE_VARIANCE * (random.random() * 2 - 1)]
        elif edge == 2: # Top Edge
            pos = [random.random() * WINDOW_WIDTH, -size]
            speed = [ENEMY_ANGLE_VARIANCE * (random.random() * 2 - 1), 1]
        elif edge == 3: # Bottom Edge
            pos = [random.random() * WINDOW_WIDTH, WINDOW_HEIGHT + size]
            speed = [ENEMY_ANGLE_VARIANCE * (random.random() * 2 - 1), -1]

        rand_speed = random.randint(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)/FRAMERATE
        speed[0] *= rand_speed
        speed[1] *= rand_speed
        num_sides = random.randint(3, POLY_MAX_SIDES)
        rotation_rate = random.randint(
            int(-POLY_ROTATION_MAX), int(POLY_ROTATION_MAX)) / FRAMERATE
        super().__init__(
            MoveData(speed=speed, position=pos, acceleration=[0.0, 0.0], friction=1,
                     rotation=0, rotation_rate=rotation_rate),
            SpriteData(size=size, num_sides=num_sides, fill_color=[0, 0, 0]),
            screen
        )
        self.player_ref = player_ref
        self.update_color()

    def update_color(self):
        """Updates the enemy color based on its size relative to the player"""
        p_size = self.player_ref.sprite_data.size
        e_size = self.sprite_data.size
        # set appropriate color and embed code into blue value of bigger or smaller
        if e_size > p_size:
            # enemy is bigger than player, make shade of red
            self.sprite_data.fill_color = [255 * p_size / e_size, 0, ENEMY_BIG_COLOR_CODE]
        else:
            # enemy is smaller than player, make shade of green
            self.sprite_data.fill_color = [0, 255 * e_size / p_size, ENEMY_SMALL_COLOR_CODE]


class Explosion():
    """For making explosions in collision"""
    def __init__(self, move_data, sprite_data, n_particles, screen, duration, max_speed):
        self.move_data = move_data
        self.sprite_data = sprite_data
        self.screen = screen
        self.start_time = time.time()
        self.duration = duration
        self.max_speed = max_speed
        self.particles = []  # list of PolygonActors
        for i in range(0, n_particles):  # number of particles
            speed = [max_speed * (random.random() * 2 - 1),
                        max_speed * (random.random() * 2 - 1)]
            friction = 0.8
            particle = PolygonActor(
                MoveData(
                    speed=speed,
                    position=self.move_data.position,
                    acceleration=self.move_data.acceleration,
                    friction=friction
                ),
                SpriteData(size=1, num_sides=3, fill_color=self.sprite_data.fill_color),
                screen
            )
            self.particles.append(particle)

    def update(self):
        """Check time, return if still exploding"""
        for particle in self.particles:
            particle.move()
        if time.time() > self.start_time + self.duration:
            self.particles = []
            return False
        return True

    def draw(self):
        """Draws all particles"""
        for particle in self.particles:
            particle.draw()



@dataclass
class GameData:
    """Data class to encapsulate information about the state of the game"""
    clock: pygame.time.Clock
    screen: pygame.surface
    window_tint: List[int]
    font_color: List[int]
    score: int
    player: PlayerActor
    enemies: List[EnemyActor]
    font_large: pygame.font
    font_small: pygame.font
    crunch_sound: pygame.mixer.Sound
    boom_sound: pygame.mixer.Sound
    explosions: List[Explosion]


def quit_game():
    """Quit the pygame"""
    pygame.quit()
    quit()

def title_screen_loop(game_data):
    """Interaction loop for the title screen"""
    while True:
        # spawn enemies
        frames_per_enemy_spawn = int(FRAMES_PER_ENEMY_SPAWN_INIT - (game_data.score / 2))
        if frames_per_enemy_spawn < FRAMES_PER_ENEMY_SPAWN_MIN:
            frames_per_enemy_spawn = frames_per_enemy_spawn
        if random.randint(1, frames_per_enemy_spawn) == 1:
            game_data.enemies.append(EnemyActor(game_data.player, game_data.screen))

        # move and draw game objects
        game_data.screen.fill([0, 0, 0])
        for enemy in game_data.enemies:
            enemy.move()
            enemy.sprite_data.fill_color = [255, 255, 255]
            enemy.draw()

        text0 = game_data.font_large.render("Polygonner!", True, [200, 200, 200])
        text1 = game_data.font_small.render(
            "Eat the smaller polygons to grow larger", True, [100, 255, 100])
        text2 = game_data.font_small.render(
            "Avoid the larger ones, or you'll be a gonner", True, [255, 100, 100])
        text3 = game_data.font_small.render(
            "Arrow keys to move, Enter to start, Esc to quit", True, [200, 200, 200])
        game_data.screen.blit(text0,
                              ((WINDOW_WIDTH - text0.get_width()) / 2,
                               (WINDOW_HEIGHT - 4 * text0.get_height()) / 2))
        game_data.screen.blit(text1,
                              ((WINDOW_WIDTH - text1.get_width()) / 2,
                               (WINDOW_HEIGHT - 2 * text1.get_height()) / 2))
        game_data.screen.blit(text2,
                              ((WINDOW_WIDTH - text2.get_width()) / 2,
                               (WINDOW_HEIGHT + 0 * text2.get_height()) / 2))
        game_data.screen.blit(text3,
                              ((WINDOW_WIDTH - text3.get_width()) / 2,
                               (WINDOW_HEIGHT + 2 * text3.get_height()) / 2))

        pygame.display.flip()  # clear screen
        game_data.clock.tick(FRAMERATE)  # make sure game runs at correct framerate

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            return  # start the game
        if keys[pygame.K_ESCAPE]:
            quit_game()  # quit the game

        # handle quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

def gameplay_loop(game_data):
    """Main loop for playing the game"""
    game_is_playing = True
    while True:
        # spawn enemies
        frames_per_enemy_spawn = int(FRAMES_PER_ENEMY_SPAWN_INIT - (game_data.score / 2))
        if frames_per_enemy_spawn < FRAMES_PER_ENEMY_SPAWN_MIN:
            frames_per_enemy_spawn = frames_per_enemy_spawn
        if random.randint(1, frames_per_enemy_spawn) == 1:
            game_data.enemies.append(EnemyActor(game_data.player, game_data.screen))

        game_data.screen.fill(game_data.window_tint)

        if game_is_playing:
            # move and draw player
            for explosion in game_data.explosions:
                explosion.update()
                explosion.draw()
                # if not explosion.update():
                #     game_data.explosions.remove(explosion)
            game_data.player.move()
            game_data.player.draw()
            for enemy in game_data.enemies:
                enemy.move()
                enemy.draw()

            # collision detection
            collision = game_data.player.check_collision(game_data.enemies)
            if collision == "DEAD":
                game_is_playing = False
                game_data.boom_sound.play()
                game_data.explosions.append(
                    Explosion(
                        game_data.player.move_data,
                        game_data.player.sprite_data,
                        32,
                        game_data.screen,
                        1000,
                        max_speed=10
                    )
                )

            elif collision == "EAT":
                game_data.crunch_sound.play()
                # shuffle screen and font color
                game_data.window_tint = game_data.window_tint[1:] + [game_data.window_tint[0]]
                game_data.font_color = game_data.font_color[1:] + [game_data.font_color[0]]
                game_data.score += 1
                game_data.explosions.append(
                    Explosion(
                        game_data.player.move_data,
                        game_data.player.sprite_data,
                        32,
                        game_data.screen,
                        1000,
                        max_speed=10
                    )
                )
        else:
            # game is over, show game over screen
            for enemy in game_data.enemies:
                enemy.move()
                enemy.draw()
            game_data.window_tint = [0, 0, 0]
            text0 = game_data.font_large.render("Game Over!", True, [255, 100, 100])
            text1 = game_data.font_small.render(
                "Enter to restart, Esc to quit", True, [100, 255, 100])

            game_data.screen.blit(text0,
                                  ((WINDOW_WIDTH - text0.get_width()) / 2,
                                   (WINDOW_HEIGHT - 2 * text0.get_height()) / 2))
            game_data.screen.blit(text1,
                                  ((WINDOW_WIDTH - text1.get_width()) / 2,
                                   (WINDOW_HEIGHT + 0 * text1.get_height()) / 2))

            keys = pygame.key.get_pressed()
            if keys[pygame.K_RETURN]:
                # restart the game
                game_data = initialize_game_data()
                game_is_playing = True
                pygame.mixer.music.rewind()
            if keys[pygame.K_ESCAPE]:
                quit_game()  # quit the game

        score_text = game_data.font_large.render(
            "Score: {}00".format(game_data.score), True, game_data.font_color)
        game_data.screen.blit(score_text, (WINDOW_WIDTH - score_text.get_width() - 16, 16))

        pygame.display.flip()  # clear screen
        game_data.clock.tick(FRAMERATE)  # make sure game runs at correct framerate
        # handle quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

def initialize_game_data():
    """Returns an initialized GameData object"""
    window_size = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode(window_size)
    game_data = GameData(
        clock=pygame.time.Clock(),
        screen=screen,
        window_tint=[35, 15, 70],
        font_color=[100, 100, 240],
        score=0,
        font_large=pygame.font.Font(FONT_PATH, FONT_SIZE),
        font_small=pygame.font.Font(FONT_PATH, int(FONT_SIZE * 2 / 3)),
        enemies=[],
        player=PlayerActor(
            MoveData(speed=[0, 0], position=[WINDOW_WIDTH/2, WINDOW_HEIGHT/2],
                     acceleration=[0, 0], friction=PLAYER_INIT_FRICTION),
            SpriteData(size=PLAYER_INIT_SIZE, num_sides=PLAYER_INIT_SIDES,
                       outline_color=[21, 121, 212], fill_color=[21, 121, 212]),
            screen
        ),
        crunch_sound=pygame.mixer.Sound(CRUNCH_PATH),
        boom_sound=pygame.mixer.Sound(BOOM_PATH),
        explosions=[]
    )
    game_data.crunch_sound.set_volume(0.45)
    return game_data

def main():
    """Main game execution function"""
    # set up game and variables
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.mixer.init()
    pygame.init()
    game_data = initialize_game_data()
    pygame.display.set_caption("Polygonner!")

    pygame.mixer.music.load(MUSIC_PATH)
    pygame.mixer.music.play(-1)

    title_screen_loop(game_data)

    game_data = initialize_game_data()  # reset game before start of playing
    gameplay_loop(game_data)


if __name__ == "__main__":
    main()
    