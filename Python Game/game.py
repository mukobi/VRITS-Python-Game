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
import pygame

# constants
FRAMERATE = 60
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PLAYER_ACC_LIMIT = 0.4
PLAYER_INIT_SIZE = 6
PLAYER_INIT_SIDES = 6
PLAYER_INIT_FRICTION = 0.9
PLAYER_SPEED_LIMIT = 12
FRAMES_PER_ENEMY_SPAWN = 50
ENEMY_MAX_SIZE_SCALE = 3
ENEMY_SPEED_MIN = 20
ENEMY_SPEED_MAX = 200
ENEMY_BIG_COLOR_CODE = 4
ENEMY_SMALL_COLOR_CODE = 3
POLY_ROTATION_MAX = 1.0 * math.pi
POLY_MAX_SIDES = 10


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
    """Get the distance between 2 2D vectors"""
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
        """Draw the actor"""


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
        for vert in self.sprite_data.verts:
            blue_code = self.screen.get_at((int(vert[0]), int(vert[1])))[2]
            if blue_code == ENEMY_BIG_COLOR_CODE:
                # hit a bigger enemy
                return "DEAD"
            if blue_code == ENEMY_SMALL_COLOR_CODE:
                # hit a smaller enemy, figure out which one
                closest_enemy = enemies[0]
                min_square_dist = sys.maxsize
                for enemy in enemies:
                    enemy.update_color()
                    x_diff = enemy.move_data.position[0] - vert[0]
                    y_diff = enemy.move_data.position[1] - vert[1]
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
        size = random.randint(1, player_ref.sprite_data.size * ENEMY_MAX_SIZE_SCALE)
        # choose a random edge to spawn from
        edge = random.randint(0, 3)
        if edge == 0: # Left Edge
            pos = [-size, random.random() * WINDOW_HEIGHT]
            speed = [1, 0]
        elif edge == 1:  # Right Edge
            pos = [WINDOW_WIDTH + size, random.random() * WINDOW_HEIGHT]
            speed = [-1, 0]
        elif edge == 2: # Top Edge
            pos = [random.random() * WINDOW_WIDTH, -size]
            speed = [0, 1]
        elif edge == 3: # Bottom Edge
            pos = [random.random() * WINDOW_WIDTH, WINDOW_HEIGHT + size]
            speed = [0, -1]

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

def main():
    """Main game execution function"""
    # set up game and variables
    pygame.init()
    clock = pygame.time.Clock()
    window_size = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode(window_size)
    frames_per_enemy_spawn = FRAMES_PER_ENEMY_SPAWN

    player = PlayerActor(
        MoveData(speed=[0, 0], position=[WINDOW_WIDTH/2, WINDOW_HEIGHT/2],
                 acceleration=[0, 0], friction=PLAYER_INIT_FRICTION),
        SpriteData(size=PLAYER_INIT_SIZE, num_sides=PLAYER_INIT_SIDES,
                   outline_color=[0, 0, 212], fill_color=[0, 0, 212]),
        screen
    )
    enemies = []

    # main game loop
    game_is_playing = True
    while game_is_playing:
        # handle quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        # spawn enemies
        if random.randint(1, frames_per_enemy_spawn) == 1:
            enemies.append(EnemyActor(player, screen))

        # move and draw actors
        screen.fill([0, 0, 40])  # tint screen a little blue
        player.move()
        player.draw()
        for enemy in enemies:
            enemy.move()
            enemy.draw()

        # collision detection
        collision = player.check_collision(enemies)
        game_is_playing = collision != "DEAD"
        if collision == "EAT":
            # TODO track score
            pass

        pygame.display.flip()  # clear screen
        clock.tick(FRAMERATE)  # make sure game runs at correct framerate

    print("Game over")
    pygame.quit()
    # TODO game over


if __name__ == "__main__":
    main()
    