"""
game.py - Gabriel Mukobi - 2019 04 18
A simple pygame game where the player avoids larger polygons
to stay alive and eats smaller polygons to grow.
"""

import math
from math import sqrt, sin, cos
import sys
import random
import pygame

# constants
FRAMERATE = 60
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

class Kinematics:
    """Data class to encapsulate information about movement"""
    def __init__(self, speed, position, friction, acceleration):
        self.speed = speed
        self.position = position
        self.friction = friction
        self.acceleration = acceleration

def length(vec):
    """Get the distance between 2 2D vectors"""
    return sqrt(vec[0] * vec[0] + vec[1] * vec[1])

class Actor:
    """Parent class for game actors"""
    # TODO add rotation
    def __init__(self, kinematics):
        self.kinematics = kinematics

    def accelerate(self):
        """Accelerate the actor"""

    def modify_speed(self):
        """Change the actor's speed"""
        self.kinematics.speed[0] *= self.kinematics.friction
        self.kinematics.speed[1] *= self.kinematics.friction

    def move(self):
        """Move the actor based on speed and acceleration"""
        self.accelerate()

        self.kinematics.speed[0] += self.kinematics.acceleration[0]
        self.kinematics.speed[1] += self.kinematics.acceleration[1]

        self.modify_speed()

        self.kinematics.position[0] = self.kinematics.position[0] + self.kinematics.speed[0]
        self.kinematics.position[1] = self.kinematics.position[1] + self.kinematics.speed[1]

    def draw(self):
        """Draw the actor"""


class PolygonActor(Actor):
    """Class for all enemies"""

    def __init__(self, kinematics, size, num_sides):
        super().__init__(kinematics)
        self.size = size
        self.num_sides = num_sides
        self.verts = []
        self.outline_color = [255, 255, 255]
        self.fill_color = [0, 0, 255]

    def generate_poly(self):
        """Populate the list verts with vertices of actor's polygon"""
        verts = []
        for i in range(0, self.num_sides):
            angle = 2.0 * math.pi / self.num_sides * i
            vert_x = self.size * cos(angle) + self.kinematics.position[0]
            vert_y = self.size * sin(angle) + self.kinematics.position[1]
            verts.append([vert_x, vert_y])
        self.verts = verts

    def draw(self):
        """Generate polygon geometry then draws shape accordingly"""
        self.generate_poly()
        pygame.draw.polygon(SCREEN, self.fill_color, self.verts)
        pygame.draw.aalines(SCREEN, self.outline_color, True, self.verts)

    def collides_with(self, other_polygon_actor):
        """Test if colliding with another polygon actor"""
        x_diff = self.kinematics.position[0] - other_polygon_actor.kinematics.position[0]
        y_diff = self.kinematics.position[1] - other_polygon_actor.kinematics.position[1]
        dist = sqrt(x_diff*x_diff + y_diff*y_diff)
        return dist < self.size + other_polygon_actor.size

class PlayerActor(PolygonActor):
    """Class for player character"""

    def accelerate(self):
        keys = pygame.key.get_pressed()
        acc_limit = 0.4
        self.kinematics.acceleration = [0, 0]
        if keys[pygame.K_LEFT]:
            self.kinematics.acceleration[0] -= acc_limit
        if keys[pygame.K_RIGHT]:
            self.kinematics.acceleration[0] += acc_limit
        if keys[pygame.K_UP]:
            self.kinematics.acceleration[1] -= acc_limit
        if keys[pygame.K_DOWN]:
            self.kinematics.acceleration[1] += acc_limit

        acc_mag = length(self.kinematics.acceleration)
        if acc_mag > acc_limit:
            self.kinematics.acceleration[0] = self.kinematics.acceleration[0] / acc_mag * acc_limit
            self.kinematics.acceleration[1] = self.kinematics.acceleration[1] / acc_mag * acc_limit

    def modify_speed(self):
        speed_limit = 8
        speed_mag = length(self.kinematics.speed)
        if speed_mag > speed_limit:
            self.kinematics.speed[0] = self.kinematics.speed[0] / speed_mag * speed_limit
            self.kinematics.speed[1] = self.kinematics.speed[1] / speed_mag * speed_limit

        super().modify_speed()

    def move(self):
        super().move()
        if self.kinematics.position[0] < self.size:
            self.kinematics.position[0] = self.size
        if self.kinematics.position[0] > WINDOW_WIDTH - self.size:
            self.kinematics.position[0] = WINDOW_WIDTH - self.size
        if self.kinematics.position[1] < self.size:
            self.kinematics.position[1] = self.size
        if self.kinematics.position[1] > WINDOW_HEIGHT - self.size:
            self.kinematics.position[1] = WINDOW_HEIGHT - self.size

class EnemyActor(PolygonActor):
    """Class for all enemies"""

    def __init__(self):
        """Spawn in enemy from a random edge witg random speed"""
        pos = [0, 0]
        spd = [0, 0]
        size = random.randint(1, 40)
        # choose a random edge
        edge = random.randint(0, 3)
        if edge == 0: # Left Edge
            pos = [-size, random.randint(0, WINDOW_HEIGHT)]
            spd = [1, 0]
        elif edge == 1:  # Right Edge
            pos = [WINDOW_WIDTH + size, random.randint(0, WINDOW_HEIGHT)]
            spd = [-1, 0]
        elif edge == 2: # Top Edge
            pos = [random.randint(0, WINDOW_WIDTH), -size]
            spd = [0, 1]
        elif edge == 3: # Bottom Edge
            pos = [random.randint(0, WINDOW_WIDTH), WINDOW_HEIGHT + size]
            spd = [0, -1]

        rand_speed = random.randint(20, 100)/60
        spd[0] *= rand_speed
        spd[1] *= rand_speed
        super().__init__(Kinematics(spd, pos, 1, [0, 0]), size, 5)


if __name__ == "__main__": # TODO refactor into function
    pygame.init()

    CLOCK = pygame.time.Clock()

    WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT

    SCREEN = pygame.display.set_mode(WINDOW_SIZE)

    PLAYER = PlayerActor(
        Kinematics([0, 0], [WINDOW_WIDTH/2, WINDOW_HEIGHT/2], 0.9, [0, 0]),
        4, 8
    )

    ENEMIES = []

    game_is_playing = True
    while game_is_playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        if random.randint(1, 50) == 1:
            ENEMIES.append(EnemyActor())


        SCREEN.fill([0, 0, 0])
        PLAYER.move()
        PLAYER.draw()

        for enemy in ENEMIES:
            enemy.move()
            enemy.draw()

        non_colliding_enemies = []
        for enemy in ENEMIES:
            if PLAYER.collides_with(enemy):
                if PLAYER.size > enemy.size:
                    PLAYER.size += 1
                else:
                    game_is_playing = False
            else:
                non_colliding_enemies.append(enemy)

        ENEMIES = non_colliding_enemies

        pygame.display.flip()

        CLOCK.tick(FRAMERATE)  # make sure game runs at correct framerate


    print("Game over")
    pygame.quit()
    # TODO game over
    