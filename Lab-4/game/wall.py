import pygame

class Wall:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
