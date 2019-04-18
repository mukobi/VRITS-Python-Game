"""
game.py - Gabriel Mukobi - 2019 04 18
A simple pygame game where the player avoids larger polygons
to stay alive and eats smaller polygons to grow.
"""

import math
from math import sqrt, sin, cos
import sys
import random
from dataclasses import dataclass
from typing import List
import pygame

# constants
FRAMERATE = 60
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

@dataclass
class MoveData:
    """Data class to encapsulate information about movement"""
    speed: List[float]
    position: List[float]
    acceleration: List[float]
    friction: float

@dataclass
class SpriteData:
    """Data class to encapsulate information about movement"""
    speed: List[float]
    position: List[float]
    acceleration: List[float]
    friction: float

def length(vec):
    """Get the distance between 2 2D vectors"""
    return sqrt(vec[0] * vec[0] + vec[1] * vec[1])

class Actor:
    """Parent class for game actors"""
    # TODO add rotation
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

    def draw(self):
        """Draw the actor"""


class PolygonActor(Actor):
    """Class for all enemies"""

    def __init__(self, move_data, size, num_sides, screen):
        super().__init__(move_data)
        self.size = size
        self.num_sides = num_sides
        self.verts = []
        self.outline_color = [255, 255, 255]
        self.fill_color = [0, 0, 255]
        self.screen = screen

    def generate_poly(self):
        """Populate the list verts with vertices of actor's polygon"""
        verts = []
        for i in range(0, self.num_sides):
            angle = 2.0 * math.pi / self.num_sides * i
            vert_x = self.size * cos(angle) + self.move_data.position[0]
            vert_y = self.size * sin(angle) + self.move_data.position[1]
            verts.append([vert_x, vert_y])
        self.verts = verts

    def draw(self):
        """Generate polygon geometry then draws shape accordingly"""
        self.generate_poly()
        pygame.draw.polygon(self.screen, self.fill_color, self.verts)
        pygame.draw.aalines(self.screen, self.outline_color, True, self.verts)

    def collides_with(self, other_polygon_actor):
        """Test if colliding with another polygon actor"""
        x_diff = self.move_data.position[0] - other_polygon_actor.move_data.position[0]
        y_diff = self.move_data.position[1] - other_polygon_actor.move_data.position[1]
        dist = sqrt(x_diff*x_diff + y_diff*y_diff)
        return dist < self.size + other_polygon_actor.size

class PlayerActor(PolygonActor):
    """Class for player character"""

    def accelerate(self):
        keys = pygame.key.get_pressed()
        acc_limit = 0.4
        self.move_data.acceleration = [0.0, 0.0]
        if keys[pygame.K_LEFT]:
            self.move_data.acceleration[0] -= acc_limit
        if keys[pygame.K_RIGHT]:
            self.move_data.acceleration[0] += acc_limit
        if keys[pygame.K_UP]:
            self.move_data.acceleration[1] -= acc_limit
        if keys[pygame.K_DOWN]:
            self.move_data.acceleration[1] += acc_limit

        acc_mag = length(self.move_data.acceleration)
        if acc_mag > acc_limit:
            self.move_data.acceleration[0] = self.move_data.acceleration[0] / acc_mag * acc_limit
            self.move_data.acceleration[1] = self.move_data.acceleration[1] / acc_mag * acc_limit

    def modify_speed(self):
        speed_limit = 8
        speed_mag = length(self.move_data.speed)
        if speed_mag > speed_limit:
            self.move_data.speed[0] = self.move_data.speed[0] / speed_mag * speed_limit
            self.move_data.speed[1] = self.move_data.speed[1] / speed_mag * speed_limit

        super().modify_speed()

    def move(self):
        super().move()
        if self.move_data.position[0] < self.size:
            self.move_data.position[0] = self.size
        if self.move_data.position[0] > WINDOW_WIDTH - self.size:
            self.move_data.position[0] = WINDOW_WIDTH - self.size
        if self.move_data.position[1] < self.size:
            self.move_data.position[1] = self.size
        if self.move_data.position[1] > WINDOW_HEIGHT - self.size:
            self.move_data.position[1] = WINDOW_HEIGHT - self.size

class EnemyActor(PolygonActor):
    """Class for all enemies"""

    def __init__(self, player_ref, screen):
        """Spawn in enemy from a random edge witg random speed"""
        pos = [0, 0]
        spd = [0, 0]
        size = random.randint(1, 40)
        # choose a random edge
        edge = random.randint(0, 3)
        if edge == 0: # Left Edge
            pos = [-size, random.random() * WINDOW_HEIGHT]
            spd = [1, 0]
        elif edge == 1:  # Right Edge
            pos = [WINDOW_WIDTH + size, random.random() * WINDOW_HEIGHT]
            spd = [-1, 0]
        elif edge == 2: # Top Edge
            pos = [random.random() * WINDOW_WIDTH, -size]
            spd = [0, 1]
        elif edge == 3: # Bottom Edge
            pos = [random.random() * WINDOW_WIDTH, WINDOW_HEIGHT + size]
            spd = [0, -1]

        rand_speed = random.randint(20, 100)/60
        spd[0] *= rand_speed
        spd[1] *= rand_speed
        super().__init__(MoveData(spd, pos, [0.0, 0.0], 1), size, 5, screen)
        self.player_ref = player_ref
        self.update_color()

    def update_color(self):
        """Updates the enemy color based on its size relative to the player"""
        #size_dif = self.player_ref.move_data.


def main():
    """Main game runtime function"""

    pygame.init()

    clock = pygame.time.Clock()

    window_size = WINDOW_WIDTH, WINDOW_HEIGHT

    screen = pygame.display.set_mode(window_size)

    player = PlayerActor(
        MoveData([0, 0], [WINDOW_WIDTH/2, WINDOW_HEIGHT/2], [0, 0], 0.9),
        4, 8, screen
    )

    enemies = []

    game_is_playing = True
    while game_is_playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if random.randint(1, 50) == 1:
            enemies.append(EnemyActor(player, screen))


        screen.fill([0, 0, 0])
        player.move()
        player.draw()

        for enemy in enemies:
            enemy.move()
            enemy.draw()

        non_colliding_enemies = []
        for enemy in enemies:
            if player.collides_with(enemy):
                if player.size > enemy.size:
                    player.size += 1
                else:
                    game_is_playing = False
            else:
                non_colliding_enemies.append(enemy)

        enemies = non_colliding_enemies

        pygame.display.flip()

        clock.tick(FRAMERATE)  # make sure game runs at correct framerate


    print("Game over")
    pygame.quit()
    # TODO game over


if __name__ == "__main__":
    main()
    