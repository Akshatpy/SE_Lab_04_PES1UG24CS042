import pygame
from .marble import Marble
from .wall import Wall
from .sounds import Sounds

# Game Engine

WHITE = (255, 255, 255)
DARK = (40, 40, 50)
WALL_COLOR = (90, 90, 110)
GOAL_COLOR = (60, 200, 120)

# tilt strength, friction and time limit for each difficulty
DIFFICULTIES = {
    "Easy":   {"tilt": 0.8, "friction": 0.03, "time_ms": 60000},
    "Medium": {"tilt": 0.6, "friction": 0.02, "time_ms": 45000},
    "Hard":   {"tilt": 0.45, "friction": 0.01, "time_ms": 30000},
}
DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.marble = Marble(50, 50)
        self.max_speed = 9

        self.walls = self._build_maze()
        self.goal_x, self.goal_y, self.goal_radius = width - 60, height - 60, 22

        self.sounds = Sounds()
        self.difficulty = "Medium"
        self.state = "menu"  # "menu" or "playing"
        self.start_round(self.difficulty)
        self.state = "menu"

        self.font = pygame.font.SysFont("Arial", 26)
        self.big_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20)

    def start_round(self, difficulty):
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.tilt_strength = settings["tilt"]
        self.friction = settings["friction"]
        self.time_limit_ms = settings["time_ms"]

        self.marble = Marble(50, 50)
        self.start_ticks = pygame.time.get_ticks()
        self.game_over = False
        self.result = None  # "solved" or "timeout"
        self.finish_time_ms = None
        self.state = "playing"

    def _menu_button_rects(self):
        rects = []
        for i in range(len(DIFFICULTY_ORDER)):
            rects.append(pygame.Rect(self.width // 2 - 110, 200 + i * 65, 220, 50))
        return rects

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
        # movement is driven by the mouse position in handle_input,
        # events are only used for the menu and the end screen
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            elif self.state == "menu":
                keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2}
                if event.key in keys:
                    self.start_round(DIFFICULTY_ORDER[keys[event.key]])
            elif self.game_over and event.key in (pygame.K_r, pygame.K_RETURN):
                self.state = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "menu":
                for name, rect in zip(DIFFICULTY_ORDER, self._menu_button_rects()):
                    if rect.collidepoint(event.pos):
                        self.start_round(name)

    def handle_input(self):
        if self.state != "playing" or self.game_over:
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
        if self.state != "playing" or self.game_over:
            return

        elapsed = pygame.time.get_ticks() - self.start_ticks
        if elapsed >= self.time_limit_ms:
            self.game_over = True
            self.result = "timeout"
            self.sounds.play("timeout")
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
            self.sounds.play("win")

    def _resolve_wall_collisions(self):
        m = self.marble
        for wall in self.walls:
            rect = wall.rect()

            # closest point on the wall rect to the marble's centre
            cx = max(rect.left, min(m.x, rect.right))
            cy = max(rect.top, min(m.y, rect.bottom))
            dx = m.x - cx
            dy = m.y - cy
            dist_sq = dx * dx + dy * dy

            if dist_sq >= m.radius ** 2:
                continue

            if dist_sq > 0:
                dist = dist_sq ** 0.5
                nx, ny = dx / dist, dy / dist
                penetration = m.radius - dist
            else:
                # centre is inside the wall, push out through the nearest side
                left = m.x - rect.left
                right = rect.right - m.x
                top = m.y - rect.top
                bottom = rect.bottom - m.y
                smallest = min(left, right, top, bottom)
                if smallest == left:
                    nx, ny = -1, 0
                elif smallest == right:
                    nx, ny = 1, 0
                elif smallest == top:
                    nx, ny = 0, -1
                else:
                    nx, ny = 0, 1
                penetration = smallest + m.radius

            m.x += nx * penetration
            m.y += ny * penetration

            # only bounce if we're moving into the wall
            vn = m.vx * nx + m.vy * ny
            if vn < 0:
                if vn < -1.5:  # ignore tiny scrapes so it doesn't buzz
                    self.sounds.play("bounce")
                # remove the normal part and add back 0.3 of it reversed
                m.vx -= (1 + 0.3) * vn * nx
                m.vy -= (1 + 0.3) * vn * ny

    def _render_menu(self, screen):
        screen.fill(DARK)
        title = self.big_font.render("Marble Tilt Maze", True, WHITE)
        screen.blit(title, title.get_rect(center=(self.width // 2, 100)))
        sub = self.small_font.render("Pick a difficulty (click or press 1/2/3)", True, WHITE)
        screen.blit(sub, sub.get_rect(center=(self.width // 2, 160)))

        mouse = pygame.mouse.get_pos()
        for i, (name, rect) in enumerate(zip(DIFFICULTY_ORDER, self._menu_button_rects())):
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(screen, (110, 110, 140) if hover else WALL_COLOR, rect, border_radius=8)
            info = DIFFICULTIES[name]
            label = self.font.render(f"{i + 1}. {name}  ({info['time_ms'] // 1000}s)", True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))

        esc = self.small_font.render("ESC to quit", True, WHITE)
        screen.blit(esc, esc.get_rect(center=(self.width // 2, self.height - 30)))

    def render(self, screen):
        if self.state == "menu":
            self._render_menu(screen)
            return

        screen.fill(DARK)

        for wall in self.walls:
            pygame.draw.rect(screen, WALL_COLOR, wall.rect())

        pygame.draw.circle(screen, GOAL_COLOR, (self.goal_x, self.goal_y), self.goal_radius)
        pygame.draw.circle(screen, WHITE, (int(self.marble.x), int(self.marble.y)), self.marble.radius)

        elapsed = pygame.time.get_ticks() - self.start_ticks
        if self.result == "solved":
            elapsed = self.finish_time_ms  # keep the timer frozen after a win
        seconds_left = max(0, (self.time_limit_ms - elapsed) // 1000)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, WHITE)
        screen.blit(timer_text, (10, 10))

        if self.game_over:
            self._render_end_screen(screen)

    def _render_end_screen(self, screen):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))

        if self.result == "solved":
            title, color = "You solved it!", GOAL_COLOR
            detail = f"Finished in {self.finish_time_ms / 1000:.1f}s"
        else:
            title, color = "Time's up!", (220, 80, 80)
            detail = "The maze was not solved"

        lines = [
            (self.big_font, title, color, self.height // 2 - 60),
            (self.font, detail, WHITE, self.height // 2),
            (self.small_font, "Press R or ENTER to play again, ESC to quit", WHITE, self.height // 2 + 60),
        ]
        for font, text, col, y in lines:
            surf = font.render(text, True, col)
            screen.blit(surf, surf.get_rect(center=(self.width // 2, y)))
