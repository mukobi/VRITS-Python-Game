import math
from math import sqrt, sin, cos
import sys
import random
import pygame

# constants
FRAMERATE = 60
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600


def length(vec):
    """Get the distance between 2 2D vectors"""
    return sqrt(vec[0] * vec[0] + vec[1] * vec[1])

class Actor:
    """Parent class for game actors"""

    def __init__(self, speed, position, friction):
        self.speed = speed
        self.position = position
        self.friction = friction
        self.acceleration = [0, 0]

    def accelerate(self):
        """Accelerate the actor"""
        return

    def modify_speed(self):
        """Change the actor's speed"""
        self.speed[0] *= self.friction
        self.speed[1] *= self.friction
        return

    def move(self):
        """Move the actor based on speed and acceleration"""
        self.accelerate()

        self.speed[0] += self.acceleration[0]
        self.speed[1] += self.acceleration[1]

        self.modify_speed()

        self.position[0] = self.position[0] + self.speed[0]
        self.position[1] = self.position[1] + self.speed[1]

    def draw(self):
        """Draw the actor"""
        return


class PolygonActor(Actor):
    def __init__(self, speed, position, friction, size, num_sides):
        super().__init__(speed, position, friction)
        self.size = size
        self.num_sides = num_sides
        self.verts = []

    def generate_poly(self):
        verts = []
        for i in range(0, self.num_sides):
            angle = 2.0 * math.pi / self.num_sides * i
            vert_x = self.size * cos(angle) + self.position[0]
            vert_y = self.size * sin(angle) + self.position[1]
            verts.append([vert_x, vert_y])
        self.verts = verts

    def draw(self):
        self.generate_poly()
        pygame.draw.aalines(SCREEN, [255, 255, 255], True, self.verts)
        pygame.draw.polygon(SCREEN, [255, 255, 255], self.verts)

    def collides_with(self, other_polygon_actor):
        x_diff = self.position[0] - other_polygon_actor.position[0]
        y_diff = self.position[1] - other_polygon_actor.position[1]
        dist = sqrt(x_diff*x_diff + y_diff*y_diff)
        return dist < self.size + other_polygon_actor.size

class PlayerActor(PolygonActor):
    def accelerate(self):
        keys = pygame.key.get_pressed()
        acc_limit = 0.4
        self.acceleration = [0, 0]
        if keys[pygame.K_LEFT]:
            self.acceleration[0] -= acc_limit
        if keys[pygame.K_RIGHT]:
            self.acceleration[0] += acc_limit
        if keys[pygame.K_UP]:
            self.acceleration[1] -= acc_limit
        if keys[pygame.K_DOWN]:
            self.acceleration[1] += acc_limit

        acc_mag = length(self.acceleration)
        if acc_mag > acc_limit:
            self.acceleration[0] = self.acceleration[0] / acc_mag * acc_limit
            self.acceleration[1] = self.acceleration[1] / acc_mag * acc_limit

    def modify_speed(self):
        speed_limit = 8
        speed_mag = length(self.speed)
        if speed_mag > speed_limit:
            self.speed[0] = self.speed[0] / speed_mag * speed_limit
            self.speed[1] = self.speed[1] / speed_mag * speed_limit

        super().modify_speed()

    def move(self):
        super().move()
        if self.position[0] < self.size:
            self.position[0] = self.size
        if self.position[0] > WINDOW_WIDTH - self.size:
            self.position[0] = WINDOW_WIDTH - self.size
        if self.position[1] < self.size:
            self.position[1] = self.size
        if self.position[1] > WINDOW_HEIGHT - self.size:
            self.position[1] = WINDOW_HEIGHT - self.size

class EnemyActor(PolygonActor):
    def __init__(self):
        """Spawn in enemy from a random edge witg random speed"""
        pos = [0, 0]
        spd = [0, 0]
        size = random.randint(1, 40)
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
        super().__init__(spd, pos, 1, size, 5)


if __name__ == "__main__":
    pygame.init()

    CLOCK = pygame.time.Clock()

    WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT

    SCREEN = pygame.display.set_mode(WINDOW_SIZE)

    PLAYER = PlayerActor([0, 0], [WINDOW_WIDTH/2, WINDOW_HEIGHT/2], 0.9, 4, 8)

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

    while 1:
        CLOCK.tick(FRAMERATE)
        continue