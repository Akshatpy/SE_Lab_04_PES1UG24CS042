import pygame

class Marble:
    def __init__(self, x, y, radius=12):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = 0
        self.vy = 0

    def rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
