import pygame
import math
import random
import sys

pygame.init()

# ----------------------
# Game Configuration
# ----------------------
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 0.25       # Thrust acceleration
ROTATION_SPEED = 5        # Degrees per frame
BULLET_SPEED = 7
ASTEROID_MIN_SPEED = 1
ASTEROID_MAX_SPEED = 3
ASTEROID_SPAWN_COUNT = 5  # Number of asteroids to start with
ASTEROID_SIZE = 50        # Rough bounding size
BULLET_LIFETIME = 60      # Frames bullet stays alive

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroids Clone")
clock = pygame.time.Clock()

# ----------------------
# Helper Functions
# ----------------------
def wrap_position(pos):
    """
    Wrap an (x, y) position around the screen edges,
    and return a pygame.Vector2 to avoid tuple attribute errors.
    """
    v = pygame.Vector2(pos)  # Convert to Vector2 if not already
    v.x = v.x % WIDTH
    v.y = v.y % HEIGHT
    return v

def distance(pos1, pos2):
    """Euclidean distance between two points (x1, y1) and (x2, y2)."""
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# ----------------------
# Classes
# ----------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Represent the ship as a simple triangle
        #   Apex is at (15, 0)
        #   Other corners: (0, 30) and (30, 30)
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, WHITE, [(15, 0), (0, 30), (30, 30)])
        self.orig_image = self.image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        # Angle 0 means pointing "up" (the triangle apex is at (15,0)).
        self.angle = 0

    def update(self, keys_pressed):
        # Rotate left -> angle increases (CCW), Rotate right -> angle decreases (CW).
        if keys_pressed[pygame.K_LEFT]:
            self.angle += ROTATION_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            self.angle -= ROTATION_SPEED

        # Thrust forward
        if keys_pressed[pygame.K_UP]:
            rad_angle = math.radians(self.angle)
            # Move in the direction of the triangle's apex (which is "up" at angle=0)
            self.velocity.x += math.cos(rad_angle) * PLAYER_SPEED
            self.velocity.y -= math.sin(rad_angle) * PLAYER_SPEED

        # Update position and wrap
        self.position += self.velocity
        self.position = wrap_position(self.position)

        # Slight drag
        self.velocity *= 0.99

        # Rotate the image
        # pygame.transform.rotate(image, angle) rotates CCW for positive angle
        self.image = pygame.transform.rotate(self.orig_image, self.angle)
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

    def shoot(self):
        """Create a bullet from the player's current position and heading."""
        rad_angle = math.radians(self.angle)
        # Offset the bullet spawn point so it emerges from the ship's tip (apex).
        # The apex is roughly 15px above the center in local coordinates.
        # Feel free to tweak '15' to '20' or something else if you want it
        # slightly further in front of the ship.
        offset_distance = 15
        offset_x = math.cos(rad_angle) * offset_distance
        offset_y = -math.sin(rad_angle) * offset_distance

        bullet_pos = (self.position.x + offset_x, self.position.y + offset_y)
        bullet_vel = pygame.Vector2(math.cos(rad_angle), -math.sin(rad_angle)) * BULLET_SPEED
        return Bullet(bullet_pos, bullet_vel)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, vel):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(WHITE)
        # Ensure rect coordinates are integers
        self.rect = self.image.get_rect(center=(int(pos[0]), int(pos[1])))
        self.position = pygame.Vector2(pos)
        self.velocity = vel
        self.lifetime = BULLET_LIFETIME

    def update(self):
        # Move bullet
        self.position += self.velocity
        self.position = wrap_position(self.position)
        self.rect.center = (int(self.position.x), int(self.position.y))
        # Decrement lifetime and kill when done
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, pos=None, size=ASTEROID_SIZE):
        super().__init__()
        # Represent the asteroid as a circle
        self.size = size
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, WHITE, (size//2, size//2), size//2)
        self.rect = self.image.get_rect()

        if pos is None:
            # Random spawn location
            self.position = pygame.Vector2(random.randrange(WIDTH),
                                           random.randrange(HEIGHT))
        else:
            self.position = pygame.Vector2(pos)

        # Random velocity
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(ASTEROID_MIN_SPEED, ASTEROID_MAX_SPEED)
        self.velocity = pygame.Vector2(
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )

        self.rect.center = (int(self.position.x), int(self.position.y))

    def update(self):
        self.position += self.velocity
        self.position = wrap_position(self.position)
        self.rect.center = (int(self.position.x), int(self.position.y))

# ----------------------
# Main Game Loop
# ----------------------
def main():
    player = Player(WIDTH // 2, HEIGHT // 2)
    player_group = pygame.sprite.GroupSingle(player)

    bullets_group = pygame.sprite.Group()
    asteroids_group = pygame.sprite.Group()

    # Spawn initial asteroids
    for _ in range(ASTEROID_SPAWN_COUNT):
        asteroids_group.add(Asteroid())

    running = True
    while running:
        clock.tick(FPS)
        screen.fill(BLACK)

        # Event handling
        keys_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or keys_pressed[pygame.K_ESCAPE]:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Shoot bullet
                    bullet = player.shoot()
                    bullets_group.add(bullet)

        # Update sprites
        player_group.update(keys_pressed)
        bullets_group.update()
        asteroids_group.update()

        # Collision detection between bullets and asteroids
        for bullet in bullets_group:
            hit_asteroids = pygame.sprite.spritecollide(bullet, asteroids_group, True)
            if hit_asteroids:
                bullet.kill()
                # Optionally spawn smaller asteroids here

        # Collision detection between player and asteroids
        if pygame.sprite.spritecollideany(player, asteroids_group):
            print("You were hit by an asteroid! Game Over.")
            running = False

        # Draw everything
        player_group.draw(screen)
        bullets_group.draw(screen)
        asteroids_group.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
