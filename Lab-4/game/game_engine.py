import pygame
from .marble import Marble
from .wall import Wall

# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.marble = Marble(50, 50)
        self.tilt_strength = 0.6
        self.friction = 0.02
        self.max_speed = 9

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = width - 60, height - 60, 22

        self.time_limit_ms = 45000
        self.start_ticks = pygame.time.get_ticks()

        self.font = pygame.font.SysFont("Arial", 26)
        self.game_over = False
        self.result = None  # "solved" or "timeout"
        self.finish_time_ms = None

    def _build_maze(self):
        walls = []
        t = 16  # wall thickness

        # outer boundary
        walls.append(Wall(0, 0, self.width, t))
        walls.append(Wall(0, self.height - t, self.width, t))
        walls.append(Wall(0, 0, t, self.height))
        walls.append(Wall(self.width - t, 0, t, self.height))

        # a few internal walls forming a simple winding path
        walls.append(Wall(0, 140, self.width - 140, t))
        walls.append(Wall(140, 260, self.width - 140, t))
        walls.append(Wall(0, 380, self.width - 140, t))

        return walls

    def handle_event(self, event):
        # This game is driven entirely by the continuous mouse
        # position, handled in handle_input each frame.
        pass

    def handle_input(self):
        if self.game_over:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        dx = mouse_x - self.width // 2
        dy = mouse_y - self.height // 2
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        ax = (dx / dist) * self.tilt_strength
        ay = (dy / dist) * self.tilt_strength
        self.marble.vx += ax
        self.marble.vy += ay

    def update(self):
        if self.game_over:
            return

        elapsed = pygame.time.get_ticks() - self.start_ticks
        if elapsed >= self.time_limit_ms:
            self.game_over = True
            self.result = "timeout"
            return

        self.marble.vx *= (1 - self.friction)
        self.marble.vy *= (1 - self.friction)

        speed = (self.marble.vx ** 2 + self.marble.vy ** 2) ** 0.5
        if speed > self.max_speed:
            scale = self.max_speed / speed
            self.marble.vx *= scale
            self.marble.vy *= scale

        self.marble.x += self.marble.vx
        self.marble.y += self.marble.vy

        self._resolve_wall_collisions()

        gx = self.goal_x - self.marble.x
        gy = self.goal_y - self.marble.y
        if (gx ** 2 + gy ** 2) ** 0.5 <= self.goal_radius:
            self.game_over = True
            self.result = "solved"
            self.finish_time_ms = elapsed

    def _resolve_wall_collisions(self):
        for wall in self.walls:
            marble_rect = self.marble.rect()
            wall_rect = wall.rect()

            # NOTE: this checks a simple bounding-box overlap
            # (colliderect) between the marble's square bounding box
            # and the wall, instead of a true circle-vs-rectangle
            # distance test. Near a wall's corner, the marble's
            # bounding square can overlap the wall rect well before
            # the actual round marble visually touches it, causing an
            # early "phantom" bounce off empty space right next to
            # corners. See Task 1 in the README.
            if marble_rect.colliderect(wall_rect):
                overlap_x = min(marble_rect.right, wall_rect.right) - max(marble_rect.left, wall_rect.left)
                overlap_y = min(marble_rect.bottom, wall_rect.bottom) - max(marble_rect.top, wall_rect.top)

                if overlap_x < overlap_y:
                    if self.marble.x < wall_rect.centerx:
                        self.marble.x -= overlap_x
                    else:
                        self.marble.x += overlap_x
                    self.marble.vx *= -0.3
                else:
                    if self.marble.y < wall_rect.centery:
                        self.marble.y -= overlap_y
                    else:
                        self.marble.y += overlap_y
                    self.marble.vy *= -0.3

    def render(self, screen):
        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        elapsed = pygame.time.get_ticks() - self.start_ticks
        seconds_left = max(0, (self.time_limit_ms - elapsed) // 1000)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, WHITE)
        screen.blit(timer_text, (10, 10))

        if self.game_over and not getattr(self, "_game_over_logged", False):
            # NOTE: no proper end screen yet - see Task 2 in the README.
            if self.result == "solved":
                print(f"Solved! Finished in {self.finish_time_ms / 1000:.1f}s")
            else:
                print("Time's up! Maze not solved.")
            self._game_over_logged = True
