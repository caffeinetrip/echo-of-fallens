import math

import pygame

from ..utils.elements import Element
from ..utils.game_math import advance

class Spark(Element):
    def __init__(self, pos, angle, size=(6, 1), speed=250, decay=3.0, color=(255, 255, 255), z=0):
        super().__init__()
        self.pos = list(pos)
        self.z = z
        self.angle = angle
        if len(size) == 2:
            size = (size[0], size[1], size[0], size[1])
        self.size = tuple(size)
        self.speed = speed
        self.decay = decay * self.speed
        self.color = color
        
        self.lifetime = 0
    
    def update(self, dt):
        self.speed -= self.decay * dt
        if self.speed <= 0:
            return True
        
        self.lifetime += 1
        if self.lifetime > 50:
            return True
        
        advance(self.pos, self.angle, self.speed * dt)
        
    def generate_points(self, offset=(0, 0)):
        shifted_base = [self.pos[0] - offset[0], self.pos[1] - offset[1]]
        points = [
            advance(shifted_base.copy(), self.angle, self.speed * 0.01 * self.size[0]),
            advance(shifted_base.copy(), self.angle + math.pi * 0.5, self.speed * 0.01 * self.size[1]),
            advance(shifted_base.copy(), self.angle + math.pi, self.speed * 0.01 * self.size[2]),
            advance(shifted_base.copy(), self.angle - math.pi * 0.5, self.speed * 0.01 * self.size[3]),
        ]
        return points
    
    def render(self, surf, offset=(0, 0)):
        points = self.generate_points(offset=offset)
        pygame.draw.polygon(surf, self.color, points)
    
    def renderz(self, group='default', offset=(0, 0)):
        points = self.generate_points(offset=offset)
        self.e['Renderer'].renderf(pygame.draw.polygon, self.color, points, z=self.z, group=group)