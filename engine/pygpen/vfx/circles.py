import math

import pygame

from ..utils.elements import Element
from ..utils.game_math import normalize

class Circle(Element):
    def __init__(self, pos, velocity=150, decay=1.0, width=6, radius=0, color=(255, 255, 255), z=0):
        super().__init__()
        self.pos = list(pos)
        self.z = z
        self.init_velocity = velocity
        self.velocity = velocity
        self.decay = decay * velocity
        self.width = width
        self.radius = radius
        self.color = color
        
    def update(self, dt):
        self.radius += self.velocity * dt
        self.velocity = normalize(self.velocity, self.decay * dt)
        if (self.radius < 0) or (self.velocity == 0):
            return True
        
    def args(self, offset=(0, 0)):
        return (self.color, (int(self.pos[0] - offset[0]), int(self.pos[1] - offset[1])), int(self.radius), math.ceil(self.width * (self.velocity / self.init_velocity)))
        
    def render(self, surf, offset=(0, 0)):
        pygame.draw.circle(surf, self.color, *self.args(offset=offset))
        
    def renderz(self, group='default', offset=(0, 0)):
        self.e['Renderer'].renderf(pygame.draw.circle, *self.args(offset=offset), z=self.z, group=group)
        